"""
Workout Template routes — Save, list, load, rename, delete templates.
"""

from datetime import datetime, timezone
from typing import Optional, List

from bson import ObjectId
from fastapi import APIRouter, HTTPException, status, Depends, Query
from pydantic import BaseModel, Field

from app.database import get_db
from app.utils.security import get_current_user


router = APIRouter(prefix="/api/templates", tags=["Templates"])


# ── Schemas ────────────────────────────────────────────────────────

class TemplateExerciseSet(BaseModel):
    reps: int = Field(0, ge=0)
    weight: float = Field(0, ge=0)
    side: Optional[str] = None
    notes: Optional[str] = None


class TemplateExercise(BaseModel):
    exercise_name: str
    category: Optional[str] = None
    is_unilateral: Optional[bool] = False
    superset_group: Optional[int] = None
    sets: List[TemplateExerciseSet]


class TemplateCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    exercises: List[TemplateExercise] = Field(..., min_length=1)


class TemplateRename(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)


class TemplateResponse(BaseModel):
    id: str
    name: str
    exercises: List[TemplateExercise]
    exercise_count: int
    total_sets: int
    created_at: datetime
    last_used: Optional[datetime] = None
    use_count: int = 0


# ── Routes ─────────────────────────────────────────────────────────

@router.post("", response_model=TemplateResponse, status_code=status.HTTP_201_CREATED)
async def create_template(
    payload: TemplateCreate,
    current_user: dict = Depends(get_current_user),
):
    """Save the current workout as a reusable template."""
    db = get_db()

    # Check for duplicate name
    existing = await db.workout_templates.find_one({
        "user_id": current_user["id"],
        "name": {"$regex": f"^{payload.name}$", "$options": "i"},
    })
    if existing:
        raise HTTPException(status_code=400, detail="Template with this name already exists")

    exercises_data = [ex.model_dump() for ex in payload.exercises]
    total_sets = sum(len(ex.sets) for ex in payload.exercises)

    doc = {
        "user_id": current_user["id"],
        "name": payload.name,
        "exercises": exercises_data,
        "exercise_count": len(payload.exercises),
        "total_sets": total_sets,
        "use_count": 0,
        "last_used": None,
        "created_at": datetime.now(timezone.utc),
    }
    result = await db.workout_templates.insert_one(doc)

    return TemplateResponse(
        id=str(result.inserted_id),
        name=doc["name"],
        exercises=payload.exercises,
        exercise_count=doc["exercise_count"],
        total_sets=doc["total_sets"],
        created_at=doc["created_at"],
        last_used=None,
        use_count=0,
    )


@router.get("", response_model=List[TemplateResponse])
async def list_templates(
    current_user: dict = Depends(get_current_user),
):
    """List all saved workout templates for the user, most recently used first."""
    db = get_db()
    templates = []
    cursor = db.workout_templates.find(
        {"user_id": current_user["id"]}
    ).sort("created_at", -1)

    async for t in cursor:
        templates.append(TemplateResponse(
            id=str(t["_id"]),
            name=t["name"],
            exercises=t["exercises"],
            exercise_count=t.get("exercise_count", len(t["exercises"])),
            total_sets=t.get("total_sets", sum(len(e.get("sets", [])) for e in t["exercises"])),
            created_at=t["created_at"],
            last_used=t.get("last_used"),
            use_count=t.get("use_count", 0),
        ))
    return templates


@router.post("/{template_id}/use", response_model=TemplateResponse)
async def use_template(
    template_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Mark a template as 'used' (increments use_count, updates last_used).
    Returns the full template data so the frontend can load it into the workout modal."""
    db = get_db()

    t = await db.workout_templates.find_one({
        "_id": ObjectId(template_id),
        "user_id": current_user["id"],
    })
    if not t:
        raise HTTPException(status_code=404, detail="Template not found")

    now = datetime.now(timezone.utc)
    await db.workout_templates.update_one(
        {"_id": ObjectId(template_id)},
        {"$set": {"last_used": now}, "$inc": {"use_count": 1}},
    )

    return TemplateResponse(
        id=str(t["_id"]),
        name=t["name"],
        exercises=t["exercises"],
        exercise_count=t.get("exercise_count", len(t["exercises"])),
        total_sets=t.get("total_sets", sum(len(e.get("sets", [])) for e in t["exercises"])),
        created_at=t["created_at"],
        last_used=now,
        use_count=t.get("use_count", 0) + 1,
    )


@router.put("/{template_id}", response_model=TemplateResponse)
async def rename_template(
    template_id: str,
    payload: TemplateRename,
    current_user: dict = Depends(get_current_user),
):
    """Rename a workout template."""
    db = get_db()

    t = await db.workout_templates.find_one({
        "_id": ObjectId(template_id),
        "user_id": current_user["id"],
    })
    if not t:
        raise HTTPException(status_code=404, detail="Template not found")

    # Check for duplicate name (excluding self)
    existing = await db.workout_templates.find_one({
        "user_id": current_user["id"],
        "name": {"$regex": f"^{payload.name}$", "$options": "i"},
        "_id": {"$ne": ObjectId(template_id)},
    })
    if existing:
        raise HTTPException(status_code=400, detail="Template with this name already exists")

    await db.workout_templates.update_one(
        {"_id": ObjectId(template_id)},
        {"$set": {"name": payload.name}},
    )

    return TemplateResponse(
        id=str(t["_id"]),
        name=payload.name,
        exercises=t["exercises"],
        exercise_count=t.get("exercise_count", len(t["exercises"])),
        total_sets=t.get("total_sets", sum(len(e.get("sets", [])) for e in t["exercises"])),
        created_at=t["created_at"],
        last_used=t.get("last_used"),
        use_count=t.get("use_count", 0),
    )


@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_template(
    template_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Delete a workout template."""
    db = get_db()
    result = await db.workout_templates.delete_one({
        "_id": ObjectId(template_id),
        "user_id": current_user["id"],
    })
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Template not found")

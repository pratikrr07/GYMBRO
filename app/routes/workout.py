"""Workout & Exercise routes — CRUD, history, stats, calendar."""

from datetime import datetime, timezone, timedelta
from typing import Optional
from collections import Counter

from bson import ObjectId
from fastapi import APIRouter, HTTPException, status, Depends, Query

from app.database import get_db
from app.utils.security import get_current_user
from app.schemas.workout import (
    ExerciseCreate, ExerciseResponse,
    WorkoutCreate, WorkoutUpdate, WorkoutResponse,
    WorkoutStats, CalendarDay,
)

router = APIRouter(prefix="/api/workouts", tags=["Workouts"])
exercise_router = APIRouter(prefix="/api/exercises", tags=["Exercises"])


# ═══════════════════════════════════════════════════════════════════
#  EXERCISES
# ═══════════════════════════════════════════════════════════════════

@exercise_router.get("/", response_model=list[ExerciseResponse])
async def list_exercises(
    category: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
):
    """List all default exercises + user's custom exercises."""
    db = get_db()
    query = {
        "$or": [
            {"is_default": True},
            {"created_by": current_user["id"]},
        ]
    }
    if category:
        query["category"] = category

    exercises = []
    async for ex in db.exercises.find(query).sort("name", 1):
        exercises.append(ExerciseResponse(
            id=str(ex["_id"]),
            name=ex["name"],
            category=ex["category"],
            is_default=ex["is_default"],
            created_by=ex.get("created_by"),
        ))
    return exercises


@exercise_router.post("/", response_model=ExerciseResponse, status_code=status.HTTP_201_CREATED)
async def create_exercise(
    payload: ExerciseCreate,
    current_user: dict = Depends(get_current_user),
):
    """Create a custom exercise."""
    db = get_db()

    # Check if name already exists (case-insensitive) for this user or defaults
    existing = await db.exercises.find_one({
        "name": {"$regex": f"^{payload.name}$", "$options": "i"},
        "$or": [{"is_default": True}, {"created_by": current_user["id"]}],
    })
    if existing:
        raise HTTPException(status_code=400, detail="Exercise with this name already exists")

    doc = {
        "name": payload.name,
        "category": payload.category.value,
        "is_default": False,
        "created_by": current_user["id"],
        "created_at": datetime.now(timezone.utc),
    }
    result = await db.exercises.insert_one(doc)

    return ExerciseResponse(
        id=str(result.inserted_id),
        name=doc["name"],
        category=doc["category"],
        is_default=False,
        created_by=current_user["id"],
    )


# ═══════════════════════════════════════════════════════════════════
#  WORKOUTS
# ═══════════════════════════════════════════════════════════════════

@router.post("/", response_model=WorkoutResponse, status_code=status.HTTP_201_CREATED)
async def log_workout(
    payload: WorkoutCreate,
    current_user: dict = Depends(get_current_user),
):
    """Log a new workout session. Auto-detects personal records."""
    db = get_db()
    now = datetime.now(timezone.utc)
    workout_date = payload.date or now

    # Auto-assign set_numbers if missing
    exercises_data = []
    for ex in payload.exercises:
        ex_dict = ex.model_dump()
        for i, s in enumerate(ex_dict["sets"]):
            if s.get("set_number") is None:
                s["set_number"] = i + 1
        exercises_data.append(ex_dict)

    doc = {
        "user_id": current_user["id"],
        "name": payload.name or "Workout",
        "date": workout_date,
        "exercises": exercises_data,
        "notes": payload.notes,
        "duration_minutes": payload.duration_minutes,
        "created_at": now,
        "updated_at": now,
    }
    result = await db.workouts.insert_one(doc)
    workout_id = str(result.inserted_id)

    # ── PR Detection ──────────────────────────────────────────────
    new_prs = []
    for ex in exercises_data:
        ex_name = ex.get("exercise_name", "Unknown")
        for s in ex.get("sets", []):
            weight = s.get("weight", s.get("weight_kg", 0))
            reps = s.get("reps", 0)
            if weight <= 0:
                continue

            # Check max weight PR
            prev_max_weight = await db.personal_records.find_one(
                {"user_id": current_user["id"], "exercise_name": ex_name, "record_type": "max_weight"},
                sort=[("value", -1)],
            )
            prev_weight_val = prev_max_weight["value"] if prev_max_weight else 0

            if weight > prev_weight_val:
                # Upsert the PR
                await db.personal_records.update_one(
                    {"user_id": current_user["id"], "exercise_name": ex_name, "record_type": "max_weight"},
                    {"$set": {
                        "user_id": current_user["id"],
                        "exercise_name": ex_name,
                        "record_type": "max_weight",
                        "value": weight,
                        "unit": "kg",
                        "previous_value": prev_weight_val if prev_weight_val > 0 else None,
                        "date": workout_date.strftime("%Y-%m-%d"),
                        "workout_id": workout_id,
                    }},
                    upsert=True,
                )
                if prev_weight_val > 0:  # Only celebrate if beating a previous record
                    new_prs.append({"exercise": ex_name, "type": "Weight", "value": weight, "unit": "kg", "previous": prev_weight_val})

            # Check estimated 1RM PR (Epley: w × (1 + r/30))
            if reps > 0:
                e1rm = round(weight * (1 + reps / 30), 1)
                prev_1rm = await db.personal_records.find_one(
                    {"user_id": current_user["id"], "exercise_name": ex_name, "record_type": "estimated_1rm"},
                    sort=[("value", -1)],
                )
                prev_1rm_val = prev_1rm["value"] if prev_1rm else 0

                if e1rm > prev_1rm_val:
                    await db.personal_records.update_one(
                        {"user_id": current_user["id"], "exercise_name": ex_name, "record_type": "estimated_1rm"},
                        {"$set": {
                            "user_id": current_user["id"],
                            "exercise_name": ex_name,
                            "record_type": "estimated_1rm",
                            "value": e1rm,
                            "unit": "kg",
                            "previous_value": prev_1rm_val if prev_1rm_val > 0 else None,
                            "date": workout_date.strftime("%Y-%m-%d"),
                            "workout_id": workout_id,
                        }},
                        upsert=True,
                    )

    # Tag the workout document with PRs found
    if new_prs:
        await db.workouts.update_one({"_id": result.inserted_id}, {"$set": {"new_prs": new_prs}})

    response = WorkoutResponse(
        id=workout_id,
        user_id=current_user["id"],
        name=doc["name"],
        date=workout_date,
        exercises=payload.exercises,
        notes=payload.notes,
        duration_minutes=payload.duration_minutes,
        created_at=now,
    )
    # Attach PRs to response as extra field
    response_dict = response.model_dump()
    response_dict["new_prs"] = new_prs
    return response_dict


@router.get("/", response_model=list[WorkoutResponse])
async def list_workouts(
    current_user: dict = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
):
    """Get workout history (paginated, newest first)."""
    db = get_db()
    workouts = []
    cursor = db.workouts.find({"user_id": current_user["id"]}).sort("date", -1).skip(skip).limit(limit)
    async for w in cursor:
        workouts.append(WorkoutResponse(
            id=str(w["_id"]),
            user_id=w["user_id"],
            name=w.get("name"),
            date=w["date"],
            exercises=w["exercises"],
            notes=w.get("notes"),
            duration_minutes=w.get("duration_minutes"),
            created_at=w["created_at"],
        ))
    return workouts


@router.get("/calendar", response_model=list[CalendarDay])
async def workout_calendar(
    year: int = Query(...),
    month: int = Query(..., ge=1, le=12),
    current_user: dict = Depends(get_current_user),
):
    """Get calendar view of workouts for a given month."""
    db = get_db()

    start = datetime(year, month, 1, tzinfo=timezone.utc)
    if month == 12:
        end = datetime(year + 1, 1, 1, tzinfo=timezone.utc)
    else:
        end = datetime(year, month + 1, 1, tzinfo=timezone.utc)

    days_map: dict[str, CalendarDay] = {}
    cursor = db.workouts.find({
        "user_id": current_user["id"],
        "date": {"$gte": start, "$lt": end},
    })

    async for w in cursor:
        day_key = w["date"].strftime("%Y-%m-%d")
        if day_key not in days_map:
            days_map[day_key] = CalendarDay(date=day_key, workout_count=0, exercises=[])
        days_map[day_key].workout_count += 1
        for ex in w.get("exercises", []):
            name = ex.get("exercise_name", "Unknown")
            if name not in days_map[day_key].exercises:
                days_map[day_key].exercises.append(name)

    return sorted(days_map.values(), key=lambda d: d.date)


@router.get("/stats", response_model=WorkoutStats)
async def workout_stats(current_user: dict = Depends(get_current_user)):
    """Get overall workout statistics."""
    db = get_db()
    now = datetime.now(timezone.utc)

    # Total workouts
    total = await db.workouts.count_documents({"user_id": current_user["id"]})

    # This month
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    total_month = await db.workouts.count_documents({
        "user_id": current_user["id"],
        "date": {"$gte": month_start},
    })

    # This week (Monday start)
    week_start = now - timedelta(days=now.weekday())
    week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
    total_week = await db.workouts.count_documents({
        "user_id": current_user["id"],
        "date": {"$gte": week_start},
    })

    # Streak & favorites & volume
    exercise_counter = Counter()
    total_volume = 0.0
    workout_dates = set()

    cursor = db.workouts.find({"user_id": current_user["id"]}).sort("date", -1)
    async for w in cursor:
        workout_dates.add(w["date"].strftime("%Y-%m-%d"))
        for ex in w.get("exercises", []):
            exercise_counter[ex.get("exercise_name", "Unknown")] += 1
            for s in ex.get("sets", []):
                total_volume += s.get("weight", s.get("weight_kg", 0)) * s.get("reps", 0)

    # Calculate streak
    streak = 0
    check_date = now.date()
    while True:
        if check_date.strftime("%Y-%m-%d") in workout_dates:
            streak += 1
            check_date -= timedelta(days=1)
        elif check_date == now.date():
            # Today might not have a workout yet — check yesterday
            check_date -= timedelta(days=1)
        else:
            break

    favorite = exercise_counter.most_common(1)[0][0] if exercise_counter else None

    # Last workout info
    last_workout = await db.workouts.find_one(
        {"user_id": current_user["id"]},
        sort=[("date", -1)],
    )
    lw_name = None
    lw_date = None
    lw_exercises = 0
    lw_sets = 0
    lw_volume = 0.0
    lw_duration = 0
    if last_workout:
        lw_name = last_workout.get("name", "Workout")
        lw_date = last_workout["date"].strftime("%Y-%m-%d")
        exs = last_workout.get("exercises", [])
        lw_exercises = len(exs)
        for ex in exs:
            sets = ex.get("sets", [])
            lw_sets += len(sets)
            for s in sets:
                lw_volume += s.get("weight", s.get("weight_kg", 0)) * s.get("reps", 0)
        lw_duration = last_workout.get("duration_minutes") or 0

    return WorkoutStats(
        total_workouts=total,
        total_this_month=total_month,
        total_this_week=total_week,
        current_streak=streak,
        favorite_exercise=favorite,
        total_volume_kg=round(total_volume, 1),
        last_workout_name=lw_name,
        last_workout_date=lw_date,
        last_workout_exercises=lw_exercises,
        last_workout_sets=lw_sets,
        last_workout_volume_kg=round(lw_volume, 1),
        last_workout_duration_min=lw_duration,
    )


@router.get("/{workout_id}", response_model=WorkoutResponse)
async def get_workout(
    workout_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Get a single workout by ID."""
    db = get_db()
    w = await db.workouts.find_one({
        "_id": ObjectId(workout_id),
        "user_id": current_user["id"],
    })
    if not w:
        raise HTTPException(status_code=404, detail="Workout not found")

    return WorkoutResponse(
        id=str(w["_id"]),
        user_id=w["user_id"],
        date=w["date"],
        exercises=w["exercises"],
        notes=w.get("notes"),
        duration_minutes=w.get("duration_minutes"),
        created_at=w["created_at"],
    )


@router.put("/{workout_id}", response_model=WorkoutResponse)
async def update_workout(
    workout_id: str,
    payload: WorkoutUpdate,
    current_user: dict = Depends(get_current_user),
):
    """Update an existing workout."""
    db = get_db()

    existing = await db.workouts.find_one({
        "_id": ObjectId(workout_id),
        "user_id": current_user["id"],
    })
    if not existing:
        raise HTTPException(status_code=404, detail="Workout not found")

    update_data = {}
    if payload.exercises is not None:
        update_data["exercises"] = [ex.model_dump() for ex in payload.exercises]
    if payload.notes is not None:
        update_data["notes"] = payload.notes
    if payload.duration_minutes is not None:
        update_data["duration_minutes"] = payload.duration_minutes

    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")

    update_data["updated_at"] = datetime.now(timezone.utc)
    await db.workouts.update_one({"_id": ObjectId(workout_id)}, {"$set": update_data})

    updated = await db.workouts.find_one({"_id": ObjectId(workout_id)})
    return WorkoutResponse(
        id=str(updated["_id"]),
        user_id=updated["user_id"],
        date=updated["date"],
        exercises=updated["exercises"],
        notes=updated.get("notes"),
        duration_minutes=updated.get("duration_minutes"),
        created_at=updated["created_at"],
    )


@router.delete("/{workout_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_workout(
    workout_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Delete a workout."""
    db = get_db()
    result = await db.workouts.delete_one({
        "_id": ObjectId(workout_id),
        "user_id": current_user["id"],
    })
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Workout not found")

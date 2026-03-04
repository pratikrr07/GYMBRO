"""Meal tracking routes — log meals, manual entry, daily summary, history, calendar."""

from datetime import datetime, timezone, timedelta
from typing import Optional
from calendar import monthrange

from bson import ObjectId
from fastapi import APIRouter, HTTPException, status, Depends, Query

from app.database import get_db
from app.utils.security import get_current_user
from app.schemas.meal import (
    MealLogRequest, ManualMealRequest, MealResponse,
    DailyNutritionSummary, MealCalendarDay,
)
from app.services.ai_service import estimate_nutrition
from app.services.calorie_calculator import calculate_target_calories

router = APIRouter(prefix="/api/meals", tags=["Meals & Nutrition"])


@router.post("/", response_model=MealResponse, status_code=status.HTTP_201_CREATED)
async def log_meal(
    payload: MealLogRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Log a meal using natural language.
    AI estimates calories & macros automatically.
    
    Example: "I ate chicken, rice, and yogurt"
    """
    db = get_db()
    now = datetime.now(timezone.utc)

    # AI estimation
    nutrition = await estimate_nutrition(payload.description)

    doc = {
        "user_id": current_user["id"],
        "date": payload.date or now,
        "meal_type": payload.meal_type.value,
        "description": payload.description,
        "items": nutrition["items"],
        "total_calories": nutrition["total_calories"],
        "total_protein_g": nutrition["total_protein_g"],
        "total_carbs_g": nutrition["total_carbs_g"],
        "total_fat_g": nutrition["total_fat_g"],
        "source": nutrition.get("source", "unknown"),
        "created_at": now,
    }

    result = await db.meals.insert_one(doc)

    return MealResponse(
        id=str(result.inserted_id),
        user_id=current_user["id"],
        date=doc["date"],
        meal_type=doc["meal_type"],
        description=doc["description"],
        items=doc["items"],
        total_calories=doc["total_calories"],
        total_protein_g=doc["total_protein_g"],
        total_carbs_g=doc["total_carbs_g"],
        total_fat_g=doc["total_fat_g"],
        source=doc["source"],
        created_at=now,
    )


@router.get("/daily", response_model=DailyNutritionSummary)
async def daily_summary(
    date: Optional[str] = Query(None, description="Date in YYYY-MM-DD format, defaults to today"),
    current_user: dict = Depends(get_current_user),
):
    """Get daily nutrition summary with target comparison."""
    db = get_db()

    if date:
        try:
            target_date = datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    else:
        target_date = datetime.now(timezone.utc)

    day_start = target_date.replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=timezone.utc)
    day_end = day_start + timedelta(days=1)

    meals = []
    cursor = db.meals.find({
        "user_id": current_user["id"],
        "date": {"$gte": day_start, "$lt": day_end},
    }).sort("date", 1)

    async for m in cursor:
        meals.append(MealResponse(
            id=str(m["_id"]),
            user_id=m["user_id"],
            date=m["date"],
            meal_type=m["meal_type"],
            description=m["description"],
            items=m["items"],
            total_calories=m["total_calories"],
            total_protein_g=m["total_protein_g"],
            total_carbs_g=m["total_carbs_g"],
            total_fat_g=m["total_fat_g"],
            source=m.get("source", "unknown"),
            created_at=m["created_at"],
        ))

    total_cal = sum(m.total_calories for m in meals)
    total_pro = round(sum(m.total_protein_g for m in meals), 1)
    total_carb = round(sum(m.total_carbs_g for m in meals), 1)
    total_fat = round(sum(m.total_fat_g for m in meals), 1)

    # Calculate target calories for comparison
    target_cals = calculate_target_calories(current_user)

    return DailyNutritionSummary(
        date=day_start.strftime("%Y-%m-%d"),
        meals=meals,
        total_calories=total_cal,
        total_protein_g=total_pro,
        total_carbs_g=total_carb,
        total_fat_g=total_fat,
        target_calories=target_cals,
        calorie_diff=total_cal - target_cals if target_cals else None,
    )


@router.get("/history", response_model=list[MealResponse])
async def meal_history(
    current_user: dict = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
):
    """Get meal history (paginated, newest first)."""
    db = get_db()
    meals = []
    cursor = db.meals.find({"user_id": current_user["id"]}).sort("date", -1).skip(skip).limit(limit)
    async for m in cursor:
        meals.append(MealResponse(
            id=str(m["_id"]),
            user_id=m["user_id"],
            date=m["date"],
            meal_type=m["meal_type"],
            description=m["description"],
            items=m["items"],
            total_calories=m["total_calories"],
            total_protein_g=m["total_protein_g"],
            total_carbs_g=m["total_carbs_g"],
            total_fat_g=m["total_fat_g"],
            source=m.get("source", "unknown"),
            created_at=m["created_at"],
        ))
    return meals


@router.post("/manual", response_model=MealResponse, status_code=status.HTTP_201_CREATED)
async def log_manual_meal(
    payload: ManualMealRequest,
    current_user: dict = Depends(get_current_user),
):
    """Log a meal with manually entered nutrition data."""
    db = get_db()
    now = datetime.now(timezone.utc)

    items = []
    for item in payload.items:
        items.append({
            "name": item.name,
            "portion": item.quantity or "1 serving",
            "calories": item.calories,
            "protein_g": item.protein_g,
            "carbs_g": item.carbs_g,
            "fat_g": item.fat_g,
        })

    total_cal = sum(i["calories"] for i in items)
    total_pro = round(sum(i["protein_g"] for i in items), 1)
    total_carb = round(sum(i["carbs_g"] for i in items), 1)
    total_fat = round(sum(i["fat_g"] for i in items), 1)

    description = ", ".join(f"{i['name']} ({i['portion']})" for i in items)

    doc = {
        "user_id": current_user["id"],
        "date": payload.date or now,
        "meal_type": payload.meal_type.value,
        "description": description,
        "items": items,
        "total_calories": total_cal,
        "total_protein_g": total_pro,
        "total_carbs_g": total_carb,
        "total_fat_g": total_fat,
        "source": "manual",
        "created_at": now,
    }

    result = await db.meals.insert_one(doc)

    return MealResponse(
        id=str(result.inserted_id),
        user_id=current_user["id"],
        date=doc["date"],
        meal_type=doc["meal_type"],
        description=description,
        items=doc["items"],
        total_calories=total_cal,
        total_protein_g=total_pro,
        total_carbs_g=total_carb,
        total_fat_g=total_fat,
        source="manual",
        created_at=now,
    )


@router.get("/calendar", response_model=list[MealCalendarDay])
async def meal_calendar(
    year: int = Query(...),
    month: int = Query(..., ge=1, le=12),
    current_user: dict = Depends(get_current_user),
):
    """Get calendar view of daily meal intake for a given month."""
    db = get_db()

    start = datetime(year, month, 1, tzinfo=timezone.utc)
    if month == 12:
        end = datetime(year + 1, 1, 1, tzinfo=timezone.utc)
    else:
        end = datetime(year, month + 1, 1, tzinfo=timezone.utc)

    # Aggregate meals by day
    days_map = {}
    cursor = db.meals.find({
        "user_id": current_user["id"],
        "date": {"$gte": start, "$lt": end},
    })

    async for m in cursor:
        day_key = m["date"].strftime("%Y-%m-%d")
        day_num = m["date"].day
        if day_key not in days_map:
            days_map[day_key] = {
                "date": day_key,
                "day": day_num,
                "has_meals": True,
                "meal_count": 0,
                "total_calories": 0,
                "total_protein_g": 0,
                "total_carbs_g": 0,
                "total_fat_g": 0,
            }
        days_map[day_key]["meal_count"] += 1
        days_map[day_key]["total_calories"] += m.get("total_calories", 0)
        days_map[day_key]["total_protein_g"] += m.get("total_protein_g", 0)
        days_map[day_key]["total_carbs_g"] += m.get("total_carbs_g", 0)
        days_map[day_key]["total_fat_g"] += m.get("total_fat_g", 0)

    # Round values
    for d in days_map.values():
        d["total_calories"] = round(d["total_calories"])
        d["total_protein_g"] = round(d["total_protein_g"], 1)
        d["total_carbs_g"] = round(d["total_carbs_g"], 1)
        d["total_fat_g"] = round(d["total_fat_g"], 1)

    return sorted(days_map.values(), key=lambda d: d["date"])


@router.delete("/{meal_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_meal(
    meal_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Delete a meal log."""
    db = get_db()
    result = await db.meals.delete_one({
        "_id": ObjectId(meal_id),
        "user_id": current_user["id"],
    })
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Meal not found")

"""Goal & nutrition plan routes."""

from datetime import datetime, timezone

from bson import ObjectId
from fastapi import APIRouter, Depends

from app.database import get_db
from app.utils.security import get_current_user
from app.schemas.goal import (
    NutritionPlanResponse, GoalResponse,
    CoachingTipsResponse, TimelineEstimate, MacroTargets,
)
from app.services.calorie_calculator import get_full_nutrition_plan
from app.services.coaching import generate_coaching_tips

router = APIRouter(prefix="/api/goals", tags=["Goals & Nutrition"])


@router.get("/nutrition-plan", response_model=NutritionPlanResponse)
async def get_nutrition_plan(current_user: dict = Depends(get_current_user)):
    """
    Calculate personalized nutrition plan based on user profile.
    Uses Mifflin-St Jeor equation + goal adjustments.
    """
    plan = get_full_nutrition_plan(current_user)

    timeline = None
    if plan.get("timeline"):
        timeline = TimelineEstimate(**plan["timeline"])

    return NutritionPlanResponse(
        bmr=plan["bmr"],
        tdee=plan["tdee"],
        target_calories=plan["target_calories"],
        goal=plan["goal"],
        macros=MacroTargets(**plan["macros"]),
        protein_g=plan.get("protein_g", 0),
        carbs_g=plan.get("carbs_g", 0),
        fat_g=plan.get("fat_g", 0),
        protein_pct=plan.get("protein_pct", 0),
        carbs_pct=plan.get("carbs_pct", 0),
        fat_pct=plan.get("fat_pct", 0),
        deficit_pct=plan.get("deficit_pct", 0),
        daily_deficit=plan.get("daily_deficit", 0),
        weekly_calorie_deficit=plan.get("weekly_calorie_deficit", 0),
        weekly_weight_change_kg=plan.get("weekly_weight_change_kg", 0),
        monthly_weight_change_kg=plan.get("monthly_weight_change_kg", 0),
        direction=plan.get("direction", "none"),
        timeline=timeline,
    )


@router.post("/generate", response_model=GoalResponse)
async def generate_goal(current_user: dict = Depends(get_current_user)):
    """
    Generate (or regenerate) the user's active goal with:
    - Calorie targets
    - Macro targets
    - Timeline estimate
    - AI coaching tips
    """
    db = get_db()
    now = datetime.now(timezone.utc)

    # Calculate plan
    plan = get_full_nutrition_plan(current_user)

    # Get coaching tips
    tips_result = await generate_coaching_tips(current_user)

    # Deactivate old goals
    await db.goals.update_many(
        {"user_id": current_user["id"], "is_active": True},
        {"$set": {"is_active": False, "updated_at": now}},
    )

    # Create new goal
    doc = {
        "user_id": current_user["id"],
        "goal_type": current_user["goal"],
        "target_weight_kg": current_user.get("target_weight_kg"),
        "target_calories": plan["target_calories"],
        "target_protein_g": plan["macros"]["protein_g"],
        "target_carbs_g": plan["macros"]["carbs_g"],
        "target_fat_g": plan["macros"]["fat_g"],
        "coaching_tips": tips_result.get("tips", []),
        "timeline": plan.get("timeline"),
        "is_active": True,
        "created_at": now,
        "updated_at": now,
    }

    result = await db.goals.insert_one(doc)

    timeline = None
    if doc.get("timeline"):
        timeline = TimelineEstimate(**doc["timeline"])

    return GoalResponse(
        id=str(result.inserted_id),
        user_id=current_user["id"],
        goal_type=doc["goal_type"],
        target_weight_kg=doc["target_weight_kg"],
        target_calories=doc["target_calories"],
        target_protein_g=doc["target_protein_g"],
        target_carbs_g=doc["target_carbs_g"],
        target_fat_g=doc["target_fat_g"],
        coaching_tips=doc["coaching_tips"],
        timeline=timeline,
        is_active=True,
        created_at=now,
    )


@router.get("/active", response_model=GoalResponse)
async def get_active_goal(current_user: dict = Depends(get_current_user)):
    """Get the user's currently active goal."""
    db = get_db()
    goal = await db.goals.find_one({
        "user_id": current_user["id"],
        "is_active": True,
    })

    if not goal:
        # Auto-generate if none exists
        from fastapi import Request
        return await generate_goal(current_user)

    timeline = None
    if goal.get("timeline"):
        timeline = TimelineEstimate(**goal["timeline"])

    return GoalResponse(
        id=str(goal["_id"]),
        user_id=goal["user_id"],
        goal_type=goal["goal_type"],
        target_weight_kg=goal.get("target_weight_kg"),
        target_calories=goal["target_calories"],
        target_protein_g=goal["target_protein_g"],
        target_carbs_g=goal["target_carbs_g"],
        target_fat_g=goal["target_fat_g"],
        coaching_tips=goal.get("coaching_tips", []),
        timeline=timeline,
        is_active=goal["is_active"],
        created_at=goal["created_at"],
    )


@router.get("/coaching-tips", response_model=CoachingTipsResponse)
async def get_coaching_tips(current_user: dict = Depends(get_current_user)):
    """Get personalized AI coaching tips."""
    result = await generate_coaching_tips(current_user)
    return CoachingTipsResponse(
        tips=result.get("tips", []),
        source=result.get("source", "default"),
    )

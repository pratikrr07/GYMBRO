"""
🧠 Smart Coach routes — AI-powered fitness analysis & workout generation.

POST /api/coaching/smart-analysis  → Comprehensive performance report
GET  /api/coaching/generate-workout → Personalized workout plan
GET  /api/coaching/tips             → Coaching tips (existing)
"""

from fastapi import APIRouter, Depends, Query

from app.utils.security import get_current_user
from app.services.smart_coach import get_smart_analysis, get_generated_workout
from app.services.coaching import generate_coaching_tips

router = APIRouter(prefix="/api/coaching", tags=["AI Smart Coach"])


@router.post("/smart-analysis")
async def smart_analysis(
    days: int = Query(30, ge=7, le=90, description="Analysis period in days"),
    current_user: dict = Depends(get_current_user),
):
    """
    🧠 AI Smart Coach — Comprehensive Fitness Analysis

    Pulls all user data (workouts, meals, weight, PRs, water, streaks) from
    the last N days and returns a structured coaching report with:
    - Performance score (0-100) with grade
    - Score breakdown by category
    - Data-driven wins, insights, and warnings
    - Muscle group distribution analysis
    - Top exercises
    - AI-generated summary (when Gemini key is set)
    """
    return await get_smart_analysis(current_user, days)


@router.get("/generate-workout")
async def generate_workout(
    current_user: dict = Depends(get_current_user),
):
    """
    🏋️ AI Workout Generator — Personalized Training Plan

    Analyzes training history, identifies weak/neglected muscle groups,
    and generates a full weekly workout plan with:
    - Split recommendation (Full Body / Upper-Lower / PPL)
    - Exercise selection with sets, reps, rest times
    - Goal-specific adjustments
    - Coaching notes
    """
    return await get_generated_workout(current_user)


@router.get("/tips")
async def coaching_tips(
    current_user: dict = Depends(get_current_user),
):
    """Get personalized coaching tips (science-backed library or AI)."""
    return await generate_coaching_tips(current_user)

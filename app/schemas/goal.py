"""Pydantic schemas for goals & nutrition plans."""

from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel


class MacroTargets(BaseModel):
    protein_g: float
    carbs_g: float
    fat_g: float


class TimelineEstimate(BaseModel):
    weight_diff_kg: Optional[float] = None
    estimated_weeks: Optional[int] = None
    estimated_months: Optional[float] = None
    rate_per_week_kg: Optional[float] = None
    current_weight: Optional[float] = None
    target_weight: Optional[float] = None
    message: str


class NutritionPlanResponse(BaseModel):
    bmr: float
    tdee: int
    target_calories: int
    goal: str
    macros: MacroTargets
    # Flat macro fields for easy frontend access
    protein_g: float = 0
    carbs_g: float = 0
    fat_g: float = 0
    protein_pct: int = 0
    carbs_pct: int = 0
    fat_pct: int = 0
    # Deficit / surplus prediction
    deficit_pct: float = 0
    daily_deficit: int = 0
    weekly_calorie_deficit: int = 0
    weekly_weight_change_kg: float = 0
    monthly_weight_change_kg: float = 0
    direction: str = "none"   # "loss" | "gain" | "none"
    timeline: Optional[TimelineEstimate] = None


class GoalResponse(BaseModel):
    id: str
    user_id: str
    goal_type: str
    target_weight_kg: Optional[float] = None
    target_calories: int
    target_protein_g: float
    target_carbs_g: float
    target_fat_g: float
    coaching_tips: List[str]
    timeline: Optional[TimelineEstimate] = None
    is_active: bool
    created_at: datetime


class CoachingTipsResponse(BaseModel):
    tips: List[str]
    source: str  # "ai" or "default"

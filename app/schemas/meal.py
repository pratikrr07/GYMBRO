"""Pydantic schemas for meal tracking."""

from datetime import datetime
from typing import Optional, List
from enum import Enum

from pydantic import BaseModel, Field


class MealType(str, Enum):
    breakfast = "breakfast"
    lunch = "lunch"
    dinner = "dinner"
    snack = "snack"


# ── Request ────────────────────────────────────────────────────────
class MealLogRequest(BaseModel):
    description: str = Field(..., min_length=3, max_length=500,
                             examples=["I ate chicken, rice, and yogurt"])
    meal_type: MealType = MealType.lunch
    date: Optional[datetime] = None  # defaults to now


class ManualMealItem(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    quantity: Optional[str] = None       # e.g. "200g", "1 cup"
    calories: float = Field(..., ge=0)
    protein_g: float = Field(0, ge=0)
    carbs_g: float = Field(0, ge=0)
    fat_g: float = Field(0, ge=0)


class ManualMealRequest(BaseModel):
    meal_type: MealType = MealType.lunch
    items: List[ManualMealItem] = Field(..., min_length=1)
    date: Optional[datetime] = None


# ── Response items ─────────────────────────────────────────────────
class NutritionItem(BaseModel):
    name: str
    portion: Optional[str] = None
    calories: float
    protein_g: float
    carbs_g: float
    fat_g: float


class MealResponse(BaseModel):
    id: str
    user_id: str
    date: datetime
    meal_type: str
    description: str
    items: List[NutritionItem]
    total_calories: float
    total_protein_g: float
    total_carbs_g: float
    total_fat_g: float
    source: str
    created_at: datetime


class DailyNutritionSummary(BaseModel):
    date: str  # YYYY-MM-DD
    meals: List[MealResponse]
    total_calories: float
    total_protein_g: float
    total_carbs_g: float
    total_fat_g: float
    target_calories: Optional[int] = None
    calorie_diff: Optional[float] = None  # positive = over, negative = under


class MealCalendarDay(BaseModel):
    date: str  # YYYY-MM-DD
    day: int
    has_meals: bool
    meal_count: int
    total_calories: float
    total_protein_g: float
    total_carbs_g: float
    total_fat_g: float

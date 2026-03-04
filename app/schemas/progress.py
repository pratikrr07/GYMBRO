"""Schemas for progress tracking, achievements, and personal records."""

from pydantic import BaseModel
from typing import Optional
from datetime import datetime


# ── Calorie Trend ────────────────────────────────────────────────
class CalorieTrendDay(BaseModel):
    date: str
    calories: float
    protein_g: float = 0
    carbs_g: float = 0
    fat_g: float = 0
    target: float = 0


# ── Workout Frequency ───────────────────────────────────────────
class WorkoutFrequencyWeek(BaseModel):
    week_label: str          # e.g. "Dec 2", "Dec 9"
    week_start: str          # YYYY-MM-DD
    count: int


# ── Strength Trend ──────────────────────────────────────────────
class StrengthDataPoint(BaseModel):
    date: str
    max_weight: float
    max_reps: int
    estimated_1rm: float     # Epley formula: weight × (1 + reps/30)


class StrengthTrend(BaseModel):
    exercise_name: str
    data_points: list[StrengthDataPoint]


# ── Personal Records ────────────────────────────────────────────
class PersonalRecord(BaseModel):
    id: Optional[str] = None
    exercise_name: str
    record_type: str         # "max_weight" | "max_reps" | "max_volume" | "estimated_1rm"
    value: float
    unit: str                # "kg", "reps", "kg×reps"
    previous_value: Optional[float] = None
    date: str
    workout_id: Optional[str] = None


# ── Achievements ─────────────────────────────────────────────────
class Achievement(BaseModel):
    id: str
    name: str
    description: str
    icon: str
    category: str            # "workout", "nutrition", "consistency", "hydration"
    unlocked: bool = False
    unlocked_at: Optional[str] = None
    progress: Optional[float] = None     # 0.0 → 1.0
    progress_text: Optional[str] = None  # "3 / 7 days"


# ── Water Intake ─────────────────────────────────────────────────
class WaterLogResponse(BaseModel):
    glasses: int
    goal: int = 8
    percentage: float


class WaterEntry(BaseModel):
    id: str
    timestamp: str


# ── Weight Log ───────────────────────────────────────────────────
class WeightLogEntry(BaseModel):
    id: Optional[str] = None
    date: str
    weight_kg: float
    note: Optional[str] = None


class WeightLogResponse(BaseModel):
    entries: list[WeightLogEntry]
    current_weight: Optional[float] = None
    start_weight: Optional[float] = None
    target_weight: Optional[float] = None
    total_change: Optional[float] = None


# ── Progress Overview ────────────────────────────────────────────
class ProgressOverview(BaseModel):
    total_workouts: int = 0
    total_meals: int = 0
    active_days: int = 0
    current_streak: int = 0
    longest_streak: int = 0
    total_volume_kg: float = 0
    total_calories_burned: float = 0
    avg_workout_duration_min: float = 0
    total_prs: int = 0
    achievements_unlocked: int = 0
    member_since_days: int = 0

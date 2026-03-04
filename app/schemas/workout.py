"""Pydantic schemas for workouts and exercises."""

from datetime import datetime, date
from typing import Optional, List
from enum import Enum

from pydantic import BaseModel, Field


# ── Enums ──────────────────────────────────────────────────────────
class ExerciseCategory(str, Enum):
    chest = "chest"
    back = "back"
    shoulders = "shoulders"
    arms = "arms"
    legs = "legs"
    glutes = "glutes"
    forearms = "forearms"
    core = "core"
    cardio = "cardio"
    full_body = "full_body"
    stretching = "stretching"
    other = "other"


# ── Exercise schemas ───────────────────────────────────────────────
class ExerciseCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    category: ExerciseCategory


class ExerciseResponse(BaseModel):
    id: str
    name: str
    category: str
    is_default: bool
    created_by: Optional[str] = None


# ── Set schema ─────────────────────────────────────────────────────
class SetEntry(BaseModel):
    set_number: Optional[int] = Field(None, ge=1)
    reps: int = Field(..., ge=0)
    weight: float = Field(0, ge=0)
    side: Optional[str] = None      # "L" or "R" for unilateral exercises
    notes: Optional[str] = None


# ── Workout exercise entry ─────────────────────────────────────────
class WorkoutExerciseEntry(BaseModel):
    exercise_id: Optional[str] = None
    exercise_name: str
    category: Optional[str] = None
    is_unilateral: Optional[bool] = False
    superset_group: Optional[int] = None     # exercises with same group number are a superset
    sets: List[SetEntry]


# ── Workout schemas ────────────────────────────────────────────────
class WorkoutCreate(BaseModel):
    name: Optional[str] = None
    date: Optional[datetime] = None
    exercises: List[WorkoutExerciseEntry] = Field(..., min_length=1)
    notes: Optional[str] = None
    duration_minutes: Optional[int] = Field(None, ge=1, le=600)


class WorkoutUpdate(BaseModel):
    exercises: Optional[List[WorkoutExerciseEntry]] = None
    notes: Optional[str] = None
    duration_minutes: Optional[int] = Field(None, ge=1, le=600)


class WorkoutResponse(BaseModel):
    id: str
    user_id: str
    name: Optional[str] = None
    date: datetime
    exercises: List[WorkoutExerciseEntry]
    notes: Optional[str] = None
    duration_minutes: Optional[int] = None
    created_at: datetime


# ── Stats schemas ──────────────────────────────────────────────────
class WorkoutStats(BaseModel):
    total_workouts: int
    total_this_month: int
    total_this_week: int
    current_streak: int
    favorite_exercise: Optional[str] = None
    total_volume_kg: float  # total weight lifted all time
    last_workout_name: Optional[str] = None
    last_workout_date: Optional[str] = None
    last_workout_exercises: int = 0
    last_workout_sets: int = 0
    last_workout_volume_kg: float = 0.0
    last_workout_duration_min: int = 0


class CalendarDay(BaseModel):
    date: str  # YYYY-MM-DD
    workout_count: int
    exercises: List[str]

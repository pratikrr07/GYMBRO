"""Pydantic schemas for authentication & user profile."""

from datetime import datetime
from typing import Optional
from enum import Enum

from pydantic import BaseModel, EmailStr, Field


# ── Enums ──────────────────────────────────────────────────────────
class Gender(str, Enum):
    male = "male"
    female = "female"
    other = "other"


class ActivityLevel(str, Enum):
    sedentary = "sedentary"                  # Little or no exercise
    lightly_active = "lightly_active"          # 1-3 days/week
    moderately_active = "moderately_active"    # 3-5 days/week
    very_active = "very_active"                # 6-7 days/week
    extremely_active = "extremely_active"      # Athlete / physical job


class Goal(str, Enum):
    lose_weight = "lose_weight"
    gain_muscle = "gain_muscle"
    maintain = "maintain"


# ── Request schemas ────────────────────────────────────────────────
class UserSignup(BaseModel):
    username: str = Field(..., min_length=3, max_length=30)
    email: EmailStr
    password: str = Field(..., min_length=6)
    age: Optional[int] = Field(None, ge=13, le=120)
    height_cm: Optional[float] = Field(None, gt=50, lt=300)
    weight_kg: Optional[float] = Field(None, gt=20, lt=500)
    gender: Gender = Gender.male
    activity_level: ActivityLevel = ActivityLevel.moderately_active
    goal: Goal = Goal.maintain
    target_weight_kg: Optional[float] = Field(None, gt=20, lt=500)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserProfileUpdate(BaseModel):
    username: Optional[str] = Field(None, min_length=3, max_length=30)
    age: Optional[int] = Field(None, ge=13, le=120)
    height_cm: Optional[float] = Field(None, gt=50, lt=300)
    weight_kg: Optional[float] = Field(None, gt=20, lt=500)
    gender: Optional[Gender] = None
    activity_level: Optional[ActivityLevel] = None
    goal: Optional[Goal] = None
    target_weight_kg: Optional[float] = Field(None, gt=20, lt=500)
    weight_unit: Optional[str] = Field(None, pattern="^(kg|lbs)$")
    custom_calories: Optional[int] = Field(None, ge=0, le=10000)
    custom_protein_g: Optional[int] = Field(None, ge=0, le=1000)
    custom_carbs_g: Optional[int] = Field(None, ge=0, le=2000)
    custom_fat_g: Optional[int] = Field(None, ge=0, le=1000)


# ── Response schemas ───────────────────────────────────────────────
class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    age: Optional[int] = None
    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None
    gender: Optional[str] = None
    activity_level: Optional[str] = None
    goal: Optional[str] = None
    target_weight_kg: Optional[float] = None
    weight_unit: Optional[str] = "kg"
    custom_calories: Optional[int] = None
    custom_protein_g: Optional[int] = None
    custom_carbs_g: Optional[int] = None
    custom_fat_g: Optional[int] = None
    created_at: datetime


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

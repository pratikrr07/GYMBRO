"""Authentication routes — signup, login, profile."""

from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, status, Depends

from app.database import get_db
from app.schemas.user import (
    UserSignup, UserLogin, UserProfileUpdate,
    UserResponse, TokenResponse,
)
from app.utils.security import (
    hash_password, verify_password,
    create_access_token, get_current_user,
)

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


# ── SIGNUP ─────────────────────────────────────────────────────────
@router.post("/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def signup(payload: UserSignup):
    db = get_db()

    # Check duplicates
    if await db.users.find_one({"email": payload.email}):
        raise HTTPException(status_code=400, detail="Email already registered")
    if await db.users.find_one({"username": payload.username}):
        raise HTTPException(status_code=400, detail="Username already taken")

    now = datetime.now(timezone.utc)
    user_doc = {
        "username": payload.username,
        "email": payload.email,
        "hashed_password": hash_password(payload.password),
        "age": payload.age,
        "height_cm": payload.height_cm,
        "weight_kg": payload.weight_kg,
        "gender": payload.gender.value,
        "activity_level": payload.activity_level.value,
        "goal": payload.goal.value,
        "target_weight_kg": payload.target_weight_kg,
        "created_at": now,
        "updated_at": now,
    }

    result = await db.users.insert_one(user_doc)
    user_id = str(result.inserted_id)

    token = create_access_token(data={"sub": user_id})

    return TokenResponse(
        access_token=token,
        user=UserResponse(
            id=user_id,
            username=payload.username,
            email=payload.email,
            age=payload.age,
            height_cm=payload.height_cm,
            weight_kg=payload.weight_kg,
            gender=payload.gender.value,
            activity_level=payload.activity_level.value,
            goal=payload.goal.value,
            target_weight_kg=payload.target_weight_kg,
            weight_unit="kg",
            custom_calories=None,
            custom_protein_g=None,
            custom_carbs_g=None,
            custom_fat_g=None,
            created_at=now,
        ),
    )


# ── LOGIN ──────────────────────────────────────────────────────────
@router.post("/login", response_model=TokenResponse)
async def login(payload: UserLogin):
    db = get_db()
    user = await db.users.find_one({"email": payload.email})

    if not user or not verify_password(payload.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    user_id = str(user["_id"])
    token = create_access_token(data={"sub": user_id})

    return TokenResponse(
        access_token=token,
        user=UserResponse(
            id=user_id,
            username=user["username"],
            email=user["email"],
            age=user["age"],
            height_cm=user["height_cm"],
            weight_kg=user["weight_kg"],
            gender=user["gender"],
            activity_level=user["activity_level"],
            goal=user["goal"],
            target_weight_kg=user.get("target_weight_kg"),
            weight_unit=user.get("weight_unit", "kg"),
            custom_calories=user.get("custom_calories"),
            custom_protein_g=user.get("custom_protein_g"),
            custom_carbs_g=user.get("custom_carbs_g"),
            custom_fat_g=user.get("custom_fat_g"),
            created_at=user["created_at"],
        ),
    )


# ── GET PROFILE ────────────────────────────────────────────────────
@router.get("/me", response_model=UserResponse)
async def get_profile(current_user: dict = Depends(get_current_user)):
    return UserResponse(
        id=current_user["id"],
        username=current_user.get("username", ""),
        email=current_user["email"],
        age=current_user.get("age"),
        height_cm=current_user.get("height_cm"),
        weight_kg=current_user.get("weight_kg"),
        gender=current_user.get("gender"),
        activity_level=current_user.get("activity_level"),
        goal=current_user.get("goal"),
        target_weight_kg=current_user.get("target_weight_kg"),
        weight_unit=current_user.get("weight_unit", "kg"),
        custom_calories=current_user.get("custom_calories"),
        custom_protein_g=current_user.get("custom_protein_g"),
        custom_carbs_g=current_user.get("custom_carbs_g"),
        custom_fat_g=current_user.get("custom_fat_g"),
        created_at=current_user["created_at"],
    )


# ── UPDATE PROFILE ─────────────────────────────────────────────────
@router.put("/me", response_model=UserResponse)
async def update_profile(
    payload: UserProfileUpdate,
    current_user: dict = Depends(get_current_user),
):
    db = get_db()

    update_data = {k: v for k, v in payload.model_dump(exclude_unset=True).items()}
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")

    # Convert enums to strings
    for key in ("gender", "activity_level", "goal"):
        if key in update_data and hasattr(update_data[key], "value"):
            update_data[key] = update_data[key].value

    # Treat custom_* = 0 as "clear" (set to None in DB)
    custom_fields = ("custom_calories", "custom_protein_g", "custom_carbs_g", "custom_fat_g")
    for cf in custom_fields:
        if cf in update_data and update_data[cf] == 0:
            update_data[cf] = None

    update_data["updated_at"] = datetime.now(timezone.utc)

    from bson import ObjectId
    await db.users.update_one(
        {"_id": ObjectId(current_user["id"])},
        {"$set": update_data},
    )

    # Return updated user
    updated = await db.users.find_one({"_id": ObjectId(current_user["id"])})
    return UserResponse(
        id=str(updated["_id"]),
        username=updated.get("username", ""),
        email=updated["email"],
        age=updated.get("age"),
        height_cm=updated.get("height_cm"),
        weight_kg=updated.get("weight_kg"),
        gender=updated.get("gender"),
        activity_level=updated.get("activity_level"),
        goal=updated.get("goal"),
        target_weight_kg=updated.get("target_weight_kg"),
        weight_unit=updated.get("weight_unit", "kg"),
        custom_calories=updated.get("custom_calories"),
        custom_protein_g=updated.get("custom_protein_g"),
        custom_carbs_g=updated.get("custom_carbs_g"),
        custom_fat_g=updated.get("custom_fat_g"),
        created_at=updated["created_at"],
    )

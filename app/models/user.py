"""User MongoDB document shape (reference — not enforced ORM, just docs)."""

# MongoDB collection: users
#
# {
#   "_id": ObjectId,
#   "username": str,
#   "email": str,
#   "hashed_password": str,
#   "age": int,
#   "height_cm": float,
#   "weight_kg": float,
#   "gender": "male" | "female" | "other",
#   "activity_level": "sedentary" | "light" | "moderate" | "active" | "very_active",
#   "goal": "lose" | "gain" | "maintain",
#   "target_weight_kg": float | null,
#   "created_at": datetime,
#   "updated_at": datetime,
# }

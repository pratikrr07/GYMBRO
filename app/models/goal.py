"""Goal MongoDB document shape (reference)."""

# MongoDB collection: goals (one active goal per user)
#
# {
#   "_id": ObjectId,
#   "user_id": str,
#   "goal_type": "lose" | "gain" | "maintain",
#   "target_weight_kg": float | null,
#   "target_calories": int,
#   "target_protein_g": float,
#   "target_carbs_g": float,
#   "target_fat_g": float,
#   "coaching_tips": [str],
#   "timeline": {
#       "weight_diff_kg": float,
#       "estimated_weeks": int,
#       "estimated_months": float,
#       "rate_per_week_kg": float,
#       "message": str,
#   } | null,
#   "is_active": bool,
#   "created_at": datetime,
#   "updated_at": datetime,
# }

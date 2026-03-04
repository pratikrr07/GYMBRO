"""Meal MongoDB document shape (reference)."""

# MongoDB collection: meals
#
# {
#   "_id": ObjectId,
#   "user_id": str,
#   "date": datetime,                    # date of the meal
#   "meal_type": "breakfast" | "lunch" | "dinner" | "snack",
#   "description": str,                  # raw user input
#   "items": [
#       {
#           "name": str,
#           "portion": str,
#           "calories": int,
#           "protein_g": float,
#           "carbs_g": float,
#           "fat_g": float,
#       }
#   ],
#   "total_calories": int,
#   "total_protein_g": float,
#   "total_carbs_g": float,
#   "total_fat_g": float,
#   "source": "ai" | "fallback" | "cache",
#   "created_at": datetime,
# }

"""Workout & Exercise MongoDB document shapes (reference)."""

# MongoDB collection: exercises
#
# {
#   "_id": ObjectId,
#   "name": str,
#   "category": "chest" | "back" | "shoulders" | "arms" | "legs" | "core" | "cardio" | "other",
#   "is_default": bool,
#   "created_by": str | null,       # user_id for custom exercises
#   "created_at": datetime,
# }

# MongoDB collection: workouts
#
# {
#   "_id": ObjectId,
#   "user_id": str,
#   "date": datetime,
#   "exercises": [
#       {
#           "exercise_id": str,
#           "exercise_name": str,
#           "sets": [
#               {
#                   "set_number": int,
#                   "reps": int,
#                   "weight_kg": float,
#                   "notes": str | null,
#               }
#           ]
#       }
#   ],
#   "notes": str | null,
#   "duration_minutes": int | null,
#   "created_at": datetime,
#   "updated_at": datetime,
# }

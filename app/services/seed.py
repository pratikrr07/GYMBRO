"""Seed default exercises into MongoDB."""

from datetime import datetime, timezone
from app.database import get_db

DEFAULT_EXERCISES = [
    # ── Chest ──────────────────────────────────────────────────────
    {"name": "Bench Press", "category": "chest"},
    {"name": "Incline Bench Press", "category": "chest"},
    {"name": "Decline Bench Press", "category": "chest"},
    {"name": "Dumbbell Fly", "category": "chest"},
    {"name": "Push-ups", "category": "chest"},
    {"name": "Cable Crossover", "category": "chest"},
    {"name": "Chest Dip", "category": "chest"},
    {"name": "Incline Dumbbell Press", "category": "chest"},
    {"name": "Decline Dumbbell Press", "category": "chest"},
    {"name": "Machine Chest Press", "category": "chest"},
    {"name": "Pec Deck Machine", "category": "chest"},
    {"name": "Dumbbell Pullover", "category": "chest"},
    {"name": "Incline Dumbbell Fly", "category": "chest"},
    {"name": "Landmine Press", "category": "chest"},
    {"name": "Close-Grip Bench Press", "category": "chest"},
    {"name": "Diamond Push-ups", "category": "chest"},

    # ── Back ───────────────────────────────────────────────────────
    {"name": "Deadlift", "category": "back"},
    {"name": "Pull-ups", "category": "back"},
    {"name": "Chin-ups", "category": "back"},
    {"name": "Barbell Row", "category": "back"},
    {"name": "Lat Pulldown", "category": "back"},
    {"name": "Seated Cable Row", "category": "back"},
    {"name": "T-Bar Row", "category": "back"},
    {"name": "Dumbbell Row", "category": "back"},
    {"name": "Face Pulls", "category": "back"},
    {"name": "Pendlay Row", "category": "back"},
    {"name": "Single-Arm Cable Row", "category": "back"},
    {"name": "Rack Pull", "category": "back"},
    {"name": "Meadows Row", "category": "back"},
    {"name": "Wide-Grip Lat Pulldown", "category": "back"},
    {"name": "Close-Grip Lat Pulldown", "category": "back"},
    {"name": "Straight Arm Pulldown", "category": "back"},
    {"name": "Machine Row", "category": "back"},
    {"name": "Inverted Row", "category": "back"},
    {"name": "Hyperextension", "category": "back"},

    # ── Shoulders ──────────────────────────────────────────────────
    {"name": "Overhead Press", "category": "shoulders"},
    {"name": "Lateral Raise", "category": "shoulders"},
    {"name": "Front Raise", "category": "shoulders"},
    {"name": "Reverse Fly", "category": "shoulders"},
    {"name": "Arnold Press", "category": "shoulders"},
    {"name": "Shrugs", "category": "shoulders"},
    {"name": "Upright Row", "category": "shoulders"},
    {"name": "Dumbbell Shoulder Press", "category": "shoulders"},
    {"name": "Machine Shoulder Press", "category": "shoulders"},
    {"name": "Cable Lateral Raise", "category": "shoulders"},
    {"name": "Cable Front Raise", "category": "shoulders"},
    {"name": "Rear Delt Fly Machine", "category": "shoulders"},
    {"name": "Dumbbell Shrugs", "category": "shoulders"},
    {"name": "Barbell Shrugs", "category": "shoulders"},
    {"name": "Lu Raise", "category": "shoulders"},
    {"name": "Behind The Neck Press", "category": "shoulders"},

    # ── Arms (Biceps & Triceps) ────────────────────────────────────
    {"name": "Barbell Curl", "category": "arms"},
    {"name": "Dumbbell Curl", "category": "arms"},
    {"name": "Hammer Curl", "category": "arms"},
    {"name": "Tricep Pushdown", "category": "arms"},
    {"name": "Tricep Dip", "category": "arms"},
    {"name": "Skull Crushers", "category": "arms"},
    {"name": "Overhead Tricep Extension", "category": "arms"},
    {"name": "Preacher Curl", "category": "arms"},
    {"name": "Concentration Curl", "category": "arms"},
    {"name": "EZ Bar Curl", "category": "arms"},
    {"name": "Incline Dumbbell Curl", "category": "arms"},
    {"name": "Spider Curl", "category": "arms"},
    {"name": "Cable Curl", "category": "arms"},
    {"name": "Cable Tricep Kickback", "category": "arms"},
    {"name": "Dumbbell Tricep Kickback", "category": "arms"},
    {"name": "Rope Pushdown", "category": "arms"},
    {"name": "Close-Grip Dumbbell Press", "category": "arms"},
    {"name": "Cross-Body Hammer Curl", "category": "arms"},
    {"name": "Bayesian Curl", "category": "arms"},
    {"name": "21s Bicep Curl", "category": "arms"},
    {"name": "Overhead Cable Curl", "category": "arms"},

    # ── Forearms ───────────────────────────────────────────────────
    {"name": "Wrist Curl", "category": "forearms"},
    {"name": "Reverse Wrist Curl", "category": "forearms"},
    {"name": "Reverse Barbell Curl", "category": "forearms"},
    {"name": "Farmer's Walk", "category": "forearms"},
    {"name": "Plate Pinch Hold", "category": "forearms"},
    {"name": "Dead Hang", "category": "forearms"},
    {"name": "Zottman Curl", "category": "forearms"},

    # ── Legs ───────────────────────────────────────────────────────
    {"name": "Squat", "category": "legs"},
    {"name": "Front Squat", "category": "legs"},
    {"name": "Leg Press", "category": "legs"},
    {"name": "Romanian Deadlift", "category": "legs"},
    {"name": "Lunges", "category": "legs"},
    {"name": "Bulgarian Split Squat", "category": "legs"},
    {"name": "Leg Extension", "category": "legs"},
    {"name": "Leg Curl", "category": "legs"},
    {"name": "Calf Raise", "category": "legs"},
    {"name": "Goblet Squat", "category": "legs"},
    {"name": "Hack Squat", "category": "legs"},
    {"name": "Sumo Squat", "category": "legs"},
    {"name": "Walking Lunges", "category": "legs"},
    {"name": "Reverse Lunges", "category": "legs"},
    {"name": "Seated Calf Raise", "category": "legs"},
    {"name": "Standing Calf Raise", "category": "legs"},
    {"name": "Sissy Squat", "category": "legs"},
    {"name": "Leg Press Calf Raise", "category": "legs"},
    {"name": "Sumo Deadlift", "category": "legs"},
    {"name": "Step-ups", "category": "legs"},
    {"name": "Box Squat", "category": "legs"},
    {"name": "Smith Machine Squat", "category": "legs"},
    {"name": "Pendulum Squat", "category": "legs"},

    # ── Glutes ─────────────────────────────────────────────────────
    {"name": "Hip Thrust", "category": "glutes"},
    {"name": "Barbell Hip Thrust", "category": "glutes"},
    {"name": "Glute Bridge", "category": "glutes"},
    {"name": "Single-Leg Glute Bridge", "category": "glutes"},
    {"name": "Cable Pull-Through", "category": "glutes"},
    {"name": "Kickback (Cable)", "category": "glutes"},
    {"name": "Kickback (Machine)", "category": "glutes"},
    {"name": "Donkey Kick", "category": "glutes"},
    {"name": "Fire Hydrant", "category": "glutes"},
    {"name": "Glute Ham Raise", "category": "glutes"},
    {"name": "Frog Pump", "category": "glutes"},
    {"name": "Hip Abduction Machine", "category": "glutes"},
    {"name": "Banded Clamshell", "category": "glutes"},

    # ── Core ───────────────────────────────────────────────────────
    {"name": "Plank", "category": "core"},
    {"name": "Crunches", "category": "core"},
    {"name": "Russian Twist", "category": "core"},
    {"name": "Hanging Leg Raise", "category": "core"},
    {"name": "Ab Wheel Rollout", "category": "core"},
    {"name": "Cable Woodchop", "category": "core"},
    {"name": "Dead Bug", "category": "core"},
    {"name": "Mountain Climbers", "category": "core"},
    {"name": "Bicycle Crunch", "category": "core"},
    {"name": "Reverse Crunch", "category": "core"},
    {"name": "Decline Sit-ups", "category": "core"},
    {"name": "Pallof Press", "category": "core"},
    {"name": "V-ups", "category": "core"},
    {"name": "Toe Touch", "category": "core"},
    {"name": "Side Plank", "category": "core"},
    {"name": "Flutter Kicks", "category": "core"},
    {"name": "Dragon Flag", "category": "core"},
    {"name": "Leg Raise (Lying)", "category": "core"},
    {"name": "Windshield Wipers", "category": "core"},

    # ── Cardio ─────────────────────────────────────────────────────
    {"name": "Treadmill Run", "category": "cardio"},
    {"name": "Cycling", "category": "cardio"},
    {"name": "Rowing Machine", "category": "cardio"},
    {"name": "Jump Rope", "category": "cardio"},
    {"name": "Stair Climber", "category": "cardio"},
    {"name": "Elliptical", "category": "cardio"},
    {"name": "Swimming", "category": "cardio"},
    {"name": "Battle Ropes", "category": "cardio"},
    {"name": "Burpees", "category": "cardio"},
    {"name": "Sprints", "category": "cardio"},
    {"name": "Box Jumps", "category": "cardio"},
    {"name": "Assault Bike", "category": "cardio"},
    {"name": "Sled Push", "category": "cardio"},
    {"name": "Sled Pull", "category": "cardio"},
    {"name": "Hiking", "category": "cardio"},
    {"name": "Jumping Jacks", "category": "cardio"},
    {"name": "High Knees", "category": "cardio"},
    {"name": "Stair Running", "category": "cardio"},

    # ── Full Body / Compound ───────────────────────────────────────
    {"name": "Clean and Press", "category": "full_body"},
    {"name": "Clean and Jerk", "category": "full_body"},
    {"name": "Snatch", "category": "full_body"},
    {"name": "Thrusters", "category": "full_body"},
    {"name": "Man Makers", "category": "full_body"},
    {"name": "Turkish Get-up", "category": "full_body"},
    {"name": "Kettlebell Swing", "category": "full_body"},
    {"name": "Devil Press", "category": "full_body"},
    {"name": "Wall Ball", "category": "full_body"},
    {"name": "Bear Crawl", "category": "full_body"},

    # ── Stretching / Mobility ──────────────────────────────────────
    {"name": "Foam Rolling", "category": "stretching"},
    {"name": "Hip Flexor Stretch", "category": "stretching"},
    {"name": "Hamstring Stretch", "category": "stretching"},
    {"name": "Shoulder Dislocates", "category": "stretching"},
    {"name": "Pigeon Stretch", "category": "stretching"},
    {"name": "Cat-Cow Stretch", "category": "stretching"},
    {"name": "World's Greatest Stretch", "category": "stretching"},
    {"name": "90/90 Hip Stretch", "category": "stretching"},
]


async def seed_exercises():
    """Insert default exercises if they don't exist yet."""
    db = get_db()
    count = await db.exercises.count_documents({"is_default": True})

    if count >= len(DEFAULT_EXERCISES):
        print(f"📋 Default exercises already seeded ({count} found)")
        return

    now = datetime.now(timezone.utc)
    inserted = 0

    for exercise in DEFAULT_EXERCISES:
        existing = await db.exercises.find_one({
            "name": exercise["name"],
            "is_default": True,
        })
        if not existing:
            await db.exercises.insert_one({
                "name": exercise["name"],
                "category": exercise["category"],
                "is_default": True,
                "created_by": None,
                "created_at": now,
            })
            inserted += 1

    print(f"🏋️ Seeded {inserted} new default exercises (total: {count + inserted})")

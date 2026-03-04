"""Progress routes — calorie trends, workout frequency, strength trends, achievements, water intake, PRs."""

from datetime import datetime, timezone, timedelta
from typing import Optional
from collections import defaultdict

from bson import ObjectId
from fastapi import APIRouter, Depends, Query

from app.database import get_db
from app.utils.security import get_current_user
from app.services.calorie_calculator import calculate_target_calories
from app.schemas.progress import (
    CalorieTrendDay, WorkoutFrequencyWeek, StrengthTrend, StrengthDataPoint,
    PersonalRecord, Achievement, WaterLogResponse, WaterEntry,
    WeightLogEntry, WeightLogResponse, ProgressOverview,
)

router = APIRouter(prefix="/api/progress", tags=["Progress & Achievements"])


# ═══════════════════════════════════════════════════════════════════
#  CALORIE TREND — last N days
# ═══════════════════════════════════════════════════════════════════
@router.get("/calorie-trend", response_model=list[CalorieTrendDay])
async def calorie_trend(
    days: int = Query(30, ge=7, le=90),
    current_user: dict = Depends(get_current_user),
):
    """Daily calorie intake for the last N days."""
    db = get_db()
    now = datetime.now(timezone.utc)
    start = (now - timedelta(days=days)).replace(hour=0, minute=0, second=0, microsecond=0)
    target = calculate_target_calories(current_user)

    day_map: dict[str, dict] = {}
    # Pre-fill all days with zeros
    for i in range(days):
        d = start + timedelta(days=i)
        key = d.strftime("%Y-%m-%d")
        day_map[key] = {"date": key, "calories": 0, "protein_g": 0, "carbs_g": 0, "fat_g": 0, "target": target}

    cursor = db.meals.find({
        "user_id": current_user["id"],
        "date": {"$gte": start},
    })
    async for m in cursor:
        key = m["date"].strftime("%Y-%m-%d")
        if key in day_map:
            day_map[key]["calories"] += m.get("total_calories", 0)
            day_map[key]["protein_g"] += m.get("total_protein_g", 0)
            day_map[key]["carbs_g"] += m.get("total_carbs_g", 0)
            day_map[key]["fat_g"] += m.get("total_fat_g", 0)

    result = sorted(day_map.values(), key=lambda d: d["date"])
    return [CalorieTrendDay(**{k: round(v, 1) if isinstance(v, float) else v for k, v in d.items()}) for d in result]


# ═══════════════════════════════════════════════════════════════════
#  WORKOUT FREQUENCY — last N weeks
# ═══════════════════════════════════════════════════════════════════
@router.get("/workout-frequency", response_model=list[WorkoutFrequencyWeek])
async def workout_frequency(
    weeks: int = Query(12, ge=4, le=52),
    current_user: dict = Depends(get_current_user),
):
    """Workout count per week for the last N weeks."""
    db = get_db()
    now = datetime.now(timezone.utc)
    # Go back to the Monday of `weeks` ago
    days_since_monday = now.weekday()
    current_monday = (now - timedelta(days=days_since_monday)).replace(hour=0, minute=0, second=0, microsecond=0)
    start = current_monday - timedelta(weeks=weeks - 1)

    week_map: dict[str, WorkoutFrequencyWeek] = {}
    for i in range(weeks):
        w_start = start + timedelta(weeks=i)
        key = w_start.strftime("%Y-%m-%d")
        label = w_start.strftime("%b %d")
        week_map[key] = WorkoutFrequencyWeek(week_label=label, week_start=key, count=0)

    cursor = db.workouts.find({
        "user_id": current_user["id"],
        "date": {"$gte": start},
    })
    async for w in cursor:
        w_date = w["date"]
        # Find which week this belongs to
        days_diff = (w_date.replace(tzinfo=timezone.utc) - start).days
        week_idx = days_diff // 7
        if 0 <= week_idx < weeks:
            w_start = start + timedelta(weeks=week_idx)
            key = w_start.strftime("%Y-%m-%d")
            if key in week_map:
                week_map[key].count += 1

    return sorted(week_map.values(), key=lambda w: w.week_start)


# ═══════════════════════════════════════════════════════════════════
#  STRENGTH TREND — per exercise
# ═══════════════════════════════════════════════════════════════════
@router.get("/strength-trend", response_model=list[StrengthTrend])
async def strength_trend(
    current_user: dict = Depends(get_current_user),
):
    """Top 5 exercises with weight progression over time."""
    db = get_db()

    # Gather all exercises and their max weights per workout
    exercise_data: dict[str, list] = defaultdict(list)

    cursor = db.workouts.find({"user_id": current_user["id"]}).sort("date", 1)
    async for w in cursor:
        date_str = w["date"].strftime("%Y-%m-%d")
        for ex in w.get("exercises", []):
            name = ex.get("exercise_name", "Unknown")
            best_weight = 0
            best_reps = 0
            for s in ex.get("sets", []):
                weight = s.get("weight", s.get("weight_kg", 0))
                reps = s.get("reps", 0)
                if weight > best_weight:
                    best_weight = weight
                    best_reps = reps
                if reps > best_reps and weight >= best_weight * 0.8:
                    best_reps = reps
            if best_weight > 0:
                # Epley 1RM estimate: weight × (1 + reps/30)
                e1rm = round(best_weight * (1 + best_reps / 30), 1) if best_reps > 0 else best_weight
                exercise_data[name].append(StrengthDataPoint(
                    date=date_str,
                    max_weight=best_weight,
                    max_reps=best_reps,
                    estimated_1rm=e1rm,
                ))

    # Pick top 5 exercises by number of data points
    sorted_exercises = sorted(exercise_data.items(), key=lambda x: len(x[1]), reverse=True)[:5]

    return [StrengthTrend(exercise_name=name, data_points=pts) for name, pts in sorted_exercises]


# ═══════════════════════════════════════════════════════════════════
#  PERSONAL RECORDS
# ═══════════════════════════════════════════════════════════════════
@router.get("/prs", response_model=list[PersonalRecord])
async def get_personal_records(
    current_user: dict = Depends(get_current_user),
):
    """Get all personal records."""
    db = get_db()
    prs = []
    cursor = db.personal_records.find({"user_id": current_user["id"]}).sort("date", -1)
    async for pr in cursor:
        prs.append(PersonalRecord(
            id=str(pr["_id"]),
            exercise_name=pr["exercise_name"],
            record_type=pr["record_type"],
            value=pr["value"],
            unit=pr["unit"],
            previous_value=pr.get("previous_value"),
            date=pr["date"],
            workout_id=pr.get("workout_id"),
        ))
    return prs


# ═══════════════════════════════════════════════════════════════════
#  WATER INTAKE
# ═══════════════════════════════════════════════════════════════════
@router.post("/water", response_model=WaterLogResponse)
async def log_water(current_user: dict = Depends(get_current_user)):
    """Log one glass of water."""
    db = get_db()
    now = datetime.now(timezone.utc)
    await db.water_logs.insert_one({
        "user_id": current_user["id"],
        "date": now.strftime("%Y-%m-%d"),
        "timestamp": now,
    })
    return await _get_water_status(db, current_user["id"])


@router.delete("/water", response_model=WaterLogResponse)
async def undo_water(current_user: dict = Depends(get_current_user)):
    """Remove the last glass of water logged today."""
    db = get_db()
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    last = await db.water_logs.find_one(
        {"user_id": current_user["id"], "date": today},
        sort=[("timestamp", -1)],
    )
    if last:
        await db.water_logs.delete_one({"_id": last["_id"]})
    return await _get_water_status(db, current_user["id"])


@router.get("/water", response_model=WaterLogResponse)
async def get_water(current_user: dict = Depends(get_current_user)):
    """Get today's water intake."""
    db = get_db()
    return await _get_water_status(db, current_user["id"])


async def _get_water_status(db, user_id: str) -> WaterLogResponse:
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    count = await db.water_logs.count_documents({"user_id": user_id, "date": today})
    goal = 8
    return WaterLogResponse(glasses=count, goal=goal, percentage=round(min(count / goal, 1.0) * 100, 1))


# ═══════════════════════════════════════════════════════════════════
#  ACHIEVEMENTS
# ═══════════════════════════════════════════════════════════════════

# Achievement definitions
ACHIEVEMENT_DEFS = [
    {"id": "first_workout",  "name": "First Rep",         "icon": "🏋️", "description": "Log your first workout",                     "category": "workout"},
    {"id": "10_workouts",    "name": "Getting Serious",   "icon": "💪", "description": "Complete 10 workouts",                        "category": "workout"},
    {"id": "50_workouts",    "name": "Iron Addict",       "icon": "🔩", "description": "Complete 50 workouts",                        "category": "workout"},
    {"id": "100_workouts",   "name": "Century Club",      "icon": "💯", "description": "Complete 100 workouts",                       "category": "workout"},
    {"id": "beast_mode",     "name": "Beast Mode",        "icon": "🦁", "description": "Log 5+ exercises in a single workout",        "category": "workout"},
    {"id": "first_meal",     "name": "Fuel Up",           "icon": "🍽️", "description": "Log your first meal",                         "category": "nutrition"},
    {"id": "50_meals",       "name": "Meal Prepper",      "icon": "🥗", "description": "Log 50 meals",                                "category": "nutrition"},
    {"id": "on_target",      "name": "On Target",         "icon": "🎯", "description": "Hit your daily calorie goal within ±5%",      "category": "nutrition"},
    {"id": "streak_3",       "name": "Hat Trick",         "icon": "🔥", "description": "3-day workout streak",                        "category": "consistency"},
    {"id": "streak_7",       "name": "One Week Warrior",  "icon": "⚡", "description": "7-day workout streak",                        "category": "consistency"},
    {"id": "streak_30",      "name": "Unstoppable",       "icon": "🏆", "description": "30-day workout streak",                       "category": "consistency"},
    {"id": "hydrated",       "name": "Stay Hydrated",     "icon": "💧", "description": "Drink 8 glasses of water in a day",           "category": "hydration"},
    {"id": "pr_set",         "name": "New PR!",           "icon": "🏅", "description": "Set a personal record on any exercise",       "category": "workout"},
    {"id": "early_bird",     "name": "Early Bird",        "icon": "🌅", "description": "Log a workout before 7 AM",                   "category": "consistency"},
]


@router.get("/achievements", response_model=list[Achievement])
async def get_achievements(current_user: dict = Depends(get_current_user)):
    """Get all achievements with unlock status."""
    db = get_db()

    # Fetch user's unlocked achievements
    unlocked_map = {}
    cursor = db.achievements.find({"user_id": current_user["id"]})
    async for a in cursor:
        unlocked_map[a["achievement_id"]] = a.get("unlocked_at", "")

    # Gather stats for progress
    total_workouts = await db.workouts.count_documents({"user_id": current_user["id"]})
    total_meals = await db.meals.count_documents({"user_id": current_user["id"]})
    total_prs = await db.personal_records.count_documents({"user_id": current_user["id"]})

    # Streak calculation
    now = datetime.now(timezone.utc)
    workout_dates = set()
    async for w in db.workouts.find({"user_id": current_user["id"]}, {"date": 1}):
        workout_dates.add(w["date"].strftime("%Y-%m-%d"))
    streak = 0
    check_date = now.date()
    while True:
        if check_date.strftime("%Y-%m-%d") in workout_dates:
            streak += 1
            check_date -= timedelta(days=1)
        elif check_date == now.date():
            check_date -= timedelta(days=1)
        else:
            break

    # Water today
    today_str = now.strftime("%Y-%m-%d")
    water_today = await db.water_logs.count_documents({"user_id": current_user["id"], "date": today_str})

    # Build achievement list with progress
    result = []
    for defn in ACHIEVEMENT_DEFS:
        aid = defn["id"]
        is_unlocked = aid in unlocked_map
        progress = None
        progress_text = None

        if aid == "first_workout":
            progress = min(total_workouts, 1)
            progress_text = f"{min(total_workouts, 1)} / 1"
        elif aid == "10_workouts":
            progress = min(total_workouts / 10, 1.0)
            progress_text = f"{min(total_workouts, 10)} / 10"
        elif aid == "50_workouts":
            progress = min(total_workouts / 50, 1.0)
            progress_text = f"{min(total_workouts, 50)} / 50"
        elif aid == "100_workouts":
            progress = min(total_workouts / 100, 1.0)
            progress_text = f"{min(total_workouts, 100)} / 100"
        elif aid == "first_meal":
            progress = min(total_meals, 1)
            progress_text = f"{min(total_meals, 1)} / 1"
        elif aid == "50_meals":
            progress = min(total_meals / 50, 1.0)
            progress_text = f"{min(total_meals, 50)} / 50"
        elif aid == "streak_3":
            progress = min(streak / 3, 1.0)
            progress_text = f"{min(streak, 3)} / 3 days"
        elif aid == "streak_7":
            progress = min(streak / 7, 1.0)
            progress_text = f"{min(streak, 7)} / 7 days"
        elif aid == "streak_30":
            progress = min(streak / 30, 1.0)
            progress_text = f"{min(streak, 30)} / 30 days"
        elif aid == "hydrated":
            progress = min(water_today / 8, 1.0)
            progress_text = f"{min(water_today, 8)} / 8 glasses"
        elif aid == "pr_set":
            progress = min(total_prs, 1)
            progress_text = f"{total_prs} PRs set"

        result.append(Achievement(
            id=aid,
            name=defn["name"],
            description=defn["description"],
            icon=defn["icon"],
            category=defn["category"],
            unlocked=is_unlocked,
            unlocked_at=unlocked_map.get(aid),
            progress=progress,
            progress_text=progress_text,
        ))

    return result


@router.post("/achievements/check")
async def check_achievements(current_user: dict = Depends(get_current_user)):
    """Check and award any newly earned achievements. Returns list of newly unlocked."""
    db = get_db()
    now = datetime.now(timezone.utc)
    now_str = now.isoformat()

    # Get already unlocked
    unlocked_ids = set()
    async for a in db.achievements.find({"user_id": current_user["id"]}):
        unlocked_ids.add(a["achievement_id"])

    # Gather stats
    total_workouts = await db.workouts.count_documents({"user_id": current_user["id"]})
    total_meals = await db.meals.count_documents({"user_id": current_user["id"]})
    total_prs = await db.personal_records.count_documents({"user_id": current_user["id"]})

    # Check beast mode
    has_beast = False
    async for w in db.workouts.find({"user_id": current_user["id"]}):
        if len(w.get("exercises", [])) >= 5:
            has_beast = True
            break

    # Streak
    workout_dates = set()
    async for w in db.workouts.find({"user_id": current_user["id"]}, {"date": 1}):
        workout_dates.add(w["date"].strftime("%Y-%m-%d"))
    streak = 0
    check_date = now.date()
    while True:
        if check_date.strftime("%Y-%m-%d") in workout_dates:
            streak += 1
            check_date -= timedelta(days=1)
        elif check_date == now.date():
            check_date -= timedelta(days=1)
        else:
            break

    # Water
    today_str = now.strftime("%Y-%m-%d")
    water_today = await db.water_logs.count_documents({"user_id": current_user["id"], "date": today_str})

    # Calorie target check
    target = calculate_target_calories(current_user)
    day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    day_end = day_start + timedelta(days=1)
    total_cal = 0
    async for m in db.meals.find({"user_id": current_user["id"], "date": {"$gte": day_start, "$lt": day_end}}):
        total_cal += m.get("total_calories", 0)
    on_target = target > 0 and abs(total_cal - target) / target <= 0.05 and total_cal > 0

    # Early bird check
    has_early = False
    async for w in db.workouts.find({"user_id": current_user["id"]}):
        if w["date"].hour < 7:
            has_early = True
            break

    # Check conditions
    checks = {
        "first_workout": total_workouts >= 1,
        "10_workouts":   total_workouts >= 10,
        "50_workouts":   total_workouts >= 50,
        "100_workouts":  total_workouts >= 100,
        "beast_mode":    has_beast,
        "first_meal":    total_meals >= 1,
        "50_meals":      total_meals >= 50,
        "on_target":     on_target,
        "streak_3":      streak >= 3,
        "streak_7":      streak >= 7,
        "streak_30":     streak >= 30,
        "hydrated":      water_today >= 8,
        "pr_set":        total_prs >= 1,
        "early_bird":    has_early,
    }

    newly_unlocked = []
    for aid, condition in checks.items():
        if condition and aid not in unlocked_ids:
            await db.achievements.insert_one({
                "user_id": current_user["id"],
                "achievement_id": aid,
                "unlocked_at": now_str,
            })
            # Find the definition
            defn = next((d for d in ACHIEVEMENT_DEFS if d["id"] == aid), None)
            if defn:
                newly_unlocked.append({
                    "id": aid,
                    "name": defn["name"],
                    "icon": defn["icon"],
                    "description": defn["description"],
                })

    return {"newly_unlocked": newly_unlocked, "total_unlocked": len(unlocked_ids) + len(newly_unlocked)}


# ═══════════════════════════════════════════════════════════════════
#  WORKOUT STREAK HEATMAP — GitHub-style calendar
# ═══════════════════════════════════════════════════════════════════
@router.get("/heatmap")
async def workout_heatmap(
    year: int = Query(None),
    current_user: dict = Depends(get_current_user),
):
    """Return daily workout count for a full year (GitHub-style heatmap data)."""
    db = get_db()
    now = datetime.now(timezone.utc)
    target_year = year or now.year

    # Build date range: Jan 1 – Dec 31 of target year
    start = datetime(target_year, 1, 1, tzinfo=timezone.utc)
    end = datetime(target_year, 12, 31, 23, 59, 59, tzinfo=timezone.utc)

    # Don't go past today
    if end > now:
        end = now

    # Pre-fill all days
    day_map: dict[str, int] = {}
    d = start
    while d <= end:
        day_map[d.strftime("%Y-%m-%d")] = 0
        d += timedelta(days=1)

    # Count workouts per day
    cursor = db.workouts.find({
        "user_id": current_user["id"],
        "date": {"$gte": start, "$lte": end},
    })
    async for w in cursor:
        key = w["date"].strftime("%Y-%m-%d")
        if key in day_map:
            day_map[key] += 1

    # Calculate streaks
    all_dates = sorted(day_map.keys())
    current_streak = 0
    longest_streak = 0
    temp_streak = 0
    total_workouts = sum(day_map.values())
    active_days = sum(1 for v in day_map.values() if v > 0)

    for date_str in all_dates:
        if day_map[date_str] > 0:
            temp_streak += 1
            longest_streak = max(longest_streak, temp_streak)
        else:
            temp_streak = 0

    # Current streak: count backwards from today
    today_str = now.strftime("%Y-%m-%d")
    check = now
    while True:
        key = check.strftime("%Y-%m-%d")
        if key in day_map and day_map[key] > 0:
            current_streak += 1
            check -= timedelta(days=1)
        else:
            break

    days = [{"date": k, "count": v} for k, v in sorted(day_map.items())]

    return {
        "year": target_year,
        "days": days,
        "stats": {
            "total_workouts": total_workouts,
            "active_days": active_days,
            "current_streak": current_streak,
            "longest_streak": longest_streak,
        },
    }


# ═══════════════════════════════════════════════════════════════════
#  WEIGHT LOG — track body weight over time
# ═══════════════════════════════════════════════════════════════════
@router.post("/weight-log", response_model=WeightLogEntry)
async def log_weight(
    weight_kg: float = Query(..., gt=20, lt=500),
    note: str = Query("", max_length=200),
    current_user: dict = Depends(get_current_user),
):
    """Log a weight entry."""
    db = get_db()
    now = datetime.now(timezone.utc)
    today = now.strftime("%Y-%m-%d")

    # Upsert: one entry per day
    result = await db.weight_logs.update_one(
        {"user_id": current_user["id"], "date": today},
        {"$set": {
            "user_id": current_user["id"],
            "date": today,
            "weight_kg": weight_kg,
            "note": note,
            "timestamp": now,
        }},
        upsert=True,
    )

    # Also update user profile weight
    await db.users.update_one(
        {"_id": ObjectId(current_user["id"])},
        {"$set": {"weight_kg": weight_kg, "updated_at": now}},
    )

    entry_id = result.upserted_id or (await db.weight_logs.find_one(
        {"user_id": current_user["id"], "date": today}
    ))["_id"]

    return WeightLogEntry(id=str(entry_id), date=today, weight_kg=weight_kg, note=note)


@router.get("/weight-log", response_model=WeightLogResponse)
async def get_weight_log(
    days: int = Query(90, ge=7, le=365),
    current_user: dict = Depends(get_current_user),
):
    """Get weight log entries for the last N days."""
    db = get_db()
    now = datetime.now(timezone.utc)
    start = (now - timedelta(days=days)).replace(hour=0, minute=0, second=0, microsecond=0)

    entries = []
    cursor = db.weight_logs.find(
        {"user_id": current_user["id"], "date": {"$gte": start.strftime("%Y-%m-%d")}},
    ).sort("date", 1)
    async for e in cursor:
        entries.append(WeightLogEntry(
            id=str(e["_id"]),
            date=e["date"],
            weight_kg=e["weight_kg"],
            note=e.get("note", ""),
        ))

    current_weight = current_user.get("weight_kg")
    target_weight = current_user.get("target_weight_kg")
    start_weight = entries[0].weight_kg if entries else current_weight
    total_change = round(current_weight - start_weight, 1) if current_weight and start_weight else None

    return WeightLogResponse(
        entries=entries,
        current_weight=current_weight,
        start_weight=start_weight,
        target_weight=target_weight,
        total_change=total_change,
    )


@router.delete("/weight-log/{entry_id}")
async def delete_weight_log(
    entry_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Delete a weight log entry."""
    db = get_db()
    result = await db.weight_logs.delete_one(
        {"_id": ObjectId(entry_id), "user_id": current_user["id"]}
    )
    if result.deleted_count == 0:
        from fastapi import HTTPException
        raise HTTPException(404, "Entry not found")
    return {"ok": True}


# ═══════════════════════════════════════════════════════════════════
#  PROGRESS OVERVIEW — aggregated stats
# ═══════════════════════════════════════════════════════════════════
@router.get("/overview", response_model=ProgressOverview)
async def progress_overview(
    current_user: dict = Depends(get_current_user),
):
    """Get aggregated progress stats for the overview cards."""
    db = get_db()
    now = datetime.now(timezone.utc)

    total_workouts = await db.workouts.count_documents({"user_id": current_user["id"]})
    total_meals = await db.meals.count_documents({"user_id": current_user["id"]})
    total_prs = await db.personal_records.count_documents({"user_id": current_user["id"]})

    # Achievements
    achievements_unlocked = await db.achievements.count_documents({"user_id": current_user["id"]})

    # Active days + streaks
    workout_dates = set()
    total_volume = 0.0
    total_duration = 0.0
    async for w in db.workouts.find({"user_id": current_user["id"]}):
        workout_dates.add(w["date"].strftime("%Y-%m-%d"))
        # Calculate volume
        for ex in w.get("exercises", []):
            for s in ex.get("sets", []):
                wt = s.get("weight", s.get("weight_kg", 0))
                reps = s.get("reps", 0)
                total_volume += wt * reps
        total_duration += w.get("duration_min", 0)

    active_days = len(workout_dates)

    # Current and longest streak
    current_streak = 0
    check = now.date()
    while True:
        if check.strftime("%Y-%m-%d") in workout_dates:
            current_streak += 1
            check -= timedelta(days=1)
        elif check == now.date():
            check -= timedelta(days=1)
        else:
            break

    longest_streak = 0
    temp = 0
    sorted_dates = sorted(workout_dates)
    prev_date = None
    for d in sorted_dates:
        cur = datetime.strptime(d, "%Y-%m-%d").date()
        if prev_date is None or (cur - prev_date).days == 1:
            temp += 1
        elif (cur - prev_date).days > 1:
            temp = 1
        longest_streak = max(longest_streak, temp)
        prev_date = cur

    # Member since
    created = current_user.get("created_at")
    if created:
        if created.tzinfo is None:
            created = created.replace(tzinfo=timezone.utc)
        member_days = (now - created).days
    else:
        member_days = 0

    avg_duration = round(total_duration / total_workouts, 1) if total_workouts > 0 else 0

    return ProgressOverview(
        total_workouts=total_workouts,
        total_meals=total_meals,
        active_days=active_days,
        current_streak=current_streak,
        longest_streak=longest_streak,
        total_volume_kg=round(total_volume, 1),
        total_calories_burned=0,
        avg_workout_duration_min=avg_duration,
        total_prs=total_prs,
        achievements_unlocked=achievements_unlocked,
        member_since_days=member_days,
    )

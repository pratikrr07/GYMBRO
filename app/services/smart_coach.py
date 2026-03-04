"""
🧠 GYMBRO Smart Coach — The AI engine that makes GYMBRO an "AI Fitness Coach"

Pulls ALL user data (workouts, meals, weight, PRs, water, streaks, achievements),
runs 20+ analytical rules, and produces a rich, personalized coaching report.

When Gemini API key is available → sends data snapshot to AI for natural language insights.
When not available → uses a sophisticated rule-based analysis engine that still
provides genuinely useful, data-driven coaching (not generic tips).
"""

import json
import random
import math
from datetime import datetime, timezone, timedelta
from collections import defaultdict, Counter

from app.config import get_settings
from app.database import get_db
from app.services.calorie_calculator import get_full_nutrition_plan

settings = get_settings()

# ─────────────────────────────────────────────────────────────────
#  MUSCLE GROUP MAPPING — exercises → muscle groups
# ─────────────────────────────────────────────────────────────────
MUSCLE_MAP = {
    "chest": ["bench press", "incline", "decline", "chest press", "push up", "push-up",
              "fly", "flye", "dumbbell press", "cable crossover", "pec", "dip"],
    "back": ["row", "pull up", "pull-up", "pullup", "lat pulldown", "pulldown", "deadlift",
             "chin up", "chin-up", "cable row", "t-bar", "face pull", "back extension"],
    "shoulders": ["overhead press", "ohp", "military press", "lateral raise", "front raise",
                  "rear delt", "shoulder press", "arnold", "upright row", "shrug"],
    "biceps": ["bicep curl", "hammer curl", "preacher curl", "concentration curl",
               "barbell curl", "ez curl", "cable curl", "bicep"],
    "triceps": ["tricep", "pushdown", "skull crusher", "close grip bench",
                "overhead extension", "kickback", "dip"],
    "quads": ["squat", "leg press", "leg extension", "lunge", "front squat",
              "hack squat", "goblet squat", "step up", "quad"],
    "hamstrings": ["leg curl", "romanian deadlift", "rdl", "stiff leg",
                   "good morning", "hamstring", "nordic curl"],
    "glutes": ["hip thrust", "glute bridge", "bulgarian split", "squat",
               "lunge", "step up", "glute"],
    "core": ["plank", "crunch", "sit up", "sit-up", "ab wheel", "hanging leg raise",
             "russian twist", "cable crunch", "woodchop", "pallof", "abs", "core"],
    "calves": ["calf raise", "standing calf", "seated calf", "calf"],
    "cardio": ["running", "cycling", "swimming", "rowing", "jump rope",
               "elliptical", "stairmaster", "hiit", "cardio", "treadmill"],
}


def _classify_muscle_group(exercise_name: str) -> list[str]:
    """Classify an exercise name into muscle groups."""
    name = exercise_name.lower()
    groups = []
    for muscle, keywords in MUSCLE_MAP.items():
        for kw in keywords:
            if kw in name:
                groups.append(muscle)
                break
    return groups if groups else ["other"]


# ─────────────────────────────────────────────────────────────────
#  DATA COLLECTION — gather all user fitness data
# ─────────────────────────────────────────────────────────────────
async def _collect_user_data(user: dict, days: int = 30) -> dict:
    """Pull all user data from the last N days for analysis."""
    db = get_db()
    uid = user["id"]
    now = datetime.now(timezone.utc)
    start = now - timedelta(days=days)
    start_str = start.strftime("%Y-%m-%d")

    # ── Workouts ──
    workouts = []
    all_workouts = []
    async for w in db.workouts.find({"user_id": uid}).sort("date", -1):
        w_date = w["date"]
        if w_date.tzinfo is None:
            w_date = w_date.replace(tzinfo=timezone.utc)
        w_data = {
            "name": w.get("name", "Workout"),
            "date": w_date.strftime("%Y-%m-%d"),
            "exercises": [],
            "duration_min": w.get("duration_minutes", w.get("duration_min", 0)),
            "total_volume": 0,
            "total_sets": 0,
        }
        for ex in w.get("exercises", []):
            ex_name = ex.get("exercise_name", "Unknown")
            sets_data = []
            for s in ex.get("sets", []):
                wt = s.get("weight", s.get("weight_kg", 0))
                reps = s.get("reps", 0)
                w_data["total_volume"] += wt * reps
                w_data["total_sets"] += 1
                sets_data.append({"weight": wt, "reps": reps})
            w_data["exercises"].append({
                "name": ex_name,
                "sets": sets_data,
                "muscle_groups": _classify_muscle_group(ex_name),
            })
        all_workouts.append(w_data)
        if w_date >= start:
            workouts.append(w_data)

    # ── Meals ──
    meals = []
    async for m in db.meals.find({"user_id": uid, "date": {"$gte": start}}):
        m_date = m["date"]
        if m_date.tzinfo is None:
            m_date = m_date.replace(tzinfo=timezone.utc)
        meals.append({
            "date": m_date.strftime("%Y-%m-%d"),
            "calories": m.get("total_calories", 0),
            "protein_g": m.get("total_protein_g", 0),
            "carbs_g": m.get("total_carbs_g", 0),
            "fat_g": m.get("total_fat_g", 0),
        })

    # ── Weight logs ──
    weight_logs = []
    async for wl in db.weight_logs.find(
        {"user_id": uid, "date": {"$gte": start_str}}
    ).sort("date", 1):
        weight_logs.append({
            "date": wl["date"],
            "weight_kg": wl["weight_kg"],
        })

    # ── Water logs ──
    water_days = defaultdict(int)
    async for wt in db.water_logs.find({"user_id": uid}):
        water_days[wt["date"]] += 1

    # ── PRs ──
    prs = []
    async for pr in db.personal_records.find({"user_id": uid}):
        prs.append({
            "exercise": pr["exercise_name"],
            "type": pr["record_type"],
            "value": pr["value"],
            "unit": pr.get("unit", "kg"),
            "date": pr.get("date", ""),
        })

    # ── Achievements ──
    achievements = []
    async for a in db.achievements.find({"user_id": uid}):
        achievements.append(a["achievement_id"])

    # ── Streak calculation ──
    workout_dates = set()
    for w in all_workouts:
        workout_dates.add(w["date"])

    current_streak = 0
    check = now.date()
    while True:
        key = check.strftime("%Y-%m-%d")
        if key in workout_dates:
            current_streak += 1
            check -= timedelta(days=1)
        elif check == now.date():
            check -= timedelta(days=1)
        else:
            break

    return {
        "user_profile": {
            "username": user.get("username", "Athlete"),
            "age": user.get("age"),
            "gender": user.get("gender"),
            "weight_kg": user.get("weight_kg"),
            "height_cm": user.get("height_cm"),
            "goal": user.get("goal", "maintain"),
            "target_weight_kg": user.get("target_weight_kg"),
            "activity_level": user.get("activity_level"),
        },
        "period_days": days,
        "workouts": workouts,
        "all_workouts": all_workouts,
        "meals": meals,
        "weight_logs": weight_logs,
        "water_days": dict(water_days),
        "prs": prs,
        "achievements": achievements,
        "current_streak": current_streak,
        "total_workouts_all_time": len(all_workouts),
    }


# ─────────────────────────────────────────────────────────────────
#  RULE-BASED ANALYSIS ENGINE — 20+ data-driven insights
# ─────────────────────────────────────────────────────────────────
def _analyze_data(data: dict) -> dict:
    """Run comprehensive rule-based analysis on user data."""
    profile = data["user_profile"]
    workouts = data["workouts"]
    meals = data["meals"]
    weight_logs = data["weight_logs"]
    water_days = data["water_days"]
    prs = data["prs"]
    period = data["period_days"]
    streak = data["current_streak"]

    insights = []
    warnings = []
    wins = []
    score_components = {}

    # ── 1. TRAINING CONSISTENCY ──
    workout_count = len(workouts)
    workouts_per_week = round(workout_count / max(period / 7, 1), 1)

    if workouts_per_week >= 5:
        score_components["consistency"] = 100
        wins.append(f"🔥 Elite consistency! You averaged {workouts_per_week} workouts/week over the last {period} days.")
    elif workouts_per_week >= 4:
        score_components["consistency"] = 90
        wins.append(f"💪 Great consistency at {workouts_per_week} sessions/week. Right in the sweet spot for progress.")
    elif workouts_per_week >= 3:
        score_components["consistency"] = 75
        insights.append(f"📊 You averaged {workouts_per_week} workouts/week. Aim for 4+ to maximize gains (Schoenfeld, 2016).")
    elif workouts_per_week >= 2:
        score_components["consistency"] = 55
        insights.append(f"📉 Only {workouts_per_week} sessions/week. Each muscle group needs 2x/week stimulus for optimal growth.")
    elif workouts_per_week >= 1:
        score_components["consistency"] = 35
        warnings.append(f"⚠️ Only {workouts_per_week} workouts/week detected. You need at least 3 sessions/week for meaningful progress.")
    else:
        score_components["consistency"] = 10
        warnings.append(f"🚨 Very few workouts in the last {period} days. Consistency is the #1 predictor of results.")

    # ── 2. MUSCLE GROUP BALANCE ──
    muscle_volume = defaultdict(float)
    muscle_sets = defaultdict(int)
    exercise_frequency = Counter()

    for w in workouts:
        for ex in w["exercises"]:
            exercise_frequency[ex["name"]] += 1
            for mg in ex["muscle_groups"]:
                for s in ex["sets"]:
                    muscle_volume[mg] += s["weight"] * s["reps"]
                    muscle_sets[mg] += 1

    trained_muscles = set(muscle_volume.keys()) - {"other", "cardio"}
    major_muscles = {"chest", "back", "shoulders", "quads", "hamstrings", "glutes"}
    missing_muscles = major_muscles - trained_muscles

    if missing_muscles and workout_count > 3:
        warnings.append(f"🎯 Muscle imbalance detected! You haven't trained: {', '.join(sorted(missing_muscles))}. This creates injury risk and asymmetric development.")
        score_components["balance"] = max(20, 100 - len(missing_muscles) * 15)
    elif trained_muscles:
        # Check ratio imbalance
        if muscle_sets:
            avg_sets = sum(muscle_sets.values()) / len(muscle_sets)
            over_trained = [m for m, s in muscle_sets.items() if s > avg_sets * 2 and m not in ("other", "cardio")]
            under_trained = [m for m, s in muscle_sets.items() if s < avg_sets * 0.4 and m in major_muscles]

            if over_trained:
                insights.append(f"📊 You're heavily favoring {', '.join(over_trained)}. Consider balancing volume across all muscle groups.")
            if under_trained:
                insights.append(f"📉 Under-trained muscles: {', '.join(under_trained)}. Add 2-3 sets/week to prevent imbalances.")

            score_components["balance"] = max(40, 100 - len(missing_muscles) * 15 - len(under_trained) * 10)
        else:
            score_components["balance"] = 50
    else:
        score_components["balance"] = 50

    # ── 3. VOLUME PROGRESSION ──
    if len(workouts) >= 4:
        first_half = workouts[len(workouts)//2:]  # older (workouts sorted desc)
        second_half = workouts[:len(workouts)//2]  # newer

        vol_first = sum(w["total_volume"] for w in first_half) / max(len(first_half), 1)
        vol_second = sum(w["total_volume"] for w in second_half) / max(len(second_half), 1)

        if vol_first > 0:
            vol_change = ((vol_second - vol_first) / vol_first) * 100
            if vol_change > 10:
                wins.append(f"📈 Your training volume increased {vol_change:.0f}% — progressive overload in action!")
                score_components["progression"] = min(100, 70 + vol_change)
            elif vol_change > 0:
                insights.append(f"📊 Volume up {vol_change:.0f}%. Try increasing weight by 2.5-5% when you hit all reps for 2 sessions.")
                score_components["progression"] = 60 + vol_change
            elif vol_change > -10:
                insights.append("⚖️ Your training volume is flat. Progressive overload is the #1 driver of muscle growth.")
                score_components["progression"] = 50
            else:
                warnings.append(f"📉 Training volume dropped {abs(vol_change):.0f}%. If intentional (deload), great. If not, you may be losing gains.")
                score_components["progression"] = max(20, 50 + vol_change)
        else:
            score_components["progression"] = 50
    else:
        score_components["progression"] = 50

    # ── 4. NUTRITION ADHERENCE ──
    if meals:
        nutrition_plan = get_full_nutrition_plan(profile)
        target_cal = nutrition_plan.get("target_calories", 2000)
        target_protein = nutrition_plan.get("protein_g", 150)

        # Group meals by day
        daily_cals = defaultdict(float)
        daily_protein = defaultdict(float)
        for m in meals:
            daily_cals[m["date"]] += m["calories"]
            daily_protein[m["date"]] += m["protein_g"]

        logged_days = len(daily_cals)
        avg_cals = sum(daily_cals.values()) / max(logged_days, 1)
        avg_protein = sum(daily_protein.values()) / max(logged_days, 1)
        cal_adherence = 100 - abs(avg_cals - target_cal) / target_cal * 100

        # Logging consistency
        logging_pct = (logged_days / period) * 100

        if logging_pct >= 80:
            wins.append(f"📝 You logged meals {logged_days} out of {period} days ({logging_pct:.0f}%). Trackers lose 2x more weight (Kaiser et al., 2013).")
        elif logging_pct >= 50:
            insights.append(f"📝 Meal logging at {logging_pct:.0f}%. Aim for 80%+ — consistency in tracking predicts results.")
        elif logged_days > 0:
            warnings.append(f"📝 Only {logged_days} days of meal logging in {period} days. What gets measured gets managed.")

        if avg_cals > 0:
            goal = profile.get("goal", "maintain")
            if goal == "lose_weight" and avg_cals > target_cal * 1.1:
                warnings.append(f"⚠️ Averaging {avg_cals:.0f} kcal/day vs your {target_cal:.0f} target. You're {avg_cals - target_cal:.0f} kcal over — that's ~{(avg_cals - target_cal) * 7 / 7700:.1f} kg/week of potential fat gain.")
            elif goal == "gain_muscle" and avg_cals < target_cal * 0.9:
                warnings.append(f"⚠️ Averaging {avg_cals:.0f} kcal/day vs your {target_cal:.0f} target. Under-eating makes muscle gain nearly impossible.")
            elif cal_adherence > 85:
                wins.append(f"🎯 Calorie adherence: {cal_adherence:.0f}% — averaging {avg_cals:.0f} vs {target_cal:.0f} target. Excellent discipline!")

        if avg_protein > 0:
            protein_per_kg = avg_protein / max(profile.get("weight_kg", 70), 1)
            if protein_per_kg >= 1.6:
                wins.append(f"🥩 Protein intake: {avg_protein:.0f}g/day ({protein_per_kg:.1f}g/kg). Optimal for muscle growth/retention.")
                score_components["nutrition"] = 90
            elif protein_per_kg >= 1.2:
                insights.append(f"🥩 Protein at {avg_protein:.0f}g/day ({protein_per_kg:.1f}g/kg). Aim for 1.6-2.2g/kg for optimal results.")
                score_components["nutrition"] = 70
            else:
                warnings.append(f"⚠️ Protein only {avg_protein:.0f}g/day ({protein_per_kg:.1f}g/kg). You need 1.6-2.2g/kg to maximize muscle protein synthesis.")
                score_components["nutrition"] = 40
        else:
            score_components["nutrition"] = max(30, cal_adherence * 0.7) if avg_cals > 0 else 30
    else:
        warnings.append("📝 No meal data logged. Nutrition is 70% of your results — start tracking to unlock real progress!")
        score_components["nutrition"] = 15

    # ── 5. WEIGHT TREND ──
    if len(weight_logs) >= 3:
        first_weight = weight_logs[0]["weight_kg"]
        last_weight = weight_logs[-1]["weight_kg"]
        weight_change = last_weight - first_weight
        goal = profile.get("goal", "maintain")

        if goal == "lose_weight":
            if weight_change < -0.5:
                wins.append(f"⬇️ Weight down {abs(weight_change):.1f} kg ({first_weight:.1f} → {last_weight:.1f}). On track for your goal!")
                score_components["weight_progress"] = min(100, 70 + abs(weight_change) * 10)
            elif weight_change > 0.5:
                warnings.append(f"⬆️ Weight up {weight_change:.1f} kg despite a fat loss goal. Review your calorie intake.")
                score_components["weight_progress"] = max(20, 50 - weight_change * 10)
            else:
                insights.append(f"⚖️ Weight stable at ~{last_weight:.1f} kg. If cutting, you may need a slightly larger deficit.")
                score_components["weight_progress"] = 55
        elif goal == "gain_muscle":
            if weight_change > 0.3:
                rate_per_week = weight_change / max(period / 7, 1)
                if rate_per_week > 0.5:
                    insights.append(f"⬆️ Gaining {rate_per_week:.2f} kg/week — that's fast. Aim for 0.25-0.5 kg/week to minimize fat gain.")
                else:
                    wins.append(f"⬆️ Weight up {weight_change:.1f} kg at a controlled {rate_per_week:.2f} kg/week. Clean bulk territory!")
                score_components["weight_progress"] = 85
            elif weight_change < -0.5:
                warnings.append(f"⬇️ Losing weight on a muscle gain goal. Increase calories by 200-300 kcal/day.")
                score_components["weight_progress"] = 30
            else:
                insights.append("⚖️ Weight stable on a bulk. Increase calories by 100-200 kcal/day to fuel muscle growth.")
                score_components["weight_progress"] = 55
        else:
            if abs(weight_change) < 1:
                wins.append(f"⚖️ Weight stable at ~{last_weight:.1f} kg. Perfect for maintenance!")
                score_components["weight_progress"] = 90
            else:
                insights.append(f"⚖️ Weight shifted {weight_change:+.1f} kg. Maintenance typically means ±1 kg fluctuation.")
                score_components["weight_progress"] = 70
    else:
        insights.append("📏 Log your weight regularly (2-3x/week) to track body composition changes.")
        score_components["weight_progress"] = 40

    # ── 6. HYDRATION ──
    recent_water = {k: v for k, v in water_days.items() if k >= (datetime.now(timezone.utc) - timedelta(days=7)).strftime("%Y-%m-%d")}
    if recent_water:
        avg_glasses = sum(recent_water.values()) / len(recent_water)
        if avg_glasses >= 8:
            wins.append(f"💧 Averaging {avg_glasses:.0f} glasses/day — great hydration! Even 2% dehydration cuts strength by 10-15%.")
            score_components["hydration"] = 95
        elif avg_glasses >= 5:
            insights.append(f"💧 {avg_glasses:.0f} glasses/day — aim for 8+. Muscle is 76% water; dehydration kills performance.")
            score_components["hydration"] = 60
        else:
            warnings.append(f"💧 Only {avg_glasses:.0f} glasses/day. Dehydration reduces strength by 10-15% and power by 20%. Drink up!")
            score_components["hydration"] = 30
    else:
        score_components["hydration"] = 40

    # ── 7. STREAK & HABIT ──
    if streak >= 7:
        wins.append(f"🔥 {streak}-day workout streak! It takes 66 days to form a habit (Lally et al., 2010). Keep going!")
    elif streak >= 3:
        insights.append(f"🔥 {streak}-day streak. Build momentum — aim for 7+ days. Consistency beats intensity every time.")
    elif streak == 0 and data["total_workouts_all_time"] > 0:
        warnings.append("⏸️ Your streak is broken. Remember: even a 20-minute workout maintains the habit. Get back on track today!")

    # ── 8. WORKOUT VARIETY ──
    if exercise_frequency and workout_count >= 3:
        unique_exercises = len(exercise_frequency)
        if unique_exercises < 4:
            insights.append(f"🔄 Only {unique_exercises} different exercises used. Variety prevents plateaus and ensures balanced development.")
        elif unique_exercises > 15:
            wins.append(f"🔄 {unique_exercises} different exercises — excellent variety for well-rounded fitness!")

    # ── 9. REST DAYS ──
    if workouts:
        workout_dates = sorted(set(w["date"] for w in workouts))
        consecutive_days = 0
        max_consecutive = 0
        for i in range(1, len(workout_dates)):
            d1 = datetime.strptime(workout_dates[i-1], "%Y-%m-%d")
            d2 = datetime.strptime(workout_dates[i], "%Y-%m-%d")
            if (d2 - d1).days == 1:
                consecutive_days += 1
                max_consecutive = max(max_consecutive, consecutive_days)
            else:
                consecutive_days = 0
        if max_consecutive >= 6:
            warnings.append(f"⚠️ {max_consecutive + 1} consecutive training days detected. Muscles grow during REST, not training. Take at least 1-2 rest days/week.")

    # ── 10. PR CELEBRATION ──
    recent_prs = [p for p in prs if p["date"] >= (datetime.now(timezone.utc) - timedelta(days=period)).strftime("%Y-%m-%d")]
    if recent_prs:
        wins.append(f"🏆 {len(recent_prs)} new personal record(s) in the last {period} days! Strength gains precede visible muscle gains by 4-8 weeks.")

    # ── PERFORMANCE SCORE ──
    if score_components:
        weights = {
            "consistency": 0.30,
            "nutrition": 0.25,
            "balance": 0.15,
            "progression": 0.15,
            "weight_progress": 0.10,
            "hydration": 0.05,
        }
        total_weight = sum(weights.get(k, 0.05) for k in score_components)
        score = sum(score_components.get(k, 50) * weights.get(k, 0.05) for k in score_components) / total_weight
        score = max(5, min(99, round(score)))
    else:
        score = 30

    # ── GRADE ──
    if score >= 90: grade = "S"
    elif score >= 80: grade = "A"
    elif score >= 70: grade = "B"
    elif score >= 60: grade = "C"
    elif score >= 45: grade = "D"
    else: grade = "F"

    return {
        "performance_score": score,
        "grade": grade,
        "score_breakdown": score_components,
        "wins": wins,
        "insights": insights,
        "warnings": warnings,
        "stats": {
            "workouts_this_period": workout_count,
            "workouts_per_week": workouts_per_week,
            "total_volume_kg": round(sum(w["total_volume"] for w in workouts), 1),
            "total_sets": sum(w["total_sets"] for w in workouts),
            "unique_exercises": len(exercise_frequency),
            "current_streak": streak,
            "meals_logged": len(set(m["date"] for m in meals)),
            "weight_entries": len(weight_logs),
            "prs_this_period": len(recent_prs) if prs else 0,
            "achievements_unlocked": len(data["achievements"]),
        },
        "muscle_distribution": dict(muscle_sets),
        "top_exercises": exercise_frequency.most_common(5),
    }


# ─────────────────────────────────────────────────────────────────
#  AI WORKOUT GENERATOR — personalized plan based on data
# ─────────────────────────────────────────────────────────────────
WORKOUT_TEMPLATES = {
    "push": {
        "name": "Push Day",
        "focus": ["chest", "shoulders", "triceps"],
        "exercises": [
            {"name": "Barbell Bench Press", "sets": 4, "reps": "8-10", "rest": "90s", "muscle": "chest"},
            {"name": "Incline Dumbbell Press", "sets": 3, "reps": "10-12", "rest": "75s", "muscle": "chest"},
            {"name": "Overhead Press", "sets": 4, "reps": "6-8", "rest": "90s", "muscle": "shoulders"},
            {"name": "Lateral Raise", "sets": 3, "reps": "12-15", "rest": "60s", "muscle": "shoulders"},
            {"name": "Cable Tricep Pushdown", "sets": 3, "reps": "12-15", "rest": "60s", "muscle": "triceps"},
            {"name": "Overhead Tricep Extension", "sets": 3, "reps": "10-12", "rest": "60s", "muscle": "triceps"},
        ]
    },
    "pull": {
        "name": "Pull Day",
        "focus": ["back", "biceps"],
        "exercises": [
            {"name": "Barbell Deadlift", "sets": 4, "reps": "5-6", "rest": "120s", "muscle": "back"},
            {"name": "Pull-Ups / Lat Pulldown", "sets": 4, "reps": "8-10", "rest": "90s", "muscle": "back"},
            {"name": "Seated Cable Row", "sets": 3, "reps": "10-12", "rest": "75s", "muscle": "back"},
            {"name": "Face Pull", "sets": 3, "reps": "15-20", "rest": "60s", "muscle": "shoulders"},
            {"name": "Barbell Curl", "sets": 3, "reps": "10-12", "rest": "60s", "muscle": "biceps"},
            {"name": "Hammer Curl", "sets": 3, "reps": "10-12", "rest": "60s", "muscle": "biceps"},
        ]
    },
    "legs": {
        "name": "Leg Day",
        "focus": ["quads", "hamstrings", "glutes", "calves"],
        "exercises": [
            {"name": "Barbell Squat", "sets": 4, "reps": "6-8", "rest": "120s", "muscle": "quads"},
            {"name": "Romanian Deadlift", "sets": 4, "reps": "8-10", "rest": "90s", "muscle": "hamstrings"},
            {"name": "Leg Press", "sets": 3, "reps": "10-12", "rest": "90s", "muscle": "quads"},
            {"name": "Walking Lunges", "sets": 3, "reps": "12 each", "rest": "75s", "muscle": "glutes"},
            {"name": "Leg Curl", "sets": 3, "reps": "12-15", "rest": "60s", "muscle": "hamstrings"},
            {"name": "Calf Raise", "sets": 4, "reps": "15-20", "rest": "60s", "muscle": "calves"},
        ]
    },
    "upper": {
        "name": "Upper Body",
        "focus": ["chest", "back", "shoulders", "biceps", "triceps"],
        "exercises": [
            {"name": "Barbell Bench Press", "sets": 4, "reps": "6-8", "rest": "90s", "muscle": "chest"},
            {"name": "Barbell Row", "sets": 4, "reps": "8-10", "rest": "90s", "muscle": "back"},
            {"name": "Overhead Press", "sets": 3, "reps": "8-10", "rest": "90s", "muscle": "shoulders"},
            {"name": "Lat Pulldown", "sets": 3, "reps": "10-12", "rest": "75s", "muscle": "back"},
            {"name": "Dumbbell Curl", "sets": 3, "reps": "12", "rest": "60s", "muscle": "biceps"},
            {"name": "Tricep Pushdown", "sets": 3, "reps": "12", "rest": "60s", "muscle": "triceps"},
        ]
    },
    "lower": {
        "name": "Lower Body",
        "focus": ["quads", "hamstrings", "glutes", "calves"],
        "exercises": [
            {"name": "Barbell Squat", "sets": 4, "reps": "6-8", "rest": "120s", "muscle": "quads"},
            {"name": "Romanian Deadlift", "sets": 4, "reps": "8-10", "rest": "90s", "muscle": "hamstrings"},
            {"name": "Bulgarian Split Squat", "sets": 3, "reps": "10 each", "rest": "75s", "muscle": "glutes"},
            {"name": "Leg Extension", "sets": 3, "reps": "12-15", "rest": "60s", "muscle": "quads"},
            {"name": "Leg Curl", "sets": 3, "reps": "12-15", "rest": "60s", "muscle": "hamstrings"},
            {"name": "Standing Calf Raise", "sets": 4, "reps": "15-20", "rest": "60s", "muscle": "calves"},
        ]
    },
    "full_body": {
        "name": "Full Body",
        "focus": ["quads", "chest", "back", "shoulders", "core"],
        "exercises": [
            {"name": "Barbell Squat", "sets": 3, "reps": "8-10", "rest": "120s", "muscle": "quads"},
            {"name": "Barbell Bench Press", "sets": 3, "reps": "8-10", "rest": "90s", "muscle": "chest"},
            {"name": "Barbell Row", "sets": 3, "reps": "8-10", "rest": "90s", "muscle": "back"},
            {"name": "Overhead Press", "sets": 3, "reps": "8-10", "rest": "90s", "muscle": "shoulders"},
            {"name": "Romanian Deadlift", "sets": 3, "reps": "10-12", "rest": "90s", "muscle": "hamstrings"},
            {"name": "Plank", "sets": 3, "reps": "45-60s", "rest": "60s", "muscle": "core"},
        ]
    },
}

SPLIT_PLANS = {
    "beginner": {
        "name": "Full Body 3x/Week",
        "description": "Perfect for beginners. Hit every muscle group 3x per week for maximum neuromuscular adaptation.",
        "days": ["full_body", "rest", "full_body", "rest", "full_body", "rest", "rest"],
        "frequency": 3,
    },
    "intermediate_ul": {
        "name": "Upper/Lower 4x/Week",
        "description": "Great balance of frequency and recovery. Each muscle hit 2x/week.",
        "days": ["upper", "lower", "rest", "upper", "lower", "rest", "rest"],
        "frequency": 4,
    },
    "intermediate_ppl": {
        "name": "Push/Pull/Legs 3x/Week",
        "description": "Classic bodybuilding split. Covers all muscle groups with focused sessions.",
        "days": ["push", "pull", "legs", "rest", "rest", "rest", "rest"],
        "frequency": 3,
    },
    "advanced_ppl": {
        "name": "Push/Pull/Legs 6x/Week",
        "description": "High frequency split for advanced lifters. Each muscle trained 2x/week.",
        "days": ["push", "pull", "legs", "push", "pull", "legs", "rest"],
        "frequency": 6,
    },
}


def _generate_workout_plan(data: dict) -> dict:
    """Generate a personalized workout plan based on user data."""
    profile = data["user_profile"]
    workouts = data["workouts"]
    muscle_dist = defaultdict(int)
    exercise_freq = Counter()

    for w in workouts:
        for ex in w["exercises"]:
            exercise_freq[ex["name"]] += 1
            for mg in ex["muscle_groups"]:
                muscle_dist[mg] += 1

    total_workouts = data["total_workouts_all_time"]
    workouts_per_week = len(workouts) / max(data["period_days"] / 7, 1)

    # ── Choose split based on experience ──
    if total_workouts < 20 or workouts_per_week < 3:
        split_key = "beginner"
    elif workouts_per_week < 4:
        split_key = "intermediate_ppl"
    elif workouts_per_week < 5:
        split_key = "intermediate_ul"
    else:
        split_key = "advanced_ppl"

    split = SPLIT_PLANS[split_key]

    # ── Find weak/neglected muscle groups ──
    major_muscles = {"chest", "back", "shoulders", "quads", "hamstrings", "glutes"}
    trained = {m: muscle_dist.get(m, 0) for m in major_muscles}
    avg_train = sum(trained.values()) / max(len(trained), 1) if trained else 0
    weak_muscles = [m for m, c in trained.items() if c < avg_train * 0.5]

    # ── Build the plan ──
    today_name = datetime.now(timezone.utc).strftime("%A")
    day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    schedule = []
    for i, day_type in enumerate(split["days"]):
        if day_type == "rest":
            schedule.append({
                "day": day_names[i],
                "type": "rest",
                "name": "Rest & Recovery",
                "exercises": [],
                "notes": "Active recovery: light walking, stretching, foam rolling. Muscles grow during rest!",
            })
        else:
            template = WORKOUT_TEMPLATES[day_type]
            exercises = []
            for ex in template["exercises"]:
                # Adjust reps/sets based on goal
                sets = ex["sets"]
                reps = ex["reps"]
                if profile.get("goal") == "lose_weight":
                    reps = ex["reps"].replace("6-8", "10-12").replace("5-6", "8-10") if isinstance(ex["reps"], str) else str(ex["reps"])
                elif profile.get("goal") == "gain_muscle":
                    sets = min(ex["sets"] + 1, 5)

                exercises.append({
                    "name": ex["name"],
                    "sets": sets,
                    "reps": reps,
                    "rest": ex["rest"],
                    "muscle": ex["muscle"],
                })

            schedule.append({
                "day": day_names[i],
                "type": day_type,
                "name": template["name"],
                "exercises": exercises,
                "notes": f"Focus: {', '.join(template['focus'])}",
            })

    # ── Coaching notes ──
    coaching_notes = []
    if weak_muscles:
        coaching_notes.append(f"🎯 Priority muscles to strengthen: {', '.join(weak_muscles)}. Add extra sets for these.")
    if profile.get("goal") == "lose_weight":
        coaching_notes.append("🔥 Add 20-30 min Zone 2 cardio (walking, cycling) after lifting sessions for extra fat burn.")
        coaching_notes.append("🥩 Keep protein at 1.6-2.2g/kg body weight to preserve muscle during your cut.")
    elif profile.get("goal") == "gain_muscle":
        coaching_notes.append("🍗 Eat 200-350 kcal surplus with 1.6-2.2g/kg protein for optimal muscle growth.")
        coaching_notes.append("😴 Sleep 7-9 hours. Growth hormone peaks during deep sleep stages 3-4.")

    coaching_notes.append("📈 Progressive overload: increase weight by 2.5-5% when you complete all prescribed reps for 2 consecutive sessions.")
    coaching_notes.append("🔄 Follow this plan for 4-6 weeks, then deload (reduce volume by 40-60%) for 1 week.")

    return {
        "split_name": split["name"],
        "split_description": split["description"],
        "frequency": f"{split['frequency']}x per week",
        "experience_level": split_key.split("_")[0].title(),
        "goal_optimization": profile.get("goal", "maintain").replace("_", " ").title(),
        "schedule": schedule,
        "weak_muscles": weak_muscles,
        "coaching_notes": coaching_notes,
    }


# ─────────────────────────────────────────────────────────────────
#  GEMINI AI ENHANCEMENT — when API key is available
# ─────────────────────────────────────────────────────────────────
async def _ai_enhanced_analysis(data: dict, rule_analysis: dict) -> dict:
    """Enhance the rule-based analysis with Gemini AI natural language."""
    try:
        import asyncio
        from google import genai
        client = genai.Client(api_key=settings.GEMINI_API_KEY)
        model_name = "gemini-2.0-flash"

        profile = data["user_profile"]
        stats = rule_analysis["stats"]
        prompt = f"""You are an expert AI fitness coach analyzing a real user's data. Be specific, motivating, and data-driven.

USER PROFILE:
- {profile['username']}, {profile.get('age', '?')}y {profile.get('gender', '?')}, {profile.get('weight_kg', '?')}kg, {profile.get('height_cm', '?')}cm
- Goal: {profile.get('goal', 'maintain')}, Target: {profile.get('target_weight_kg', 'not set')}kg
- Activity: {profile.get('activity_level', '?')}

LAST {data['period_days']} DAYS DATA:
- Workouts: {stats['workouts_this_period']} ({stats['workouts_per_week']}/week)
- Volume: {stats['total_volume_kg']}kg total, {stats['total_sets']} sets
- Exercises: {stats['unique_exercises']} different
- Streak: {stats['current_streak']} days
- Meals logged: {stats['meals_logged']} days
- PRs: {stats['prs_this_period']} new records
- Muscle distribution: {dict(rule_analysis.get('muscle_distribution', {}))}

EXISTING ANALYSIS (rule-based):
Wins: {rule_analysis['wins']}
Insights: {rule_analysis['insights']}
Warnings: {rule_analysis['warnings']}
Score: {rule_analysis['performance_score']}/100 (Grade: {rule_analysis['grade']})

Generate a short, personalized coaching summary (3-4 sentences) that:
1. Acknowledges their effort with specific data points
2. Identifies the ONE most impactful thing they should change
3. Gives a concrete, actionable next step
4. Ends with genuine motivation

Also provide ONE bonus tip that's creative and specific to their situation.

Respond ONLY with valid JSON:
{{"summary": "...", "bonus_tip": "..."}}"""

        response = await asyncio.wait_for(
            asyncio.to_thread(
                client.models.generate_content,
                model=model_name, contents=prompt
            ),
            timeout=10,
        )
        text = response.text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1].rsplit("```", 1)[0]
        ai_data = json.loads(text)

        rule_analysis["ai_summary"] = ai_data.get("summary", "")
        rule_analysis["ai_bonus_tip"] = ai_data.get("bonus_tip", "")
        rule_analysis["ai_enhanced"] = True

    except asyncio.TimeoutError:
        print("⚠️ AI enhancement timed out after 10s — using rule-based")
        rule_analysis["ai_enhanced"] = False
    except Exception as e:
        print(f"⚠️ AI enhancement failed: {e}")
        rule_analysis["ai_enhanced"] = False

    return rule_analysis


async def _ai_generate_workout(data: dict) -> dict | None:
    """Try to generate a workout plan via Gemini AI."""
    try:
        import asyncio
        from google import genai
        client = genai.Client(api_key=settings.GEMINI_API_KEY)
        model_name = "gemini-2.0-flash"

        profile = data["user_profile"]
        muscle_dist = defaultdict(int)
        for w in data["workouts"]:
            for ex in w["exercises"]:
                for mg in ex["muscle_groups"]:
                    muscle_dist[mg] += 1

        prompt = f"""Generate a personalized 1-day workout plan for:
- {profile.get('age', 25)}y {profile.get('gender', 'male')}, {profile.get('weight_kg', 75)}kg
- Goal: {profile.get('goal', 'maintain')}
- Recent muscle distribution (sets): {dict(muscle_dist)}
- Focus on WEAKEST muscle groups to balance training

Return ONLY valid JSON:
{{"workout_name": "...", "focus": ["muscle1", "muscle2"], "exercises": [{{"name": "Exercise Name", "sets": 4, "reps": "8-10", "rest": "90s", "muscle": "chest", "tip": "Brief form cue"}}], "warmup": "5 min description", "cooldown": "5 min description"}}"""

        response = await asyncio.wait_for(
            asyncio.to_thread(
                client.models.generate_content,
                model=model_name, contents=prompt
            ),
            timeout=10,
        )
        text = response.text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1].rsplit("```", 1)[0]
        return json.loads(text)

    except asyncio.TimeoutError:
        print("⚠️ AI workout generation timed out after 10s — using rule-based")
        return None
    except Exception as e:
        print(f"⚠️ AI workout generation failed: {e}")
        return None


# ─────────────────────────────────────────────────────────────────
#  PUBLIC API — called by route handlers
# ─────────────────────────────────────────────────────────────────
async def get_smart_analysis(user: dict, days: int = 30) -> dict:
    """Main entry point: collect data → analyze → optionally enhance with AI."""
    data = await _collect_user_data(user, days)
    analysis = _analyze_data(data)

    # Generate motivational headline
    score = analysis["performance_score"]
    name = data["user_profile"]["username"]
    if score >= 90:
        analysis["headline"] = f"🏆 {name}, you're absolutely CRUSHING it!"
        analysis["headline_sub"] = "Top-tier performance. You're in the elite zone."
    elif score >= 75:
        analysis["headline"] = f"💪 Great work, {name}! You're building something real."
        analysis["headline_sub"] = "Solid performance with room to push even harder."
    elif score >= 60:
        analysis["headline"] = f"📈 Good progress, {name}. Let's level up!"
        analysis["headline_sub"] = "You've got the foundation. Now let's optimize."
    elif score >= 40:
        analysis["headline"] = f"🔧 {name}, let's tune up your game plan."
        analysis["headline_sub"] = "Some key areas need attention to unlock real progress."
    else:
        analysis["headline"] = f"🚀 {name}, your comeback starts NOW."
        analysis["headline_sub"] = "Every champion was once a beginner. Let's build your foundation."

    # Try AI enhancement
    if settings.GEMINI_API_KEY:
        analysis = await _ai_enhanced_analysis(data, analysis)
    else:
        analysis["ai_enhanced"] = False

    analysis["period_days"] = data["period_days"]
    return analysis


async def get_generated_workout(user: dict) -> dict:
    """Generate a personalized workout plan."""
    data = await _collect_user_data(user, days=30)

    # Try AI first
    if settings.GEMINI_API_KEY:
        ai_workout = await _ai_generate_workout(data)
        if ai_workout:
            ai_workout["source"] = "ai"
            return ai_workout

    # Fall back to rule-based plan
    plan = _generate_workout_plan(data)
    plan["source"] = "algorithm"
    return plan

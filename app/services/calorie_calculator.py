"""Calorie & macro calculator — formula-based system.

═══════════════════════════════════════════════════════════════════
Sources
═══════════════════════════════════════════════════════════════════
 • BMR — Mifflin-St Jeor equation (Mifflin MD et al., Am J Clin Nutr
   1990;51:241-7). Gold-standard for resting metabolic rate.
 • Activity multipliers — Harris-Benedict activity factors, widely used
   in sports-nutrition practice.
 • Fat-loss rule — 7 700 kcal ≈ 1 kg body fat (Wishnofsky, Am J Clin
   Nutr 1958). Still the standard clinical heuristic.
 • Macro ranges — ISSN position stand (Jäger et al., J Int Soc Sports
   Nutr 2017) & ACSM/AND/DC joint position (Med Sci Sports Exerc 2016).

═══════════════════════════════════════════════════════════════════
How it works
═══════════════════════════════════════════════════════════════════
1. Maintenance = BMR × activity_multiplier
2. Goal calories = Maintenance × deficit_multiplier
     • Small deficit   = 10 %  →  × 0.90
     • Moderate deficit = 20 %  →  × 0.80
     • Aggressive deficit = 30 %  →  × 0.70
     • Muscle gain       = +10 % surplus → × 1.10
3. Weight-change prediction
     • daily_deficit = maintenance − goal_calories
     • weekly_deficit = daily_deficit × 7
     • weekly_weight_change = weekly_deficit / 7700   (kg)
     • monthly_weight_change = weekly × 4.3
4. Macros (g per kg body-weight)
     • Protein : 1.8 – 2.2 g/kg  (goal-dependent)
     • Fat     : 0.6 – 1.0 g/kg  (goal-dependent)
     • Carbs   : remaining calories ÷ 4
"""

from typing import Optional


# ── Activity multipliers ─────────────────────────────────────────────────────
ACTIVITY_MULTIPLIERS = {
    "sedentary":          1.2,    # Desk job, little/no exercise
    "lightly_active":     1.375,  # Light exercise 1-3 days/wk
    "moderately_active":  1.55,   # Moderate exercise 3-5 days/wk
    "very_active":        1.725,  # Hard exercise 6-7 days/wk
    "extremely_active":   1.9,    # Athlete / 2× per day training
}

# ── Deficit / surplus multipliers per goal ────────────────────────────────────
# lose_weight  → moderate 20 % deficit (safe, sustainable ~0.5-1 kg/wk)
# gain_muscle  → 10 % surplus (lean bulk)
# maintain     → 0 % change
GOAL_CALORIE_MULTIPLIER = {
    "lose_weight":  0.80,   # 20 % deficit
    "gain_muscle":  1.10,   # 10 % surplus
    "maintain":     1.00,   # no change
}

# ── Macro targets (grams per kg body-weight) ─────────────────────────────────
# Protein: 1.8 – 2.2 g/kg
# Fat:     0.6 – 1.0 g/kg
# Carbs:   remaining calories ÷ 4
PROTEIN_G_PER_KG = {
    "lose_weight":  2.2,   # high end — preserve lean mass during deficit
    "gain_muscle":  2.0,   # support hypertrophy
    "maintain":     1.8,   # general fitness
}

FAT_G_PER_KG = {
    "lose_weight":  0.8,   # mid-range, keeps hormones healthy
    "gain_muscle":  1.0,   # higher end, supports testosterone
    "maintain":     0.8,   # balanced
}

# ── 7 700 kcal ≈ 1 kg fat (Wishnofsky's rule) ────────────────────────────────
KCAL_PER_KG_FAT = 7700


# ═════════════════════════════════════════════════════════════════
#  CORE FORMULAS
# ═════════════════════════════════════════════════════════════════

def calculate_bmr(weight_kg: float, height_cm: float, age: int,
                  gender: str) -> float:
    """Mifflin-St Jeor BMR (kcal/day).

    Male:   10 × weight(kg) + 6.25 × height(cm) − 5 × age(y) + 5
    Female: 10 × weight(kg) + 6.25 × height(cm) − 5 × age(y) − 161
    """
    base = (10 * weight_kg) + (6.25 * height_cm) - (5 * age)
    return base + 5 if gender == "male" else base - 161


def calculate_tdee(weight_kg: float, height_cm: float, age: int,
                   gender: str, activity_level: str) -> int:
    """Maintenance calories = BMR × activity multiplier."""
    bmr = calculate_bmr(weight_kg, height_cm, age, gender)
    multiplier = ACTIVITY_MULTIPLIERS.get(activity_level, 1.55)
    return round(bmr * multiplier)


def calculate_target_calories(user: dict) -> int:
    """Goal calories = maintenance × deficit/surplus multiplier.

    Never goes below 1 200 kcal (safety floor).
    """
    if not user.get("weight_kg") or not user.get("height_cm") or not user.get("age"):
        return 2000  # sensible fallback for incomplete profiles

    tdee = calculate_tdee(
        weight_kg=user["weight_kg"],
        height_cm=user["height_cm"],
        age=user["age"],
        gender=user.get("gender", "male"),
        activity_level=user.get("activity_level", "moderately_active"),
    )
    goal = user.get("goal", "maintain")
    multiplier = GOAL_CALORIE_MULTIPLIER.get(goal, 1.0)
    return max(1200, round(tdee * multiplier))


# ═════════════════════════════════════════════════════════════════
#  MACRO CALCULATOR
# ═════════════════════════════════════════════════════════════════

def _calculate_macros(weight_kg: float, target_calories: int,
                      goal: str) -> dict:
    """Calculate macro grams using g-per-kg rules, carbs = remainder.

    Protein : 1.8 – 2.2 g/kg  (goal-dependent)
    Fat     : 0.6 – 1.0 g/kg  (goal-dependent)
    Carbs   : (target_calories − protein_cal − fat_cal) / 4
    """
    # Step 1 — Protein
    protein_g = round(weight_kg * PROTEIN_G_PER_KG.get(goal, 1.8), 1)

    # Step 2 — Fat
    fat_g = round(weight_kg * FAT_G_PER_KG.get(goal, 0.8), 1)

    # Step 3 — Carbs from remaining calories
    protein_cal = protein_g * 4
    fat_cal = fat_g * 9
    remaining_cal = max(0, target_calories - protein_cal - fat_cal)
    carbs_g = round(remaining_cal / 4, 1)

    # Derive real percentages
    total_cal = protein_cal + (carbs_g * 4) + fat_cal
    if total_cal == 0:
        total_cal = 1

    return {
        "protein_g":   protein_g,
        "carbs_g":     carbs_g,
        "fat_g":       fat_g,
        "protein_pct": round(protein_cal / total_cal * 100),
        "carbs_pct":   round((carbs_g * 4) / total_cal * 100),
        "fat_pct":     round(fat_cal / total_cal * 100),
    }


# ═════════════════════════════════════════════════════════════════
#  WEIGHT-CHANGE PREDICTION  (7 700 kcal ≈ 1 kg)
# ═════════════════════════════════════════════════════════════════

def _predict_weight_change(tdee: int, target_calories: int) -> dict:
    """Predict weight change using the 7 700 kcal/kg rule.

    Returns positive values for loss, context-labelled for gain.
    """
    daily_deficit = tdee - target_calories          # +ve = deficit, -ve = surplus
    weekly_deficit = daily_deficit * 7
    weekly_change = round(abs(weekly_deficit) / KCAL_PER_KG_FAT, 2)
    monthly_change = round(weekly_change * 4.3, 2)

    direction = "loss" if daily_deficit > 0 else "gain" if daily_deficit < 0 else "none"
    deficit_pct = round(abs(daily_deficit) / tdee * 100, 1) if tdee else 0

    return {
        "daily_deficit":           abs(daily_deficit),
        "weekly_calorie_deficit":  abs(weekly_deficit),
        "weekly_weight_change_kg": weekly_change,
        "monthly_weight_change_kg": monthly_change,
        "deficit_pct":             deficit_pct,
        "direction":               direction,    # "loss" | "gain" | "none"
    }


def estimate_timeline(
    current_weight: float,
    target_weight: Optional[float],
    goal: str,
    weekly_change_kg: float = 0,
) -> Optional[dict]:
    """Estimate weeks to reach *target_weight*."""
    if not target_weight or goal == "maintain":
        return None

    diff = abs(current_weight - target_weight)
    if diff < 0.5:
        return {
            "weight_diff_kg": 0,
            "estimated_weeks": 0,
            "estimated_months": 0,
            "rate_per_week_kg": 0,
            "current_weight": current_weight,
            "target_weight": target_weight,
            "message": "You're already at your target! 🎉",
        }

    rate = weekly_change_kg if weekly_change_kg > 0 else 0.5
    weeks = round(diff / rate)
    months = round(weeks / 4.3, 1)

    return {
        "weight_diff_kg":   round(diff, 1),
        "estimated_weeks":  weeks,
        "estimated_months": months,
        "rate_per_week_kg": round(rate, 2),
        "current_weight":   current_weight,
        "target_weight":    target_weight,
        "message": f"Estimated {months} months ({weeks} weeks) to reach {target_weight} kg",
    }


# ═════════════════════════════════════════════════════════════════
#  PUBLIC API — get_full_nutrition_plan()
# ═════════════════════════════════════════════════════════════════

def get_full_nutrition_plan(user: dict) -> dict:
    """Generate a complete nutrition plan for a user.

    Returns a flat dict with:
      • BMR, TDEE (maintenance), goal calories
      • Deficit info (% deficit, daily/weekly deficit)
      • Weight-change prediction (weekly & monthly)
      • Macro targets in grams + percentages
      • Optional timeline to reach target weight
    """
    weight   = user.get("weight_kg")
    height   = user.get("height_cm")
    age      = user.get("age")
    gender   = user.get("gender", "male")
    activity = user.get("activity_level", "moderately_active")
    goal     = user.get("goal", "maintain")

    # Guard against incomplete profiles
    if not weight or not height or not age:
        return {
            "bmr": 0, "tdee": 2000, "target_calories": 2000, "goal": goal,
            "macros": {"protein_g": 0, "carbs_g": 0, "fat_g": 0},
            "protein_g": 0, "carbs_g": 0, "fat_g": 0,
            "protein_pct": 0, "carbs_pct": 0, "fat_pct": 0,
            "deficit_pct": 0, "daily_deficit": 0,
            "weekly_calorie_deficit": 0,
            "weekly_weight_change_kg": 0, "monthly_weight_change_kg": 0,
            "direction": "none",
            "timeline": None,
        }

    # 1️⃣  BMR & Maintenance (TDEE)
    bmr    = calculate_bmr(weight, height, age, gender)
    tdee   = calculate_tdee(weight, height, age, gender, activity)

    # 2️⃣  Goal Calories
    target = calculate_target_calories(user)

    # 3️⃣  Weight-Change Prediction
    prediction = _predict_weight_change(tdee, target)

    # 4️⃣  Macros
    macros = _calculate_macros(weight, target, goal)

    # 5️⃣  Timeline (if target weight set)
    timeline = estimate_timeline(
        weight,
        user.get("target_weight_kg"),
        goal,
        weekly_change_kg=prediction["weekly_weight_change_kg"],
    )

    return {
        "bmr":              round(bmr, 1),
        "tdee":             tdee,
        "target_calories":  target,
        "goal":             goal,

        # Deficit / surplus info
        "deficit_pct":              prediction["deficit_pct"],
        "daily_deficit":            prediction["daily_deficit"],
        "weekly_calorie_deficit":   prediction["weekly_calorie_deficit"],
        "weekly_weight_change_kg":  prediction["weekly_weight_change_kg"],
        "monthly_weight_change_kg": prediction["monthly_weight_change_kg"],
        "direction":                prediction["direction"],

        # Macros — nested (backward compat for goal generation)
        "macros": {
            "protein_g": macros["protein_g"],
            "carbs_g":   macros["carbs_g"],
            "fat_g":     macros["fat_g"],
        },
        # Macros — flat (for frontend)
        "protein_g":   macros["protein_g"],
        "carbs_g":     macros["carbs_g"],
        "fat_g":       macros["fat_g"],
        "protein_pct": macros["protein_pct"],
        "carbs_pct":   macros["carbs_pct"],
        "fat_pct":     macros["fat_pct"],

        # Timeline
        "timeline": timeline,
    }

"""
Rank System — Progressive challenges based on real exercises and total volume.

Each rank has a set of challenges the user must complete to rank up.
Challenges are tracked from workout history (total reps of bodyweight moves,
max weight on compound lifts, total volume milestones, consistency streaks).
"""

from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends

from app.database import get_db
from app.utils.security import get_current_user

router = APIRouter(prefix="/api/rank", tags=["Rank System"])

# ═══════════════════════════════════════════════════════════════════
#  RANK DEFINITIONS
#  Each rank has: name, emoji, color, min_order, challenges[]
#  challenge types:
#    total_volume_kg   — cumulative weight lifted all time
#    exercise_reps     — total reps of a specific exercise all time
#    max_weight_kg     — heaviest single-set weight on a specific exercise
#    workout_count     — total number of workouts logged
#    streak            — current consistency streak (days)
# ═══════════════════════════════════════════════════════════════════

RANKS = [
    {
        "order": 0,
        "name": "Rookie",
        "emoji": "🥉",
        "color": "#8B7355",
        "challenges": [
            {"type": "workout_count",  "target": 3,     "label": "Log 3 workouts"},
            {"type": "total_volume_kg","target": 500,    "label": "Lift 500 kg total volume"},
            {"type": "exercise_reps",  "exercise": "push-up", "target": 50, "label": "Do 50 push-ups total"},
        ],
    },
    {
        "order": 1,
        "name": "Bronze",
        "emoji": "🥉",
        "color": "#CD7F32",
        "challenges": [
            {"type": "workout_count",  "target": 10,    "label": "Log 10 workouts"},
            {"type": "total_volume_kg","target": 2500,   "label": "Lift 2,500 kg total volume"},
            {"type": "exercise_reps",  "exercise": "push-up", "target": 200, "label": "Do 200 push-ups total"},
            {"type": "exercise_reps",  "exercise": "leg raise", "target": 100, "label": "Do 100 leg raises total"},
        ],
    },
    {
        "order": 2,
        "name": "Silver",
        "emoji": "🥈",
        "color": "#C0C0C0",
        "challenges": [
            {"type": "workout_count",  "target": 30,    "label": "Log 30 workouts"},
            {"type": "total_volume_kg","target": 10000,  "label": "Lift 10,000 kg total volume"},
            {"type": "exercise_reps",  "exercise": "push-up", "target": 500, "label": "Do 500 push-ups total"},
            {"type": "exercise_reps",  "exercise": "squat",   "target": 300, "label": "Do 300 squats total"},
            {"type": "max_weight_kg",  "exercise": "bench press", "target": 60, "label": "Bench press 60 kg"},
        ],
    },
    {
        "order": 3,
        "name": "Gold",
        "emoji": "🥇",
        "color": "#FFD700",
        "challenges": [
            {"type": "workout_count",  "target": 75,     "label": "Log 75 workouts"},
            {"type": "total_volume_kg","target": 50000,   "label": "Lift 50,000 kg total volume"},
            {"type": "exercise_reps",  "exercise": "push-up", "target": 1000, "label": "Do 1,000 push-ups total"},
            {"type": "exercise_reps",  "exercise": "pull-up",  "target": 200, "label": "Do 200 pull-ups total"},
            {"type": "max_weight_kg",  "exercise": "bench press", "target": 80,  "label": "Bench press 80 kg"},
            {"type": "max_weight_kg",  "exercise": "squat",       "target": 100, "label": "Squat 100 kg"},
            {"type": "streak",         "target": 7,       "label": "Hit a 7-day streak"},
        ],
    },
    {
        "order": 4,
        "name": "Platinum",
        "emoji": "💎",
        "color": "#E5E4E2",
        "challenges": [
            {"type": "workout_count",  "target": 150,    "label": "Log 150 workouts"},
            {"type": "total_volume_kg","target": 150000,  "label": "Lift 150,000 kg total volume"},
            {"type": "exercise_reps",  "exercise": "push-up",  "target": 2500, "label": "Do 2,500 push-ups total"},
            {"type": "exercise_reps",  "exercise": "pull-up",  "target": 500,  "label": "Do 500 pull-ups total"},
            {"type": "exercise_reps",  "exercise": "leg raise","target": 500,  "label": "Do 500 leg raises total"},
            {"type": "max_weight_kg",  "exercise": "bench press",  "target": 100, "label": "Bench press 100 kg"},
            {"type": "max_weight_kg",  "exercise": "deadlift",     "target": 140, "label": "Deadlift 140 kg"},
            {"type": "max_weight_kg",  "exercise": "squat",        "target": 120, "label": "Squat 120 kg"},
            {"type": "streak",         "target": 14,      "label": "Hit a 14-day streak"},
        ],
    },
    {
        "order": 5,
        "name": "Diamond",
        "emoji": "💠",
        "color": "#B9F2FF",
        "challenges": [
            {"type": "workout_count",  "target": 300,     "label": "Log 300 workouts"},
            {"type": "total_volume_kg","target": 500000,   "label": "Lift 500,000 kg total volume"},
            {"type": "exercise_reps",  "exercise": "push-up",  "target": 5000, "label": "Do 5,000 push-ups total"},
            {"type": "exercise_reps",  "exercise": "pull-up",  "target": 1000, "label": "Do 1,000 pull-ups total"},
            {"type": "exercise_reps",  "exercise": "burpee",   "target": 500,  "label": "Do 500 burpees total"},
            {"type": "max_weight_kg",  "exercise": "bench press",  "target": 120, "label": "Bench press 120 kg"},
            {"type": "max_weight_kg",  "exercise": "deadlift",     "target": 200, "label": "Deadlift 200 kg"},
            {"type": "max_weight_kg",  "exercise": "squat",        "target": 160, "label": "Squat 160 kg"},
            {"type": "streak",         "target": 30,       "label": "Hit a 30-day streak"},
        ],
    },
    {
        "order": 6,
        "name": "Legend",
        "emoji": "👑",
        "color": "#FF4500",
        "challenges": [
            {"type": "workout_count",  "target": 500,      "label": "Log 500 workouts"},
            {"type": "total_volume_kg","target": 1000000,   "label": "Lift 1,000,000 kg total volume"},
            {"type": "exercise_reps",  "exercise": "push-up",    "target": 10000, "label": "Do 10,000 push-ups total"},
            {"type": "exercise_reps",  "exercise": "pull-up",    "target": 2500,  "label": "Do 2,500 pull-ups total"},
            {"type": "exercise_reps",  "exercise": "muscle-up",  "target": 100,   "label": "Do 100 muscle-ups total"},
            {"type": "max_weight_kg",  "exercise": "bench press",  "target": 140, "label": "Bench press 140 kg"},
            {"type": "max_weight_kg",  "exercise": "deadlift",     "target": 250, "label": "Deadlift 250 kg"},
            {"type": "max_weight_kg",  "exercise": "squat",        "target": 200, "label": "Squat 200 kg"},
            {"type": "streak",         "target": 60,        "label": "Hit a 60-day streak"},
        ],
    },
]


def _normalize(name: str) -> str:
    """Lowercase + strip for fuzzy matching exercise names."""
    return name.strip().lower()


async def _compute_user_metrics(db, user_id: str):
    """
    Aggregate all relevant metrics from user's workout history.
    Returns dict with:
      workout_count, total_volume_kg, current_streak,
      exercise_total_reps {name: reps}, exercise_max_weight {name: kg}
    """
    # Total workouts
    workout_count = await db.workouts.count_documents({"user_id": user_id})

    # Total volume + per-exercise reps & max weight
    total_volume = 0.0
    exercise_reps: dict[str, int] = {}
    exercise_max: dict[str, float] = {}

    cursor = db.workouts.find({"user_id": user_id})
    dates_set = set()

    async for w in cursor:
        d = w.get("date")
        if d:
            dates_set.add(d.strftime("%Y-%m-%d") if hasattr(d, "strftime") else str(d)[:10])

        for ex in w.get("exercises", []):
            ex_name = _normalize(ex.get("exercise_name", ""))
            for s in ex.get("sets", []):
                reps = s.get("reps", 0)
                weight = s.get("weight", 0)
                total_volume += reps * weight
                # Count reps (for bodyweight moves — count even if weight=0)
                exercise_reps[ex_name] = exercise_reps.get(ex_name, 0) + reps
                # Track max weight
                if weight > exercise_max.get(ex_name, 0):
                    exercise_max[ex_name] = weight

    # Current streak
    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    sorted_dates = sorted(dates_set, reverse=True)
    streak = 0
    check = datetime.now(timezone.utc).date()
    for ds in sorted_dates:
        from datetime import date as _date
        d = _date.fromisoformat(ds)
        if d == check or d == check - timedelta(days=1):
            streak += 1
            check = d - timedelta(days=1)
        else:
            break

    return {
        "workout_count": workout_count,
        "total_volume_kg": total_volume,
        "current_streak": streak,
        "exercise_reps": exercise_reps,
        "exercise_max": exercise_max,
    }


def _evaluate_challenge(challenge: dict, metrics: dict) -> dict:
    """Evaluate a single challenge against user metrics. Returns dict with progress info."""
    ctype = challenge["type"]
    target = challenge["target"]
    label = challenge["label"]
    current = 0

    if ctype == "workout_count":
        current = metrics["workout_count"]
    elif ctype == "total_volume_kg":
        current = metrics["total_volume_kg"]
    elif ctype == "streak":
        current = metrics["current_streak"]
    elif ctype == "exercise_reps":
        ex = _normalize(challenge["exercise"])
        # Fuzzy match — check if any exercise name contains the key
        for name, reps in metrics["exercise_reps"].items():
            if ex in name or name in ex:
                current = max(current, reps)
    elif ctype == "max_weight_kg":
        ex = _normalize(challenge["exercise"])
        for name, wt in metrics["exercise_max"].items():
            if ex in name or name in ex:
                current = max(current, wt)

    completed = current >= target
    pct = min(current / target * 100, 100) if target > 0 else 100

    return {
        "label": label,
        "target": target,
        "current": round(current, 1) if isinstance(current, float) else current,
        "completed": completed,
        "pct": round(pct, 1),
    }


# ═══════════════════════════════════════════════════════════════════
#  GET /api/rank — current rank, progress, challenges
# ═══════════════════════════════════════════════════════════════════
@router.get("/")
async def get_rank(current_user: dict = Depends(get_current_user)):
    db = get_db()
    metrics = await _compute_user_metrics(db, current_user["id"])

    # Determine current rank — highest rank where ALL challenges are completed
    current_rank_idx = -1  # no rank yet (unranked)
    for rank in RANKS:
        all_done = True
        for ch in rank["challenges"]:
            result = _evaluate_challenge(ch, metrics)
            if not result["completed"]:
                all_done = False
                break
        if all_done:
            current_rank_idx = rank["order"]
        else:
            break

    # Build response
    if current_rank_idx >= 0:
        current = RANKS[current_rank_idx]
    else:
        current = None

    # Next rank to work towards
    next_rank_idx = current_rank_idx + 1
    next_rank = None
    next_challenges = []

    if next_rank_idx < len(RANKS):
        nr = RANKS[next_rank_idx]
        next_rank = {
            "name": nr["name"],
            "emoji": nr["emoji"],
            "color": nr["color"],
            "order": nr["order"],
        }
        for ch in nr["challenges"]:
            next_challenges.append(_evaluate_challenge(ch, metrics))

    # Overall progress toward next rank
    if next_challenges:
        completed_count = sum(1 for c in next_challenges if c["completed"])
        total_count = len(next_challenges)
        overall_pct = round(completed_count / total_count * 100, 1)
    else:
        completed_count = 0
        total_count = 0
        overall_pct = 100  # Max rank reached

    # All ranks summary for display
    all_ranks = []
    for r in RANKS:
        all_ranks.append({
            "name": r["name"],
            "emoji": r["emoji"],
            "color": r["color"],
            "order": r["order"],
            "unlocked": r["order"] <= current_rank_idx,
        })

    return {
        "current_rank": {
            "name": current["name"],
            "emoji": current["emoji"],
            "color": current["color"],
            "order": current["order"],
        } if current else None,
        "next_rank": next_rank,
        "next_challenges": next_challenges,
        "completed_count": completed_count,
        "total_count": total_count,
        "overall_pct": overall_pct,
        "all_ranks": all_ranks,
        "metrics_summary": {
            "workouts": metrics["workout_count"],
            "volume_kg": round(metrics["total_volume_kg"], 1),
            "streak": metrics["current_streak"],
        },
    }

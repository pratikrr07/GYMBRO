"""AI service for calorie/macro estimation using Google Gemini (free tier).
Falls back to a rule-based estimator if API key is missing or call fails."""

import json
import hashlib
from datetime import datetime, timezone
from typing import Optional

from app.config import get_settings
from app.database import get_db

settings = get_settings()

# ── Prompt template ────────────────────────────────────────────────
NUTRITION_PROMPT = """You are a nutrition expert. The user describes what they ate. 
Estimate the calories and macronutrients.

User input: "{meal_description}"

Respond ONLY with valid JSON in this exact format (no markdown, no explanation):
{{
  "items": [
    {{
      "name": "food item name",
      "portion": "estimated portion size",
      "calories": 0,
      "protein_g": 0.0,
      "carbs_g": 0.0,
      "fat_g": 0.0
    }}
  ],
  "total_calories": 0,
  "total_protein_g": 0.0,
  "total_carbs_g": 0.0,
  "total_fat_g": 0.0
}}

Be realistic with portions. If the user doesn't specify quantity, assume a normal single serving.
"""


# ── Cache helpers ──────────────────────────────────────────────────
def _hash_query(text: str) -> str:
    """Create a deterministic hash for cache lookup."""
    normalized = text.strip().lower()
    return hashlib.sha256(normalized.encode()).hexdigest()


async def _get_cached(query_hash: str) -> Optional[dict]:
    """Check MongoDB cache for previous AI result."""
    db = get_db()
    cached = await db.ai_cache.find_one({"query_hash": query_hash})
    if cached:
        return cached.get("result")
    return None


async def _set_cache(query_hash: str, result: dict):
    """Store AI result in MongoDB cache (TTL = 24h via index)."""
    db = get_db()
    await db.ai_cache.insert_one({
        "query_hash": query_hash,
        "result": result,
        "created_at": datetime.now(timezone.utc),
    })


# ── Gemini AI call ─────────────────────────────────────────────────
async def _call_gemini(meal_description: str) -> dict:
    """Call Google Gemini API to estimate nutrition."""
    import asyncio
    from google import genai

    client = genai.Client(api_key=settings.GEMINI_API_KEY)
    prompt = NUTRITION_PROMPT.format(meal_description=meal_description)

    response = await asyncio.wait_for(
        asyncio.to_thread(
            client.models.generate_content,
            model="gemini-2.0-flash", contents=prompt
        ),
        timeout=10,
    )

    # Parse response text as JSON
    text = response.text.strip()
    # Remove markdown code fences if present
    if text.startswith("```"):
        text = text.split("\n", 1)[1]
        text = text.rsplit("```", 1)[0]

    return json.loads(text)


# ── Fallback estimator ─────────────────────────────────────────────
COMMON_FOODS = {
    "chicken": {"calories": 239, "protein_g": 27.0, "carbs_g": 0.0, "fat_g": 14.0, "portion": "100g cooked"},
    "chicken breast": {"calories": 165, "protein_g": 31.0, "carbs_g": 0.0, "fat_g": 3.6, "portion": "100g"},
    "rice": {"calories": 206, "protein_g": 4.3, "carbs_g": 45.0, "fat_g": 0.4, "portion": "1 cup cooked"},
    "brown rice": {"calories": 216, "protein_g": 5.0, "carbs_g": 45.0, "fat_g": 1.8, "portion": "1 cup cooked"},
    "yogurt": {"calories": 100, "protein_g": 17.0, "carbs_g": 6.0, "fat_g": 0.7, "portion": "1 cup"},
    "egg": {"calories": 78, "protein_g": 6.0, "carbs_g": 0.6, "fat_g": 5.3, "portion": "1 large"},
    "eggs": {"calories": 156, "protein_g": 12.0, "carbs_g": 1.2, "fat_g": 10.6, "portion": "2 large"},
    "bread": {"calories": 79, "protein_g": 2.7, "carbs_g": 15.0, "fat_g": 1.0, "portion": "1 slice"},
    "banana": {"calories": 105, "protein_g": 1.3, "carbs_g": 27.0, "fat_g": 0.4, "portion": "1 medium"},
    "apple": {"calories": 95, "protein_g": 0.5, "carbs_g": 25.0, "fat_g": 0.3, "portion": "1 medium"},
    "milk": {"calories": 149, "protein_g": 8.0, "carbs_g": 12.0, "fat_g": 8.0, "portion": "1 cup"},
    "oatmeal": {"calories": 154, "protein_g": 5.0, "carbs_g": 27.0, "fat_g": 2.6, "portion": "1 cup cooked"},
    "pasta": {"calories": 220, "protein_g": 8.0, "carbs_g": 43.0, "fat_g": 1.3, "portion": "1 cup cooked"},
    "salmon": {"calories": 208, "protein_g": 20.0, "carbs_g": 0.0, "fat_g": 13.0, "portion": "100g"},
    "beef": {"calories": 250, "protein_g": 26.0, "carbs_g": 0.0, "fat_g": 15.0, "portion": "100g"},
    "broccoli": {"calories": 55, "protein_g": 3.7, "carbs_g": 11.0, "fat_g": 0.6, "portion": "1 cup"},
    "potato": {"calories": 161, "protein_g": 4.3, "carbs_g": 37.0, "fat_g": 0.2, "portion": "1 medium"},
    "sweet potato": {"calories": 103, "protein_g": 2.3, "carbs_g": 24.0, "fat_g": 0.1, "portion": "1 medium"},
    "cheese": {"calories": 113, "protein_g": 7.0, "carbs_g": 0.4, "fat_g": 9.0, "portion": "1 oz"},
    "peanut butter": {"calories": 190, "protein_g": 7.0, "carbs_g": 7.0, "fat_g": 16.0, "portion": "2 tbsp"},
    "almonds": {"calories": 164, "protein_g": 6.0, "carbs_g": 6.0, "fat_g": 14.0, "portion": "1 oz"},
    "avocado": {"calories": 240, "protein_g": 3.0, "carbs_g": 13.0, "fat_g": 22.0, "portion": "1 whole"},
    "toast": {"calories": 79, "protein_g": 2.7, "carbs_g": 15.0, "fat_g": 1.0, "portion": "1 slice"},
    "salad": {"calories": 20, "protein_g": 1.5, "carbs_g": 3.5, "fat_g": 0.2, "portion": "1 cup mixed greens"},
    "pizza": {"calories": 285, "protein_g": 12.0, "carbs_g": 36.0, "fat_g": 10.0, "portion": "1 slice"},
    "burger": {"calories": 354, "protein_g": 20.0, "carbs_g": 29.0, "fat_g": 17.0, "portion": "1 regular"},
    "protein shake": {"calories": 150, "protein_g": 25.0, "carbs_g": 8.0, "fat_g": 2.0, "portion": "1 scoop with water"},
    "whey protein": {"calories": 120, "protein_g": 24.0, "carbs_g": 3.0, "fat_g": 1.5, "portion": "1 scoop"},
    "coffee": {"calories": 5, "protein_g": 0.3, "carbs_g": 0.0, "fat_g": 0.0, "portion": "1 cup black"},
    "orange juice": {"calories": 112, "protein_g": 1.7, "carbs_g": 26.0, "fat_g": 0.5, "portion": "1 cup"},
    "tuna": {"calories": 132, "protein_g": 29.0, "carbs_g": 0.0, "fat_g": 1.0, "portion": "1 can drained"},
    "dal": {"calories": 198, "protein_g": 12.0, "carbs_g": 34.0, "fat_g": 1.0, "portion": "1 cup cooked"},
    "roti": {"calories": 104, "protein_g": 3.0, "carbs_g": 18.0, "fat_g": 3.0, "portion": "1 piece"},
    "paneer": {"calories": 265, "protein_g": 18.0, "carbs_g": 1.2, "fat_g": 21.0, "portion": "100g"},
    "naan": {"calories": 262, "protein_g": 9.0, "carbs_g": 45.0, "fat_g": 5.0, "portion": "1 piece"},
}


def _fallback_estimate(meal_description: str) -> dict:
    """Simple keyword-matching fallback when AI is unavailable."""
    words = meal_description.lower().replace(",", " ").replace("and", " ").split()
    items = []
    matched = set()

    # Try multi-word matches first
    desc_lower = meal_description.lower()
    for food_name, data in sorted(COMMON_FOODS.items(), key=lambda x: -len(x[0])):
        if food_name in desc_lower and food_name not in matched:
            matched.add(food_name)
            items.append({
                "name": food_name,
                "portion": data["portion"],
                "calories": data["calories"],
                "protein_g": data["protein_g"],
                "carbs_g": data["carbs_g"],
                "fat_g": data["fat_g"],
            })

    # Single word matches
    for word in words:
        word = word.strip(".,!?")
        if word in COMMON_FOODS and word not in matched:
            matched.add(word)
            data = COMMON_FOODS[word]
            items.append({
                "name": word,
                "portion": data["portion"],
                "calories": data["calories"],
                "protein_g": data["protein_g"],
                "carbs_g": data["carbs_g"],
                "fat_g": data["fat_g"],
            })

    if not items:
        # Can't estimate — return a rough default
        items.append({
            "name": meal_description,
            "portion": "1 serving (estimated)",
            "calories": 300,
            "protein_g": 15.0,
            "carbs_g": 35.0,
            "fat_g": 10.0,
        })

    return {
        "items": items,
        "total_calories": sum(i["calories"] for i in items),
        "total_protein_g": round(sum(i["protein_g"] for i in items), 1),
        "total_carbs_g": round(sum(i["carbs_g"] for i in items), 1),
        "total_fat_g": round(sum(i["fat_g"] for i in items), 1),
    }


# ── Main public function ──────────────────────────────────────────
async def estimate_nutrition(meal_description: str) -> dict:
    """
    Estimate nutrition for a meal description.
    Uses cache → Gemini AI → fallback estimator.
    Returns dict with items, totals.
    """
    query_hash = _hash_query(meal_description)

    # 1. Check cache
    cached = await _get_cached(query_hash)
    if cached:
        cached["source"] = "cache"
        return cached

    # 2. Try Gemini AI
    if settings.GEMINI_API_KEY:
        try:
            result = await _call_gemini(meal_description)
            result["source"] = "ai"
            await _set_cache(query_hash, result)
            return result
        except Exception as e:
            print(f"⚠️  Gemini AI failed: {e}, using fallback")

    # 3. Fallback
    result = _fallback_estimate(meal_description)
    result["source"] = "fallback"
    await _set_cache(query_hash, result)
    return result

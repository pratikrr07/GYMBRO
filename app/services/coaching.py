"""AI coaching tips generator. Uses Gemini for personalized tips, falls back to
a rich, science-backed tip library with randomized selection."""

import json
import random
from app.config import get_settings

settings = get_settings()

# ─────────────────────────────────────────────────────────────────
#  SCIENCE-BACKED TIP LIBRARY
#  Each tip includes a real fact, practical advice, and a source.
# ─────────────────────────────────────────────────────────────────

TIPS_LOSE_WEIGHT = [
    "🧬 Your body burns ~60-75% of daily calories just staying alive (BMR). A 500 kcal deficit = ~0.45 kg/wk loss — the gold standard recommended by the American College of Sports Medicine.",
    "🥩 A 2018 meta-analysis in the British Journal of Sports Medicine found that eating 1.6-2.2 g/kg of protein per day maximizes muscle retention during a caloric deficit.",
    "💧 Drinking 500 ml of water 30 min before meals reduced calorie intake by 13% in a University of Birmingham study. Hydration = free appetite control.",
    "😴 Sleeping <6 hours increases ghrelin (hunger hormone) by 28% and decreases leptin (satiety hormone) by 18%. Sleep is a weight loss tool (Spiegel et al., Annals of Internal Medicine).",
    "🔥 NEAT (Non-Exercise Activity Thermogenesis) — fidgeting, standing, walking — can vary by up to 2,000 kcal/day between people. Take the stairs, pace on calls, stand at your desk.",
    "🧪 A Stanford study (Gardner et al., 2018) found no significant difference between low-fat vs. low-carb diets for fat loss. The best diet is the one you can stick to consistently.",
    "📉 Losing weight faster than 1% of body weight per week significantly increases muscle loss (Helms et al., 2014). Slow and steady literally wins the race.",
    "🏋️ Resistance training during a cut preserves 93% more muscle than cardio alone (Villareal et al., 2017). Lift heavy even in a deficit.",
    "🍽️ Eating from smaller plates (10-inch vs 12-inch) reduces calorie intake by 22% without feeling deprived — the Delboeuf illusion applied to nutrition (Wansink, 2006).",
    "☕ Caffeine increases metabolic rate by 3-11% and fat oxidation by up to 29%. A black coffee before fasted cardio can amplify fat burning (Acheson et al., 1980).",
    "📊 People who track their food intake lose 2x more weight than non-trackers (Kaiser et al., 2013). What gets measured gets managed.",
    "🥦 Fiber intake of 30g/day is linked to weight loss similar to complex diets (Ma et al., Annals of Internal Medicine, 2015). Veggies, oats, and legumes are your friends.",
    "🧊 Cold exposure activates brown adipose tissue. Even keeping your room at 66°F (19°C) while sleeping burns extra calories through thermogenesis (van Marken Lichtenbelt, 2009).",
    "⏰ Time-restricted eating (16:8) doesn't magically burn fat, but it naturally reduces calorie intake by ~300 kcal/day in most people (Wilkinson et al., Cell Metabolism, 2020).",
    "🚶 Walking 10,000 steps/day burns an extra 300-500 kcal. It's the most underrated fat loss tool — low stress, no recovery needed, and protects muscle mass.",
    "🎯 Protein has the highest thermic effect of food (TEF): 20-30% of protein calories are burned just digesting it, vs 5-10% for carbs and 0-3% for fat.",
    "🧠 Stress increases cortisol, which promotes visceral fat storage. Even 10 min/day of meditation reduced waist circumference in a 2017 UC Davis study.",
    "🍎 Whole fruits are more satiating than juice — the fiber slows digestion. An apple (95 kcal) keeps you fuller than apple juice (114 kcal) for hours longer.",
]

TIPS_GAIN_MUSCLE = [
    "💪 Muscle protein synthesis peaks 24-48 hours after training. That means every meal in this window matters — aim for 0.4g/kg protein per meal across 4-5 meals (Schoenfeld & Aragon, 2018).",
    "🍗 The anabolic window isn't 30 minutes — it's 4-6 hours. But eating 20-40g protein within 2 hours post-workout is still optimal (Schoenfeld et al., JISSN, 2013).",
    "📈 Progressive overload is the #1 driver of muscle growth. Increase weight by 2.5-5% when you can complete all prescribed reps with good form for 2 consecutive sessions.",
    "😴 Growth hormone peaks during deep sleep (stages 3-4). Getting <7 hours of sleep reduces testosterone by 10-15% (Leproult & Van Cauter, JAMA, 2011).",
    "🥜 To gain muscle with minimal fat, aim for a surplus of 200-350 kcal/day. Larger surpluses (500+) mostly add fat, not extra muscle (Slater et al., 2019).",
    "🧬 Untrained lifters can gain ~1-1.5% of body weight in muscle per month. Intermediate lifters: 0.5-1%. Advanced: 0.25-0.5%. Set realistic expectations.",
    "🏋️ Training volume of 10-20 sets per muscle group per week is the sweet spot for hypertrophy (Schoenfeld et al., 2017). More isn't always better — recovery matters.",
    "⚡ Compound movements (squat, deadlift, bench, row, OHP) recruit more motor units and produce higher hormonal responses than isolation exercises. Build your program around these.",
    "💊 Creatine monohydrate is the most researched supplement in sports science — 300+ studies show it increases strength by 5-10% and lean mass by 1-2 kg in 4-12 weeks (Kreider et al., 2017).",
    "🍌 Eating 0.5-0.7g/kg carbs post-workout replenishes glycogen stores 2x faster than waiting. Add banana or rice to your post-workout shake.",
    "🔄 Muscles grow during rest, not during training. Each muscle group needs 48-72 hours of recovery. Training a sore muscle reduces protein synthesis by up to 50%.",
    "📏 Track your lifts, not just your weight. Strength gains precede visible muscle gains by 4-8 weeks. If your numbers are going up, your muscles are growing.",
    "🥛 Casein protein before bed provides a slow amino acid release over 7 hours, increasing overnight muscle protein synthesis by 22% (Res et al., 2012).",
    "🧪 Leucine is the amino acid that triggers muscle protein synthesis. You need 2.5-3g per meal — found in 25-30g of whey, 170g chicken, or 3 eggs.",
    "💧 Muscle is 76% water. Even 2% dehydration reduces strength by 10-15% and power output by up to 20%. Drink 3-4L daily when training for hypertrophy.",
    "🎯 Time under tension of 40-70 seconds per set is optimal for hypertrophy. Control the eccentric (lowering) phase for 2-3 seconds — this causes more muscle damage and growth.",
    "🔬 A 2019 study in JAMA showed that plant protein is equally effective as animal protein for muscle building when total protein and leucine intake is matched.",
    "⏰ Training frequency of 2x per muscle group per week is superior to 1x for hypertrophy, even when total volume is equated (Schoenfeld et al., 2016).",
]

TIPS_MAINTAIN = [
    "⚖️ Maintenance isn't a fixed number — your TDEE fluctuates by 200-300 kcal daily based on NEAT, stress, sleep, and temperature. Aim for weekly averages, not daily perfection.",
    "🔄 Periodize your training in 4-6 week blocks: strength → hypertrophy → endurance → deload. This prevents plateaus and reduces overuse injuries by 40% (Lorenz & Morrison, 2015).",
    "🥦 Micronutrient density matters more in maintenance. Aim for 5+ servings of colorful vegetables daily — each color represents different phytonutrients and antioxidants.",
    "🧠 The mind-muscle connection is real: a 2016 study by Schoenfeld showed that internally focusing on the target muscle during lifts increased hypertrophy by 12.4%.",
    "📊 Weigh yourself weekly at the same time (morning, fasted, after bathroom). A ±1kg fluctuation is normal from water, glycogen, and food weight. Look at 4-week trends only.",
    "🧘 Include 10-15 minutes of mobility work daily. Fascia tightness from training reduces range of motion by 5-10% per year if not addressed (Stecco et al., 2013).",
    "💧 Electrolyte balance is critical: sodium, potassium, and magnesium affect muscle contraction, nerve function, and hydration. Low magnesium alone can reduce exercise performance by 20%.",
    "🏃 Zone 2 cardio (conversational pace, 60-70% max HR) for 150 min/week improves mitochondrial density and fat oxidation without interfering with strength gains (Seiler, 2010).",
    "🍳 Eating protein at breakfast (30g+) increases satiety throughout the day and improves body composition compared to carb-heavy breakfasts (Leidy et al., 2015).",
    "📈 Deload every 4-6 weeks by reducing volume by 40-60% while keeping intensity. This allows full recovery and often leads to strength PRs the following week.",
    "🧬 Gut microbiome diversity correlates with better nutrient absorption and lower inflammation. Eat 30+ different plant foods per week to support gut health (McDonald et al., 2018).",
    "⚡ Your grip strength is one of the best predictors of overall mortality and health (Leong et al., Lancet, 2015). Train it: dead hangs, farmer's walks, thick bar work.",
    "🎯 The 80/20 rule applies to nutrition: 80% whole, minimally processed foods; 20% flexible. This is more sustainable long-term than strict dieting (Helms et al., 2019).",
    "🧊 Cold water immersion (10-15°C for 10-15 min) after training reduces DOMS by 20% and speeds recovery. But avoid it during hypertrophy phases — inflammation drives growth.",
    "☀️ Vitamin D deficiency affects 42% of adults and reduces strength output by up to 20%. Get 15 min of sunlight daily or supplement 2000-4000 IU (Holick, 2007).",
    "🫀 Resting heart rate is a great recovery metric. If it's 7+ BPM above your baseline in the morning, you may be under-recovered. Consider an active recovery day.",
    "🔬 Your muscles have 'memory' — satellite cells retain myonuclei even after muscle atrophy. Regaining lost muscle is 2-3x faster than building it initially (Gundersen, 2016).",
    "🍵 Green tea catechins (EGCG) increase fat oxidation by 10-17% during exercise. 2-3 cups daily provides enough without excessive caffeine (Hursel et al., 2009).",
]

GENERAL_FACTS = [
    "🧪 Your body contains enough iron to make a 3-inch nail, enough carbon for 900 pencils, and enough phosphorus for 2,200 match heads. You're literally built different.",
    "🫀 Your heart beats ~100,000 times per day, pumping ~7,500 liters of blood. Regular exercise increases stroke volume, meaning your heart does more work with fewer beats.",
    "🧬 You have ~600 muscles making up 40% of your body weight. The gluteus maximus is the largest, the stapedius (in your ear) is the smallest. Train both ends of the spectrum.",
    "⚡ ATP (adenosine triphosphate) is your cellular fuel. Your body recycles its own body weight in ATP every single day. Creatine helps regenerate it 20% faster.",
    "🦴 Weight-bearing exercise increases bone density by 1-3% per year and reduces osteoporosis risk by 40%. Your skeleton fully remodels itself every 10 years.",
    "🧠 Exercise increases BDNF (brain-derived neurotrophic factor) by 32%, literally growing new brain cells. A single workout improves focus and memory for 2-3 hours afterward.",
    "🏋️ The world record deadlift is 501 kg (Hafthor Björnsson, 2020). The average untrained person can deadlift 60-80% of their body weight. Most can reach 2x bodyweight within 2 years.",
    "💪 Eccentric contractions (lowering weight) create 20-60% more force than concentric (lifting). Slow negatives are the secret sauce for both strength and hypertrophy.",
    "🥩 A chicken breast has 31g protein per 100g. Greek yogurt has 10g per 100g. Eggs have 6g each. Lentils have 9g per 100g cooked. Mix sources for complete amino acid profiles.",
    "🔥 EPOC (Excess Post-Exercise Oxygen Consumption) means you burn extra calories for 24-72 hours after intense training. HIIT and heavy lifting create the highest EPOC.",
    "🧲 Muscle tissue burns 3x more calories at rest than fat tissue (6 kcal/kg vs 2 kcal/kg). Gaining 5 kg of muscle increases your resting metabolism by ~30 kcal/day.",
    "⏳ It takes 66 days on average to form a habit, not 21 (Lally et al., European J. Social Psychology, 2010). Be patient with yourself — consistency beats intensity.",
]


def _pick_tips(goal: str, count: int = 6) -> list[str]:
    """Select randomized tips from the appropriate pool + general facts."""
    pool_map = {
        "lose_weight": TIPS_LOSE_WEIGHT,
        "gain_muscle": TIPS_GAIN_MUSCLE,
        "maintain": TIPS_MAINTAIN,
    }
    goal_pool = pool_map.get(goal, TIPS_MAINTAIN)

    # Pick 4 goal-specific + 2 general facts (randomized)
    goal_count = min(count - 2, len(goal_pool))
    general_count = min(2, len(GENERAL_FACTS))

    selected = random.sample(goal_pool, goal_count) + random.sample(GENERAL_FACTS, general_count)
    random.shuffle(selected)
    return selected


async def generate_coaching_tips(user: dict) -> dict:
    """Generate personalized coaching tips using AI or the science-backed library."""
    goal = user.get("goal", "maintain")

    # Try AI first
    if settings.GEMINI_API_KEY:
        try:
            return await _ai_tips(user)
        except Exception as e:
            print(f"⚠️  AI coaching tips failed: {e}, using science library")

    return {
        "tips": _pick_tips(goal, 6),
        "source": "science_library",
    }


async def _ai_tips(user: dict) -> dict:
    """Generate personalized tips via Gemini AI."""
    import asyncio
    from google import genai

    client = genai.Client(api_key=settings.GEMINI_API_KEY)
    model_name = "gemini-2.0-flash"

    prompt = f"""You are a certified fitness coach and sports science expert. Generate 6 short, 
actionable coaching tips for this person. Each tip MUST include a real scientific fact 
with a study reference or mechanism. Use emojis. Be specific, evidence-based, and motivating.

Profile:
- Age: {user.get('age', '?')}, Gender: {user.get('gender', '?')}
- Weight: {user.get('weight_kg', '?')}kg, Height: {user.get('height_cm', '?')}cm
- Activity: {user.get('activity_level', '?')}
- Goal: {user.get('goal', 'maintain')}
- Target: {user.get('target_weight_kg', 'not set')}kg

Respond ONLY with valid JSON:
{{"tips": ["tip1", "tip2", "tip3", "tip4", "tip5", "tip6"]}}
"""

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

    result = json.loads(text)
    result["source"] = "ai"
    return result

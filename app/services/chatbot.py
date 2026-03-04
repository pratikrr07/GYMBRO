"""
🤖 GYMBRO Fitness Chatbot Service
Uses Gemini AI when available, otherwise uses a comprehensive
fitness knowledge base with smart keyword matching.
"""

import json
import random
import re
from app.config import get_settings

settings = get_settings()

# ─────────────────────────────────────────────────────────────────
#  FITNESS KNOWLEDGE BASE
#  Organized by topic with keyword triggers + detailed answers
# ─────────────────────────────────────────────────────────────────

KNOWLEDGE_BASE = [
    # ── PROTEIN ──
    {
        "keywords": ["protein", "how much protein", "protein intake", "protein per day"],
        "q": "How much protein do I need?",
        "a": "The optimal protein intake depends on your goal:\n\n"
             "• **Fat loss**: 1.6–2.4 g/kg body weight/day to preserve muscle (Helms et al., 2014)\n"
             "• **Muscle gain**: 1.6–2.2 g/kg/day — higher intakes show diminishing returns (Morton et al., 2018, British J. Sports Med.)\n"
             "• **Maintenance**: 1.2–1.6 g/kg/day is sufficient\n\n"
             "Spread it across 4–5 meals with 0.4 g/kg per meal for optimal muscle protein synthesis (MPS). "
             "Each meal needs ~2.5–3g of leucine to trigger MPS — that's about 25–30g of whey, 170g chicken, or 3 eggs."
    },
    {
        "keywords": ["protein source", "best protein", "protein food", "high protein"],
        "q": "What are the best protein sources?",
        "a": "Here are the top protein sources per 100g:\n\n"
             "🥇 **Chicken breast**: 31g protein, 165 kcal\n"
             "🥈 **Tuna (canned)**: 26g protein, 116 kcal\n"
             "🥉 **Greek yogurt**: 10g protein, 59 kcal\n"
             "• **Eggs**: 13g protein (6g per egg), 155 kcal\n"
             "• **Lean beef**: 26g protein, 250 kcal\n"
             "• **Lentils (cooked)**: 9g protein, 116 kcal\n"
             "• **Tofu (firm)**: 8g protein, 76 kcal\n"
             "• **Whey protein**: 80g protein per 100g powder\n\n"
             "Mix animal and plant sources for complete amino acid profiles. A 2019 JAMA study showed plant protein is equally effective "
             "for muscle building when total protein and leucine intake is matched."
    },
    {
        "keywords": ["protein timing", "when to eat protein", "anabolic window", "post workout protein", "protein after workout"],
        "q": "When should I eat protein?",
        "a": "The \"anabolic window\" is a myth — it's not 30 minutes, it's actually 4–6 hours (Schoenfeld et al., 2013, JISSN).\n\n"
             "That said, here's optimal timing:\n"
             "• **Pre-workout (1-2h before)**: 20-40g protein + carbs for fuel\n"
             "• **Post-workout (within 2h)**: 20-40g protein to maximize MPS\n"
             "• **Before bed**: 30-40g casein protein — increases overnight MPS by 22% (Res et al., 2012)\n"
             "• **Spread evenly**: 4-5 meals with 0.4g/kg protein each is better than 1-2 large doses\n\n"
             "Total daily protein matters more than exact timing. Focus on hitting your daily target consistently."
    },

    # ── CALORIES & WEIGHT LOSS ──
    {
        "keywords": ["lose weight", "fat loss", "weight loss", "how to lose", "cut", "cutting", "lose fat", "burn fat"],
        "q": "How do I lose weight effectively?",
        "a": "Fat loss comes down to a sustained calorie deficit. Here's the science-backed approach:\n\n"
             "1. **Calculate your TDEE** (use the Goals page) and eat 15-25% below it\n"
             "2. **Eat high protein** (1.6-2.2 g/kg) — preserves muscle, increases satiety, and has the highest thermic effect (20-30% of protein calories are burned digesting it)\n"
             "3. **Lift weights** — resistance training during a cut preserves 93% more muscle than cardio alone (Villareal et al., 2017)\n"
             "4. **Walk more** — 10,000 steps/day burns 300-500 extra kcal with zero recovery cost\n"
             "5. **Sleep 7-9 hours** — sleeping <6h increases hunger hormones by 28% (Spiegel et al.)\n"
             "6. **Track everything** — people who track food lose 2x more weight (Kaiser et al., 2013)\n\n"
             "⚠️ Don't lose faster than 0.5-1% of body weight per week — faster rates increase muscle loss significantly."
    },
    {
        "keywords": ["calorie", "calories", "how many calories", "tdee", "bmr", "maintenance", "calorie deficit", "deficit"],
        "q": "How many calories should I eat?",
        "a": "Your calorie needs depend on your **TDEE** (Total Daily Energy Expenditure):\n\n"
             "**TDEE = BMR × Activity Multiplier**\n"
             "• BMR is calculated via the Mifflin-St Jeor equation (the most accurate formula)\n"
             "• Activity multipliers: Sedentary (1.2), Light (1.375), Moderate (1.55), Very Active (1.725)\n\n"
             "For your goal:\n"
             "• **Fat loss**: TDEE minus 15-25% (moderate deficit = sustainable)\n"
             "• **Muscle gain**: TDEE plus 200-350 kcal (lean bulk — larger surpluses mostly add fat)\n"
             "• **Maintain**: Eat at TDEE ± 100 kcal\n\n"
             "💡 Check the **Goals & Plan** page — GYMBRO calculates this automatically based on your profile!\n\n"
             "You can also set **Custom Targets** in the Goals page to manually adjust calories and macros."
    },

    # ── MUSCLE GAIN ──
    {
        "keywords": ["gain muscle", "build muscle", "muscle gain", "bulk", "bulking", "hypertrophy", "get bigger"],
        "q": "How do I build muscle?",
        "a": "Muscle growth (hypertrophy) requires three things:\n\n"
             "**1. Progressive Overload** 📈\n"
             "Increase weight by 2.5-5% when you complete all reps for 2 consecutive sessions. This is the #1 driver of growth.\n\n"
             "**2. Sufficient Volume** 🏋️\n"
             "• 10-20 sets per muscle group per week (Schoenfeld et al., 2017)\n"
             "• Train each muscle 2x/week (superior to 1x even at same volume)\n"
             "• 6-12 reps for hypertrophy, 40-70 seconds time under tension per set\n\n"
             "**3. Nutrition** 🍗\n"
             "• Caloric surplus of 200-350 kcal/day\n"
             "• 1.6-2.2 g/kg protein spread across 4-5 meals\n"
             "• Sleep 7-9 hours (growth hormone peaks during deep sleep)\n\n"
             "Realistic expectations: Beginners gain ~1-1.5% body weight in muscle/month. Intermediate: 0.5-1%. Advanced: 0.25-0.5%."
    },
    {
        "keywords": ["compound", "best exercise", "exercise for", "compound exercise", "compound movement"],
        "q": "What are the best exercises?",
        "a": "**The Big 5 compound movements** should be the foundation of any program:\n\n"
             "1. 🏋️ **Squat** — Quads, glutes, core, entire lower body\n"
             "2. 🏋️ **Deadlift** — Posterior chain, back, grip, full body strength\n"
             "3. 🏋️ **Bench Press** — Chest, shoulders, triceps\n"
             "4. 🏋️ **Overhead Press** — Shoulders, triceps, core stability\n"
             "5. 🏋️ **Barbell Row** — Back, biceps, rear delts\n\n"
             "Why compounds? They recruit more motor units, produce higher hormonal responses, and are more time-efficient.\n\n"
             "**Supplement with isolations**: Curls, lateral raises, leg curls, face pulls, etc. for lagging body parts.\n\n"
             "💡 Browse GYMBRO's exercise library with 170+ exercises across 12 categories!"
    },

    # ── TRAINING PROGRAMS ──
    {
        "keywords": ["workout plan", "program", "routine", "split", "training split", "ppl", "push pull", "how many days"],
        "q": "What workout split should I follow?",
        "a": "Here are the most popular evidence-based splits:\n\n"
             "**🔰 Beginner (3 days/week)**: Full Body\n"
             "Mon/Wed/Fri — 3 compound + 2 isolation per session. Best for neuromuscular adaptation.\n\n"
             "**💪 Intermediate (4 days/week)**: Upper/Lower\n"
             "Mon/Thu: Upper — Tue/Fri: Lower. Great balance of frequency and recovery.\n\n"
             "**🔥 Advanced (5-6 days/week)**: Push/Pull/Legs (PPL)\n"
             "Push (chest/shoulders/triceps) / Pull (back/biceps) / Legs. Run it 2x per week.\n\n"
             "**Key principles** regardless of split:\n"
             "• Train each muscle 2x/week minimum\n"
             "• 10-20 sets per muscle/week\n"
             "• Deload every 4-6 weeks (reduce volume by 40-60%)\n"
             "• Progressive overload is non-negotiable\n\n"
             "The best split is the one you can do consistently. Consistency > perfection."
    },
    {
        "keywords": ["sets", "reps", "how many sets", "how many reps", "rep range", "volume"],
        "q": "How many sets and reps should I do?",
        "a": "It depends on your goal:\n\n"
             "**Strength**: 3-5 sets × 1-5 reps @ 85-100% 1RM, 3-5 min rest\n"
             "**Hypertrophy**: 3-4 sets × 6-12 reps @ 65-85% 1RM, 60-90 sec rest\n"
             "**Endurance**: 2-3 sets × 15-25 reps @ 50-65% 1RM, 30-60 sec rest\n\n"
             "**Weekly volume per muscle group** (Schoenfeld et al., 2017):\n"
             "• Minimum effective dose: 10 sets/week\n"
             "• Sweet spot: 12-20 sets/week\n"
             "• Maximum recoverable volume: ~20-25 sets/week\n\n"
             "If you're not recovering between sessions, reduce volume. If you're plateauing, add 1-2 sets/week gradually."
    },

    # ── SUPPLEMENTS ──
    {
        "keywords": ["supplement", "creatine", "pre workout", "bcaa", "whey", "supplements"],
        "q": "Which supplements actually work?",
        "a": "Most supplements are overhyped. Here's what the science actually supports:\n\n"
             "**✅ Tier 1 — Strong evidence:**\n"
             "• **Creatine monohydrate** (5g/day): +5-10% strength, +1-2kg lean mass in 4-12 weeks. 300+ studies. The most researched supplement ever.\n"
             "• **Whey protein**: Convenient way to hit protein targets. No advantage over food protein.\n"
             "• **Caffeine** (3-6mg/kg): +3-11% metabolic rate, improved strength and endurance.\n\n"
             "**⚠️ Tier 2 — Some evidence:**\n"
             "• **Vitamin D** (2000-4000 IU if deficient): 42% of adults are deficient; affects strength by up to 20%.\n"
             "• **Fish oil** (2-3g EPA+DHA): Anti-inflammatory, joint health.\n"
             "• **Magnesium**: If deficient, can reduce performance by 20%.\n\n"
             "**❌ Skip:** BCAAs (pointless if you eat enough protein), fat burners, testosterone boosters, most proprietary blends.\n\n"
             "💡 No supplement replaces consistent training, proper nutrition, and adequate sleep."
    },
    {
        "keywords": ["creatine", "creatine safe", "how to take creatine", "creatine loading"],
        "q": "How should I take creatine?",
        "a": "Creatine monohydrate is the most researched and safest supplement in sports science (Kreider et al., 2017).\n\n"
             "**How to take it:**\n"
             "• **Simple way**: 5g/day every day. Takes ~3-4 weeks to saturate muscles.\n"
             "• **Loading (optional)**: 20g/day (split into 4×5g) for 5-7 days, then 5g/day maintenance. Saturates faster.\n"
             "• **Timing**: Doesn't matter much. Post-workout with carbs may slightly improve uptake.\n"
             "• **With water**: Drink plenty of water (creatine pulls water into muscle cells).\n\n"
             "**Benefits**: +5-10% strength, +1-2kg lean mass, improved power output, faster recovery between sets.\n\n"
             "**Safety**: Extensively studied. No evidence of kidney damage in healthy individuals. Over 500 peer-reviewed studies confirm safety.\n\n"
             "**Only buy creatine monohydrate** — other forms (HCl, ethyl ester, etc.) are more expensive with no additional benefit."
    },

    # ── CARDIO ──
    {
        "keywords": ["cardio", "running", "how much cardio", "cardio kill gains", "cardio and muscle", "hiit"],
        "q": "Will cardio kill my gains?",
        "a": "No — but the type and amount matters. Here's the nuance:\n\n"
             "**✅ Zone 2 cardio (60-70% max HR)**: Walking, easy cycling, light jogging\n"
             "• 150 min/week improves heart health and fat oxidation WITHOUT hurting muscle gains (Seiler, 2010)\n"
             "• Actually improves recovery between lifting sessions\n\n"
             "**⚠️ HIIT**: Great for conditioning and fat loss (EPOC burns extra calories 24-72h after)\n"
             "• Limit to 2-3 sessions/week, separate from lifting by 6+ hours if possible\n\n"
             "**❌ Excessive long-duration cardio** (marathon training) can interfere with strength gains due to the \"interference effect\" (Hickson, 1980)\n\n"
             "**The sweet spot**: 2-3 Zone 2 sessions (20-30 min) + 1-2 HIIT sessions/week.\n"
             "Walking 10,000 steps/day is the most underrated cardio — burns 300-500 kcal, zero recovery cost."
    },

    # ── RECOVERY & SLEEP ──
    {
        "keywords": ["recovery", "rest day", "overtraining", "rest", "sore", "doms"],
        "q": "How important is recovery?",
        "a": "Recovery is when muscle growth actually happens. Training creates the stimulus; rest builds the muscle.\n\n"
             "**Key recovery factors:**\n"
             "1. **Sleep**: 7-9 hours minimum. Growth hormone peaks during stages 3-4. <7h sleep reduces testosterone by 10-15% (Leproult & Van Cauter, 2011)\n"
             "2. **Rest between sessions**: Each muscle group needs 48-72h. Training a sore muscle reduces MPS by up to 50%\n"
             "3. **Deload weeks**: Every 4-6 weeks, reduce volume by 40-60% while keeping intensity\n"
             "4. **Nutrition**: Hit your protein and calorie targets\n\n"
             "**Signs of overtraining:**\n"
             "• Resting heart rate 7+ BPM above baseline\n"
             "• Persistent fatigue, mood changes, poor sleep\n"
             "• Strength plateaus or regression\n"
             "• Getting sick frequently\n\n"
             "💡 Track your resting HR in the morning — it's one of the best recovery metrics."
    },
    {
        "keywords": ["sleep", "how much sleep", "sleep for muscle", "sleep and gains"],
        "q": "How does sleep affect my gains?",
        "a": "Sleep is arguably the most powerful (and free) recovery tool:\n\n"
             "**What happens during sleep:**\n"
             "• **Growth hormone**: 70-80% is released during deep sleep (stages 3-4)\n"
             "• **Testosterone**: Peaks during REM sleep. <7h reduces it by 10-15%\n"
             "• **Muscle protein synthesis**: Repair processes accelerate\n"
             "• **Brain recovery**: Memory consolidation, motor learning from training\n\n"
             "**Sleep deprivation effects (Mah et al., 2011):**\n"
             "• 10-30% reduction in strength and power output\n"
             "• 28% increase in ghrelin (hunger hormone)\n"
             "• 18% decrease in leptin (satiety hormone)\n"
             "• Impaired glucose metabolism → more fat storage\n\n"
             "**Tips for better sleep:**\n"
             "• Same bedtime/wake time (±30 min)\n"
             "• Cool room: 65-68°F (18-20°C)\n"
             "• No screens 1h before bed\n"
             "• 30-40g casein protein before bed → +22% overnight MPS (Res et al., 2012)"
    },

    # ── STRETCHING & MOBILITY ──
    {
        "keywords": ["stretch", "stretching", "mobility", "flexibility", "foam roll", "warm up"],
        "q": "Should I stretch before or after workouts?",
        "a": "**Before workout — Dynamic stretching ✅**\n"
             "• Leg swings, arm circles, hip openers, walking lunges\n"
             "• Increases blood flow, core temperature, and range of motion\n"
             "• Prepares nervous system for heavy loads\n\n"
             "**Before workout — Static stretching ❌**\n"
             "• Holding stretches 30+ seconds BEFORE lifting can reduce strength by 5-8% and power by up to 2% (Simic et al., 2013)\n\n"
             "**After workout — Static stretching ✅**\n"
             "• Hold stretches 30-60 seconds per muscle\n"
             "• Improves long-term flexibility\n"
             "• Does NOT significantly reduce DOMS (sorry!)\n\n"
             "**Foam rolling**: 1-2 min per muscle group. Reduces DOMS by 20% and improves ROM temporarily.\n\n"
             "**Mobility work**: 10-15 min daily prevents fascia tightness that reduces ROM by 5-10%/year (Stecco et al., 2013)."
    },

    # ── SPECIFIC BODY PARTS ──
    {
        "keywords": ["abs", "six pack", "core", "ab exercise", "visible abs"],
        "q": "How do I get visible abs?",
        "a": "Abs are made in the gym but revealed in the kitchen. Here's the truth:\n\n"
             "**1. Body fat percentage is everything:**\n"
             "• Men: Abs visible at ~10-14% body fat\n"
             "• Women: Abs visible at ~16-20% body fat\n"
             "• This requires a sustained calorie deficit — you cannot spot-reduce fat\n\n"
             "**2. Still train them directly:**\n"
             "• Weighted exercises: Cable crunches, hanging leg raises, ab wheel\n"
             "• Anti-movement exercises: Planks, Pallof press, dead bugs\n"
             "• 2-3 sessions/week, 3-4 sets each, treat them like any muscle\n\n"
             "**3. Compound lifts work core hard:**\n"
             "• Squats, deadlifts, and overhead press all heavily engage your core\n"
             "• But direct ab work still adds development\n\n"
             "⚠️ Doing 100 crunches daily won't reveal abs if body fat is too high. Focus on your deficit first."
    },
    {
        "keywords": ["chest", "bench press", "chest exercise", "grow chest"],
        "q": "How do I build a bigger chest?",
        "a": "Chest growth requires hitting all three regions:\n\n"
             "**Upper chest** (Clavicular head):\n"
             "• Incline bench press (30-45°)\n"
             "• Incline dumbbell press\n"
             "• Low-to-high cable flyes\n\n"
             "**Middle chest** (Sternal head):\n"
             "• Flat bench press\n"
             "• Flat dumbbell press\n"
             "• Machine chest press\n\n"
             "**Lower chest**:\n"
             "• Decline bench press\n"
             "• Dips (leaning forward)\n"
             "• High-to-low cable flyes\n\n"
             "**Programming**: 12-20 sets/week total for chest, train 2x/week.\n"
             "Focus on progressive overload on the bench press — it's the king of chest exercises.\n"
             "Use full ROM (bar to chest) for maximum muscle fiber recruitment."
    },
    {
        "keywords": ["back", "pull up", "pullup", "lat", "back exercise", "grow back", "wide back"],
        "q": "How do I build a bigger back?",
        "a": "The back has many muscles — you need both vertical and horizontal pulling:\n\n"
             "**Vertical pulling** (Lats — width):\n"
             "• Pull-ups / chin-ups (bodyweight king)\n"
             "• Lat pulldowns (wide and close grip)\n"
             "• Straight-arm pulldowns\n\n"
             "**Horizontal pulling** (Rhomboids, traps — thickness):\n"
             "• Barbell rows\n"
             "• Dumbbell rows\n"
             "• Cable rows (close grip)\n"
             "• T-bar rows\n\n"
             "**Rear delts** (for that 3D look):\n"
             "• Face pulls (do these every session!)\n"
             "• Reverse flyes\n\n"
             "**Tips**: Use straps if grip limits your back work. Focus on the squeeze — "
             "mind-muscle connection increased back hypertrophy by 12.4% (Schoenfeld, 2016). 12-20 sets/week, train 2x/week."
    },

    # ── NUTRITION TIMING ──
    {
        "keywords": ["meal prep", "meal timing", "how many meals", "intermittent fasting", "fasting", "when to eat"],
        "q": "How many meals should I eat per day?",
        "a": "Meal frequency has a smaller effect than total daily intake, but here's the research:\n\n"
             "**For muscle gain**: 4-5 meals/day is slightly superior\n"
             "• Each meal triggers MPS for ~3-5 hours\n"
             "• Spreading protein (0.4g/kg per meal) maximizes total daily MPS (Schoenfeld & Aragon, 2018)\n\n"
             "**For fat loss**: Meal frequency doesn't matter much\n"
             "• 2-3 meals vs 5-6 meals — same fat loss when calories are equal\n"
             "• Intermittent fasting (16:8) works by naturally reducing intake by ~300 kcal/day (Wilkinson et al., 2020)\n"
             "• Choose whatever pattern you can stick to\n\n"
             "**Pre-workout**: Eat 1-2 hours before training — protein + carbs for performance\n"
             "**Post-workout**: Within 2 hours — protein (20-40g) + carbs to replenish glycogen\n"
             "**Before bed**: Casein protein → slow amino release for 7 hours\n\n"
             "💡 The best meal plan is the one that fits your lifestyle."
    },
    {
        "keywords": ["macro", "macros", "macronutrient", "counting macros", "iifym", "track macros"],
        "q": "How do I count macros?",
        "a": "Macro counting (IIFYM — If It Fits Your Macros) is the flexible approach:\n\n"
             "**Step 1: Set calories** (GYMBRO calculates this for you!)\n\n"
             "**Step 2: Set protein first**\n"
             "• 1.6-2.2 g/kg bodyweight → multiply by 4 for calories from protein\n\n"
             "**Step 3: Set fat**\n"
             "• 0.7-1.2 g/kg bodyweight → multiply by 9 for calories from fat\n"
             "• Don't go below 0.5g/kg — hormones need dietary fat\n\n"
             "**Step 4: Fill rest with carbs**\n"
             "• Remaining calories ÷ 4 = carb grams\n"
             "• Carbs fuel workouts and recovery\n\n"
             "**Calorie values:**\n"
             "• Protein: 4 kcal/g\n"
             "• Carbs: 4 kcal/g\n"
             "• Fat: 9 kcal/g\n"
             "• Alcohol: 7 kcal/g\n\n"
             "💡 Use the **Custom Targets** section on the Goals page to set your exact macro targets!"
    },

    # ── BEGINNER QUESTIONS ──
    {
        "keywords": ["beginner", "start", "starting", "new to gym", "first time", "never worked out"],
        "q": "I'm a beginner — where do I start?",
        "a": "Welcome! Here's a beginner roadmap:\n\n"
             "**Week 1-2: Learn the basics**\n"
             "• Focus on form with light weights or bodyweight\n"
             "• 3 days/week full body: Squat, Bench, Row, OHP, Deadlift\n"
             "• 3 sets × 8-10 reps each exercise\n\n"
             "**Week 3-8: Build a foundation**\n"
             "• Start progressive overload (add 2.5 kg/week)\n"
             "• Learn to brace your core and breathe properly\n"
             "• Track everything in GYMBRO!\n\n"
             "**Nutrition for beginners:**\n"
             "• Hit protein target (1.6g/kg) — this alone makes a huge difference\n"
             "• Don't overthink it — eat whole foods, drink water, sleep 7-9 hours\n\n"
             "**The magic of beginner gains:**\n"
             "New lifters gain muscle AND lose fat simultaneously (body recomp). "
             "You can expect to add 1-1.5% of body weight in muscle per month for the first 6-12 months. Enjoy this period — it never comes back!"
    },
    {
        "keywords": ["plateau", "stuck", "not progressing", "not gaining", "stalled", "hit a wall"],
        "q": "I've hit a plateau — what do I do?",
        "a": "Plateaus are normal and solvable:\n\n"
             "**Strength plateau:**\n"
             "• Try a deload week (reduce volume 40-60%, keep intensity)\n"
             "• Switch rep ranges: If doing 5×5, try 3×8-10 for 4 weeks\n"
             "• Add variation: Different grip, stance, or exercise angle\n"
             "• Ensure caloric surplus if trying to get stronger\n\n"
             "**Weight loss plateau:**\n"
             "• Recalculate TDEE at your new lower weight\n"
             "• Add 1,000-2,000 steps/day instead of cutting more calories\n"
             "• Diet break: Eat at maintenance for 1-2 weeks, then resume deficit\n"
             "• Check if you're actually in a deficit (hidden calories in oils, sauces, drinks)\n\n"
             "**Muscle growth plateau:**\n"
             "• Increase training volume by 10-20%\n"
             "• Ensure progressive overload is happening\n"
             "• Eat more — you may need a larger surplus\n"
             "• Sleep and recovery — this is often the bottleneck\n\n"
             "Remember: Progress is never perfectly linear. Trust the process."
    },

    # ── INJURIES & PAIN ──
    {
        "keywords": ["injury", "pain", "hurt", "sore", "knee pain", "back pain", "shoulder pain"],
        "q": "I'm experiencing pain during exercise — what should I do?",
        "a": "⚠️ **Important: I'm an AI fitness chatbot, not a doctor. For serious pain, see a medical professional.**\n\n"
             "**DOMS (Delayed Onset Muscle Soreness)** — normal:\n"
             "• Occurs 24-72 hours after training\n"
             "• Dull, achy soreness in the muscles you trained\n"
             "• Safe to train through (lightly) — active recovery helps\n\n"
             "**Sharp/joint pain** — not normal:\n"
             "• Stop the exercise immediately\n"
             "• Sharp, stabbing, or shooting pain = potential injury\n"
             "• Joint pain (knee, shoulder, elbow) during movements = form issue or existing condition\n\n"
             "**Common fixes:**\n"
             "• **Knee pain during squats**: Check if knees track over toes, try box squats\n"
             "• **Lower back pain during deadlifts**: Likely rounding — reduce weight, focus on bracing\n"
             "• **Shoulder pain during bench**: Try floor press, widen grip, or switch to dumbbells\n\n"
             "When in doubt, **see a physiotherapist**. Training through injury = longer recovery."
    },

    # ── GYMBRO APP SPECIFIC ──
    {
        "keywords": ["how to use", "app", "gymbro", "features", "what can you do", "help"],
        "q": "What can GYMBRO do?",
        "a": "Here's everything GYMBRO offers:\n\n"
             "🏋️ **Workout Tracking** — Log exercises, sets, reps, and weight from 170+ exercises across 12 categories. Create custom exercises too!\n\n"
             "🍽️ **Meal Logging** — AI-powered calorie estimation, macro tracking (protein/carbs/fat), daily summaries.\n\n"
             "🎯 **Goals & Nutrition Plan** — Auto-calculated BMR, TDEE, macro targets based on your profile. Set custom calorie/macro targets.\n\n"
             "📊 **Progress Charts** — Calorie trends, workout frequency, strength progression over time.\n\n"
             "🏅 **Achievements** — 14 badges to unlock as you hit milestones.\n\n"
             "🏆 **Personal Records** — Auto-detected PRs for max weight and estimated 1RM.\n\n"
             "💧 **Water Tracker** — Track daily water intake.\n\n"
             "↔️ **Unilateral Tracking** — Track left/right sides separately for balanced training.\n\n"
             "⚡ **Superset Grouping** — Link exercises together as supersets.\n\n"
             "⚖️ **KG/LBS Toggle** — Switch weight display units in your profile.\n\n"
             "💬 **This chatbot** — Ask me anything about fitness!"
    },
]

# ── FALLBACK RESPONSES ──
FALLBACK_RESPONSES = [
    "That's a great question! While I don't have a specific answer for that in my knowledge base, "
    "here's what I'd suggest: check the **Goals & Plan** page for personalized nutrition targets, "
    "and try the **↻ Refresh** button on coaching tips for science-backed advice.",

    "I'm not sure about that specific topic, but I can help with questions about: "
    "💪 Muscle building, 🔥 Fat loss, 🥩 Protein & nutrition, 🏋️ Training programs, "
    "💊 Supplements, 😴 Recovery & sleep, and much more. Try asking about one of these!",

    "I don't have a detailed answer for that yet, but here's a universal fitness truth: "
    "**Consistency beats perfection.** Show up, train hard, eat enough protein, sleep well, "
    "and the results will come. Feel free to ask me something else!",
]


def _find_best_match(query: str) -> dict | None:
    """Find the best matching knowledge base entry using keyword scoring."""
    query_lower = query.lower()
    query_words = set(re.findall(r'\b\w+\b', query_lower))

    best_match = None
    best_score = 0

    for entry in KNOWLEDGE_BASE:
        score = 0
        for keyword in entry["keywords"]:
            kw_lower = keyword.lower()
            # Exact phrase match = highest score
            if kw_lower in query_lower:
                score += 10 + len(kw_lower)
            # Word overlap
            kw_words = set(re.findall(r'\b\w+\b', kw_lower))
            overlap = len(query_words & kw_words)
            score += overlap * 3

        if score > best_score:
            best_score = score
            best_match = entry

    # Require minimum score to avoid false matches
    if best_score >= 6:
        return best_match
    return None


async def get_chat_response(message: str, user: dict | None = None) -> dict:
    """Generate a chatbot response using AI or the knowledge base."""

    # Try AI first if available
    if settings.GEMINI_API_KEY:
        try:
            return await _ai_chat(message, user)
        except Exception as e:
            print(f"⚠️ AI chat failed: {e}, using knowledge base")

    # Fallback to knowledge base
    match = _find_best_match(message)

    if match:
        return {
            "response": match["a"],
            "source": "knowledge_base",
            "matched_topic": match["q"],
        }

    # No match — return a helpful fallback
    return {
        "response": random.choice(FALLBACK_RESPONSES),
        "source": "fallback",
        "matched_topic": None,
    }


async def get_suggested_questions() -> list[str]:
    """Return a rotating set of suggested questions."""
    all_questions = [entry["q"] for entry in KNOWLEDGE_BASE]
    return random.sample(all_questions, min(5, len(all_questions)))


async def _ai_chat(message: str, user: dict | None = None) -> dict:
    """Generate a response using Gemini AI."""
    import asyncio
    from google import genai

    client = genai.Client(api_key=settings.GEMINI_API_KEY)
    model_name = "gemini-2.0-flash"

    user_context = ""
    if user:
        user_context = f"""
User Profile:
- Age: {user.get('age', '?')}, Gender: {user.get('gender', '?')}
- Weight: {user.get('weight_kg', '?')}kg, Height: {user.get('height_cm', '?')}cm
- Activity Level: {user.get('activity_level', '?')}
- Goal: {user.get('goal', '?')}
- Target Weight: {user.get('target_weight_kg', 'not set')}kg
"""

    prompt = f"""You are GYMBRO's fitness AI assistant — an expert sports science coach and nutritionist.
Answer fitness, nutrition, training, and health questions with:
- Evidence-based information with study references when possible
- Practical, actionable advice
- Appropriate use of markdown formatting (bold, lists, etc.)
- Emojis for readability
- Keep responses concise but thorough (under 300 words)

ONLY answer fitness, nutrition, exercise, health, and wellness related questions.
If someone asks something unrelated to fitness, politely redirect them.

{user_context}

User question: {message}
"""

    response = await asyncio.wait_for(
        asyncio.to_thread(
            client.models.generate_content,
            model=model_name, contents=prompt
        ),
        timeout=10,
    )
    return {
        "response": response.text.strip(),
        "source": "ai",
        "matched_topic": None,
    }

"""
🏋️ GYMBRO — AI Fitness Tracker & Coach
FastAPI Backend Application
"""

import os
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.database import connect_db, close_db
from app.services.seed import seed_exercises

# ─────────────────────────────────────────────────────────────────
# FILE PATHS & DIRECTORIES
# ─────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent  # Project root directory
STATIC_DIR = BASE_DIR / "static"                    # Frontend assets (HTML, CSS, JS, icons)

# ─────────────────────────────────────────────────────────────────
# IMPORT ALL API ROUTERS
# Each router handles a specific domain (auth, workouts, meals, etc.)
# ─────────────────────────────────────────────────────────────────
from app.routes.auth import router as auth_router
from app.routes.workout import router as workout_router
from app.routes.workout import exercise_router
from app.routes.meal import router as meal_router
from app.routes.goal import router as goal_router
from app.routes.progress import router as progress_router
from app.routes.chat import router as chat_router
from app.routes.template import router as template_router
from app.routes.recipe import router as recipe_router
from app.routes.rank import router as rank_router
from app.routes.coaching import router as coaching_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifecycle events.
    Runs when server starts & stops.
    """
    # ═══════════════════════════════════════════════════════════════
    # STARTUP: Initialize database and seed default data
    # ═══════════════════════════════════════════════════════════════
    await connect_db()                    # Connect to MongoDB
    await seed_exercises()                # Seed 170+ default exercises if not already present
    print("🏋️ GYMBRO API is ready!")
    yield
    
    # ═══════════════════════════════════════════════════════════════
    # SHUTDOWN: Clean up database connection
    # ═══════════════════════════════════════════════════════════════
    await close_db()                      # Gracefully close MongoDB connection


app = FastAPI(
    title="🏋️ GYMBRO — AI Fitness Tracker & Coach",
    description=(
        "Track workouts, log meals with AI-powered calorie estimation, "
        "set goals, and get personalized coaching tips."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# ─────────────────────────────────────────────────────────────────
# MIDDLEWARE: CORS (Cross-Origin Resource Sharing)
# Allows frontend to make requests to this API
# ⚠️  Production: Restrict allow_origins to your domain
# ─────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],              # Allow all origins (change for production)
    allow_credentials=True,            # Allow cookies/auth headers
    allow_methods=["*"],              # Allow all HTTP methods
    allow_headers=["*"],              # Allow all headers
)

# ═════════════════════════════════════════════════════════════════
# REGISTER ALL API ROUTES
# Each include_router attaches a domain's endpoints to the FastAPI app
# ═════════════════════════════════════════════════════════════════
app.include_router(auth_router)          # /api/auth/* — Login, register, authentication
app.include_router(exercise_router)      # /api/exercises/* — Exercise library & management
app.include_router(workout_router)       # /api/workouts/* — Log workouts, track volume
app.include_router(meal_router)          # /api/meals/* — Log meals, calorie tracking
app.include_router(goal_router)          # /api/goals/* — Create & track fitness goals
app.include_router(progress_router)      # /api/progress/* — Heatmap, stats, analytics
app.include_router(chat_router)          # /api/chat/* — AI chatbot for coaching
app.include_router(template_router)      # /api/templates/* — Workout templates & presets
app.include_router(recipe_router)        # /api/recipes/* — Meal recipe suggestions
app.include_router(rank_router)          # /api/rank/* — Leaderboards & rankings
app.include_router(coaching_router)      # /api/coaching/* — 🤖 AI Smart Coach (analysis & workouts)

# ─────────────────────────────────────────────────────────────────
# SERVE STATIC FILES
# Maps /static/* URLs to actual files (CSS, JS, icons)
# ─────────────────────────────────────────────────────────────────
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


# ═════════════════════════════════════════════════════════════════
# SERVICE WORKER (PWA - Progressive Web App)
# Must be served from root (/) for offline support & app installation
# This enables: offline mode, background sync, home screen install
# ═════════════════════════════════════════════════════════════════
@app.get("/sw.js", include_in_schema=False)  # Not in OpenAPI docs
async def service_worker():
    """Serve service worker file with no-cache headers for PWA."""
    return FileResponse(
        str(STATIC_DIR / "sw.js"),
        media_type="application/javascript",
        headers={"Cache-Control": "no-cache, no-store, must-revalidate"},  # Always check for updates
    )


# ═════════════════════════════════════════════════════════════════
# CACHE CLEARING UTILITY
# Helps users manually clear service worker, localStorage, caches
# Navigate to http://localhost:8000/clear-cache to use
# ═════════════════════════════════════════════════════════════════
@app.get("/clear-cache", include_in_schema=False)  # Hidden from API docs
async def clear_cache():
    from fastapi.responses import HTMLResponse
    return HTMLResponse("""
    <!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
    <title>GYMBRO - Clear Cache</title>
    <style>body{background:#0f0f0f;color:#e8e8e8;font-family:Inter,sans-serif;display:flex;align-items:center;justify-content:center;min-height:100vh;margin:0;padding:1rem}
    .box{text-align:center;max-width:400px}.logo{font-size:2rem;font-weight:800;margin-bottom:1rem}
    .logo span{color:#c9a84c}#status{margin:1rem 0;padding:1rem;border-radius:10px;background:#1a1a1a;text-align:left;line-height:2}
    .btn{background:#c9a84c;color:#0f0f0f;border:none;padding:12px 24px;border-radius:8px;font-weight:700;font-size:1rem;cursor:pointer;margin-top:1rem}</style></head>
    <body><div class="box">
    <div class="logo">GYM<span>BRO</span></div>
    <h2>🧹 Clearing Cache...</h2>
    <div id="status">Working...</div>
    <script>
    async function clearAll(){
      var s=document.getElementById('status');var steps=[];
      try{
        if('serviceWorker' in navigator){
          try{
            var regs=await navigator.serviceWorker.getRegistrations();
            for(var i=0;i<regs.length;i++){await regs[i].unregister();steps.push('✅ Service Worker unregistered')}
            if(!regs.length) steps.push('ℹ️ No service workers found');
          }catch(e){steps.push('⚠️ SW: '+e.message)}
        }else{steps.push('ℹ️ No SW support')}
        if(typeof caches!=='undefined'){
          try{
            var keys=await caches.keys();
            for(var j=0;j<keys.length;j++){await caches.delete(keys[j]);steps.push('✅ Cache "'+keys[j]+'" deleted')}
            if(!keys.length) steps.push('ℹ️ No caches found');
          }catch(e){steps.push('⚠️ Cache: '+e.message)}
        }else{steps.push('ℹ️ Cache API not available (needs HTTPS)')}
        try{localStorage.clear();steps.push('✅ LocalStorage cleared')}catch(e){steps.push('⚠️ LS: '+e.message)}
        try{sessionStorage.clear();steps.push('✅ SessionStorage cleared')}catch(e){}
        steps.push('');
        steps.push('🎉 Done! Redirecting in 2s...');
        s.innerHTML=steps.join('<br>');
        setTimeout(function(){window.location.href='/'},2000);
      }catch(e){s.innerHTML='❌ Error: '+e.message+'<br><br><button class=\"btn\" onclick=\"window.location.href=\\'/\\'\">Go to App →</button>'}
    }
    clearAll();
    </script></div></body></html>
    """)


# ═════════════════════════════════════════════════════════════════
# HEALTH CHECK & FRONTEND SERVING
# ═════════════════════════════════════════════════════════════════

@app.get("/", tags=["Health"])
async def root():
    """Serve the main SPA (Single Page Application) frontend."""
    return FileResponse(
        str(STATIC_DIR / "index.html"),
        headers={"Cache-Control": "no-cache, no-store, must-revalidate"},  # Force reload
    )


@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint.
    Verifies API & database are running.
    Called by monitoring systems or status pages.
    """
    from app.database import get_db
    db = get_db()
    try:
        await db.command("ping")          # Ping MongoDB to verify connection
        return {"status": "healthy", "database": "connected"}
    except Exception:
        return {"status": "unhealthy", "database": "disconnected"}

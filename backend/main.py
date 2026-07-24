"""
FIXO DEV — Guild Glory Bot (Multi-Bot)
"""

# ===== PATH SETUP =====
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from backend.database import DatabaseManager
from backend.engine import GloryFarmingEngine
from backend.scheduler import GuildScheduler
from backend.bot_manager import BotAccountManager
from backend.models import GuildAddRequest
from backend.config import config

logger = logging.getLogger("FIXO-DEV")
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format='[%(asctime)s] %(levelname)s - %(name)s - %(message)s'
)

# ===== GLOBAL STATE =====
db = DatabaseManager(config.DB_PATH)
engine = GloryFarmingEngine(db, config)
scheduler = GuildScheduler(db, engine, config)
bot_manager = BotAccountManager()
engine_task = None
scheduler_task = None

# ===== LIFESPAN =====
@asynccontextmanager
async def lifespan(app: FastAPI):
    global engine_task, scheduler_task
    
    logger.info("🚀 FIXO DEV Starting... (Multi-Bot)")
    logger.info(f"🤖 Bots: {len(bot_manager.bots)}")
    
    bot_manager._load_bots_from_config()
    engine_task = asyncio.create_task(engine.start())
    scheduler_task = asyncio.create_task(scheduler.start())
    
    yield
    
    logger.info("🛑 Shutting down...")
    await engine.stop()
    await scheduler.stop()
    if engine_task:
        engine_task.cancel()
    if scheduler_task:
        scheduler_task.cancel()

# ===== APP =====
app = FastAPI(title="FIXO DEV", version="3.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {
        "service": "FIXO DEV",
        "version": "3.0.0",
        "bots": len(bot_manager.bots),
        "status": "online"
    }

@app.get("/api/health")
async def health_check():
    queue = await engine.get_queue_status()
    stats = db.get_stats()
    return {"status": "healthy", "queue": queue, "stats": stats}

@app.get("/api/bots")
async def get_bots():
    return bot_manager.get_stats()

@app.post("/api/guild/add")
async def add_guild(request: GuildAddRequest):
    success = db.add_guild(request.guild_uid, request.guild_name or "", request.country)
    if not success:
        raise HTTPException(400, "Failed to add guild")
    
    bot_name = await engine.assign_bot_to_guild(request.guild_uid)
    if bot_name:
        db.assign_bot_to_guild(request.guild_uid, bot_name)
        guilds = db.get_pending_guilds(limit=1)
        if guilds:
            await engine.queue_guild_for_farming(guilds[0], bot_name)
    
    return {"status": "success", "guild": request.guild_uid, "bot": bot_name or "pending"}

@app.get("/api/guilds")
async def get_guilds():
    return [g.to_dict() for g in db.get_all_guilds()]

@app.post("/api/farm/start")
async def start_farming():
    guilds = db.get_pending_guilds()
    assigned = 0
    for guild in guilds:
        bot_name = await engine.assign_bot_to_guild(guild.uid)
        if bot_name:
            db.assign_bot_to_guild(guild.uid, bot_name)
            await engine.queue_guild_for_farming(guild, bot_name)
            assigned += 1
    return {"status": "success", "guilds": len(guilds), "assigned": assigned}

@app.post("/api/farm/stop")
async def stop_farming():
    await bot_manager.stop_all_bots()
    return {"status": "success", "message": "Stopped"}

@app.get("/api/stats")
async def get_stats():
    stats = db.get_stats()
    bot_stats = bot_manager.get_stats()
    stats["bots"] = bot_stats
    return stats

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))  # Render එකට ගැලපෙන PORT
    logger.info(f"🔥 FIXO DEV — Multi-Bot Mode")
    logger.info(f"📡 http://0.0.0.0:{port}")
    uvicorn.run("backend.main:app", host="0.0.0.0", port=port)
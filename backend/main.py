"""
FIXO DEV — Guild Glory Bot
FastAPI Application
"""

import asyncio
import logging
import sys
import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from typing import List

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import config
from database import DatabaseManager
from engine import GloryFarmingEngine
from scheduler import GuildScheduler
from models import (
    GuildAddRequest, BotRegisterRequest, FarmStartRequest,
    FarmStopRequest, StatsResponse, GuildResponse, BotResponse
)

# ===== LOGGING =====
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format='[%(asctime)s] %(levelname)s - %(name)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("FIXO-DEV")

# ===== GLOBAL STATE =====
db = DatabaseManager(config.DB_PATH)
engine = GloryFarmingEngine(db, config)
scheduler = GuildScheduler(db, engine, config)
engine_task = None
scheduler_task = None

# ===== LIFESPAN =====
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global engine_task, scheduler_task
    
    logger.info("🚀 FIXO DEV Starting up...")
    
    # Start engine
    engine_task = asyncio.create_task(engine.start())
    
    # Start scheduler
    scheduler_task = asyncio.create_task(scheduler.start())
    
    yield
    
    # Shutdown
    logger.info("🛑 FIXO DEV Shutting down...")
    await engine.stop()
    await scheduler.stop()
    if engine_task:
        engine_task.cancel()
    if scheduler_task:
        scheduler_task.cancel()
    
    logger.info("✅ FIXO DEV Shutdown complete")

# ===== FASTAPI APP =====
app = FastAPI(
    title="FIXO DEV — Guild Glory Bot API",
    description="Automated glory farming for FreeFire guilds",
    version="1.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===== HEALTH CHECK =====
@app.get("/")
async def root():
    return {
        "service": "FIXO DEV — Guild Glory Bot",
        "status": "online",
        "version": "1.0.0",
        "region": config.GAME_REGION,
        "sri_lanka_optimized": True
    }

@app.get("/api/health")
async def health_check():
    queue_status = await engine.get_queue_status()
    stats = db.get_stats()
    return {
        "status": "healthy",
        "engine_running": engine.running,
        "scheduler_running": scheduler.running,
        "queue": queue_status,
        "stats": stats
    }

# ===== GUILD ENDPOINTS =====
@app.post("/api/guild/add")
async def add_guild(request: GuildAddRequest):
    """Add a new guild to the farming queue."""
    try:
        success = db.add_guild(
            uid=request.guild_uid,
            name=request.guild_name or "",
            country=request.country
        )
        if not success:
            raise HTTPException(status_code=400, detail="Failed to add guild")
        
        # Auto-activate if bots available
        bots = db.get_all_bots(status="idle")
        if bots:
            bot = bots[0]
            db.assign_bot_to_guild(request.guild_uid, bot.name)
            bot.assigned_guilds.append(request.guild_uid)
            
            # Get guild and queue for farming
            guilds = db.get_pending_guilds(limit=1)
            if guilds:
                await engine.queue_guild_for_farming(guilds[0], bot)
        
        return {"status": "success", "guild_uid": request.guild_uid}
    except Exception as e:
        logger.error(f"Add guild error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/guilds")
async def get_guilds():
    """Get all guilds."""
    try:
        guilds = db.get_all_guilds()
        return [g.to_dict() for g in guilds]
    except Exception as e:
        logger.error(f"Get guilds error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/guilds/{guild_uid}")
async def get_guild(guild_uid: str):
    """Get a specific guild by UID."""
    try:
        guilds = db.get_all_guilds()
        guild = next((g for g in guilds if g.uid == guild_uid), None)
        if not guild:
            raise HTTPException(status_code=404, detail="Guild not found")
        return guild.to_dict()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get guild error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/guilds/{guild_uid}/history")
async def get_guild_history(guild_uid: str, limit: int = 50):
    """Get glory history for a guild."""
    try:
        logs = db.get_glory_history(guild_uid, limit)
        return [
            {
                "guild_uid": log.guild_uid,
                "bot_name": log.bot_name,
                "glory": log.glory_amount,
                "success": log.success,
                "error": log.error_message,
                "timestamp": log.timestamp.isoformat()
            }
            for log in logs
        ]
    except Exception as e:
        logger.error(f"Get history error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ===== BOT ENDPOINTS =====
@app.post("/api/bot/register")
async def register_bot(request: BotRegisterRequest):
    """Register a new bot."""
    try:
        success = db.register_bot(
            bot_name=request.bot_name,
            token=request.bot_token,
            bot_type=request.bot_type,
            max_guilds=request.max_guilds
        )
        if not success:
            raise HTTPException(status_code=400, detail="Failed to register bot")
        return {"status": "success", "bot_name": request.bot_name}
    except Exception as e:
        logger.error(f"Register bot error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/bots")
async def get_bots():
    """Get all bots."""
    try:
        bots = db.get_all_bots()
        return [
            {
                "name": b.name,
                "type": b.bot_type,
                "status": b.status,
                "max_guilds": b.max_guilds,
                "region": b.region
            }
            for b in bots
        ]
    except Exception as e:
        logger.error(f"Get bots error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ===== FARM ENDPOINTS =====
@app.post("/api/farm/start")
async def start_farming(request: FarmStartRequest):
    """Start farming for all active guilds."""
    try:
        # Register bot if not exists
        existing = db.get_bot(request.bot_name)
        if not existing:
            # Create dummy token for demo
            db.register_bot(
                bot_name=request.bot_name,
                token=f"FIXO_{request.bot_name}_TOKEN",
                bot_type=request.bot_type
            )
        
        # Update bot status
        db.update_bot_status(request.bot_name, "active")
        
        # Get pending guilds
        guilds = db.get_pending_guilds()
        bot = db.get_bot(request.bot_name)
        
        for guild in guilds:
            db.assign_bot_to_guild(guild.uid, request.bot_name)
            if bot:
                bot.assigned_guilds.append(guild.uid)
                await engine.queue_guild_for_farming(guild, bot)
        
        return {
            "status": "success",
            "message": f"Bot {request.bot_name} deployed",
            "guilds_queued": len(guilds)
        }
    except Exception as e:
        logger.error(f"Start farming error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/farm/stop")
async def stop_farming(request: FarmStopRequest):
    """Stop farming."""
    try:
        if request.bot_name:
            db.update_bot_status(request.bot_name, "idle")
        else:
            # Stop all bots
            bots = db.get_all_bots(status="active")
            for bot in bots:
                db.update_bot_status(bot.name, "idle")
        
        return {"status": "success", "message": "Farming stopped"}
    except Exception as e:
        logger.error(f"Stop farming error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ===== STATS ENDPOINTS =====
@app.get("/api/stats")
async def get_stats():
    """Get system statistics."""
    try:
        stats = db.get_stats()
        return stats
    except Exception as e:
        logger.error(f"Get stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ===== ENTRY POINT =====
if __name__ == "__main__":
    import uvicorn
    logger.info("🔥 FIXO DEV — Guild Glory Bot")
    logger.info(f"📡 API Server: http://{config.API_HOST}:{config.API_PORT}")
    logger.info(f"🌍 Region: {config.GAME_REGION}")
    logger.info(f"🇱🇰 Sri Lanka Optimized: True")
    
    uvicorn.run(
        "main:app",
        host=config.API_HOST,
        port=config.API_PORT,
        reload=True
    )
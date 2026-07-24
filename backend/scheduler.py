"""
FIXO DEV — Guild Glory Bot
Auto-Scheduler
"""

import asyncio
import logging
from typing import Optional
from database import DatabaseManager
from engine import GloryFarmingEngine
from models import Guild, Bot

logger = logging.getLogger(__name__)

class GuildScheduler:
    """
    Automatically schedules glory farming for all active guilds.
    """

    def __init__(self, db: DatabaseManager, engine: GloryFarmingEngine, config):
        self.db = db
        self.engine = engine
        self.config = config
        self.running = False
        self._task: Optional[asyncio.Task] = None
        
    async def start(self):
        """Start the scheduler loop."""
        self.running = True
        self._task = asyncio.create_task(self._schedule_loop())
        logger.info("FIXO Scheduler started")
        
    async def _schedule_loop(self):
        """Main scheduling loop."""
        interval = self.config.GLORY_INTERVAL_SECONDS
        
        while self.running:
            try:
                guilds = self.db.get_pending_guilds(limit=200)
                bots = self.db.get_all_bots(status="idle")
                
                if not bots:
                    logger.warning("No bots available. Waiting...")
                    await asyncio.sleep(10)
                    continue
                
                for guild in guilds:
                    if guild.status != "active":
                        continue
                        
                    available_bot = None
                    for bot in bots:
                        if len(bot.assigned_guilds) < bot.max_guilds:
                            available_bot = bot
                            break
                    
                    if not available_bot:
                        logger.warning("All bots at capacity")
                        break
                    
                    self.db.assign_bot_to_guild(guild.uid, available_bot.name)
                    available_bot.assigned_guilds.append(guild.uid)
                    await self.engine.queue_guild_for_farming(guild, available_bot)
                
                await asyncio.sleep(interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
                await asyncio.sleep(5)
    
    async def stop(self):
        """Stop the scheduler."""
        self.running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("FIXO Scheduler stopped")
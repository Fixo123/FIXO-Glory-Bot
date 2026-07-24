"""
FIXO DEV — Auto-Scheduler
"""

import asyncio
import logging
from database import DatabaseManager
from engine import GloryFarmingEngine
from config import config

logger = logging.getLogger(__name__)

class GuildScheduler:
    def __init__(self, db: DatabaseManager, engine: GloryFarmingEngine, config):
        self.db = db
        self.engine = engine
        self.config = config
        self.running = False
        self._task = None

    async def start(self):
        self.running = True
        self._task = asyncio.create_task(self._schedule_loop())
        logger.info("Scheduler started")

    async def _schedule_loop(self):
        while self.running:
            try:
                guilds = self.db.get_pending_guilds(limit=200)
                
                for guild in guilds:
                    if guild.status != "active":
                        continue
                    
                    # Get assigned bot or auto-assign
                    bot_name = guild.bot_assigned
                    if not bot_name:
                        bot_name = await self.engine.assign_bot_to_guild(guild.uid)
                        if bot_name:
                            self.db.assign_bot_to_guild(guild.uid, bot_name)
                    
                    if bot_name:
                        await self.engine.queue_guild_for_farming(guild, bot_name)
                
                await asyncio.sleep(self.config.GLORY_INTERVAL_SECONDS)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
                await asyncio.sleep(5)

    async def stop(self):
        self.running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Scheduler stopped")
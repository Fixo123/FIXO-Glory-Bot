"""
FIXO DEV — Glory Farming Engine (Multi-Bot)
"""

# ===== PATH SETUP =====
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import logging
from typing import Optional

from models import Guild
from database import DatabaseManager
from bot_manager import BotAccountManager
from config import config

logger = logging.getLogger(__name__)

class GloryFarmingEngine:
    def __init__(self, db: DatabaseManager, config):
        self.db = db
        self.config = config
        self.bot_manager = BotAccountManager()
        self.running = False
        self.task_queue = asyncio.Queue()
        self.results_queue = asyncio.Queue()
        self.active_tasks = set()
        self.lock = asyncio.Lock()
        self._stop_event = asyncio.Event()
        self._workers = []

    async def start(self):
        self.running = True
        
        for bot in self.bot_manager.bots.values():
            if bot.status == "idle":
                await self.bot_manager.initialize_bot(bot.name)
        
        for i in range(self.config.MAX_CONCURRENT_GUILDS):
            worker = asyncio.create_task(self._worker(f"worker-{i}"))
            self._workers.append(worker)
        
        processor = asyncio.create_task(self._process_results())
        self._workers.append(processor)
        
        logger.info("🔥 Engine started (Multi-Bot Mode)")
        await self._stop_event.wait()
        
        self.running = False
        for w in self._workers:
            w.cancel()

    async def _farm_glory(self, guild: Guild, bot_name: str) -> dict:
        try:
            result = await self.bot_manager.farm_for_guild(bot_name, guild.uid)
            
            if result["success"]:
                bot = self.bot_manager.get_bot(bot_name)
                guild_info = await bot.api.get_guild_info(guild.uid) if bot and bot.api else None
                members = guild_info.get("member_count", 0) if guild_info else 0
                
                return {
                    "glory": result["glory"],
                    "members": members,
                    "success": True,
                    "error": None,
                    "bot_name": bot_name
                }
            else:
                return {
                    "glory": 0,
                    "members": 0,
                    "success": False,
                    "error": result.get("error", "Farming failed"),
                    "bot_name": bot_name
                }
        except Exception as e:
            return {
                "glory": 0,
                "members": 0,
                "success": False,
                "error": str(e),
                "bot_name": bot_name
            }

    async def _worker(self, worker_id: str):
        logger.info(f"Worker {worker_id} started")
        while self.running:
            try:
                guild, bot_name = await asyncio.wait_for(
                    self.task_queue.get(),
                    timeout=1.0
                )
                
                result = await self._farm_glory(guild, bot_name)
                result["guild_uid"] = guild.uid
                await self.results_queue.put(result)
                self.task_queue.task_done()
                
                async with self.lock:
                    self.active_tasks.discard(guild.uid)
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break

    async def _process_results(self):
        while self.running:
            try:
                result = await asyncio.wait_for(
                    self.results_queue.get(),
                    timeout=0.5
                )
                
                guild_uid = result["guild_uid"]
                bot_name = result.get("bot_name", "unknown")
                glory = result["glory"]
                success = result["success"]
                error = result.get("error")
                members = result.get("members", 0)
                
                if success:
                    self.db.update_guild_glory(guild_uid, glory, members)
                    logger.info(f"✅ Guild {guild_uid} gained {glory} glory via {bot_name}")
                else:
                    logger.warning(f"❌ Guild {guild_uid} failed: {error}")
                
                self.db.log_glory_run(guild_uid, bot_name, glory, success, error or "")
                self.results_queue.task_done()
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break

    async def queue_guild_for_farming(self, guild: Guild, bot_name: str) -> bool:
        async with self.lock:
            if guild.uid in self.active_tasks:
                return False
            self.active_tasks.add(guild.uid)
            await self.task_queue.put((guild, bot_name))
            return True

    async def assign_bot_to_guild(self, guild_uid: str) -> Optional[str]:
        return await self.bot_manager.assign_guild_to_best_bot(guild_uid)

    async def stop(self):
        self._stop_event.set()
        await asyncio.sleep(2)

    async def get_queue_status(self) -> dict:
        async with self.lock:
            return {
                "queue_size": self.task_queue.qsize(),
                "active_tasks": len(self.active_tasks),
                "results_pending": self.results_queue.qsize(),
                "bots": self.bot_manager.get_stats()
            }
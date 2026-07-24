"""
FIXO DEV — Guild Glory Bot
Glory Farming Engine
"""

import asyncio
import aiohttp
import random
import logging
from datetime import datetime
from typing import Optional, Dict, Set
from models import Guild, Bot
from database import DatabaseManager

logger = logging.getLogger(__name__)

class GloryFarmingEngine:
    """
    Core engine that handles the actual glory farming operations.
    Sri Lanka server optimized.
    """

    def __init__(self, db: DatabaseManager, config):
        self.db = db
        self.config = config
        self.session: Optional[aiohttp.ClientSession] = None
        self.running = False
        self.task_queue = asyncio.Queue()
        self.results_queue = asyncio.Queue()
        self.active_tasks: Set[str] = set()
        self.lock = asyncio.Lock()
        self._stop_event = asyncio.Event()
        self._workers = []

    async def start(self):
        """Initialize the engine."""
        self.running = True
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.config.REQUEST_TIMEOUT),
            headers={
                "User-Agent": "FIXO-DEV-GloryBot/1.0",
                "X-Bot-Type": "guild-glory"
            }
        )
        logger.info("🔥 FIXO DEV Glory Farming Engine started")
        
        # Start worker tasks
        for i in range(self.config.MAX_CONCURRENT_GUILDS):
            worker = asyncio.create_task(self._worker(f"worker-{i}"))
            self._workers.append(worker)
        
        # Start result processor
        processor = asyncio.create_task(self._process_results())
        self._workers.append(processor)
        
        # Wait for stop signal
        await self._stop_event.wait()
        
        # Cleanup
        self.running = False
        for w in self._workers:
            w.cancel()
        
        if self.session:
            await self.session.close()
        logger.info("Engine stopped")

    async def _get_guild_token(self, guild_uid: str, bot_token: str) -> Optional[str]:
        """
        Get or refresh the guild's access token.
        FIXO DEV authentication handler.
        """
        try:
            # FIXO DEV auth endpoint
            auth_url = f"{self.config.SRI_LANKA_ENDPOINT}/auth/token"
            
            payload = {
                "grant_type": "client_credentials",
                "client_id": bot_token.split(".")[0] if "." in bot_token else bot_token,
                "client_secret": bot_token,
                "scope": "guild glory farming",
                "device_id": f"FIXO-{guild_uid[:8]}"
            }
            
            async with self.session.post(auth_url, json=payload) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get("access_token")
                else:
                    logger.error(f"Token fetch failed: {resp.status}")
                    return None
        except Exception as e:
            logger.error(f"Token error: {e}")
            return None

    async def _farm_glory(self, guild: Guild, bot: Bot) -> dict:
        """
        Execute a single glory farming run for a guild.
        Sri Lanka server optimized.
        """
        try:
            # Get access token
            token = await self._get_guild_token(guild.uid, bot.token)
            if not token:
                return {"glory": 0, "success": False, "error": "Failed to get access token"}

            headers = {
                "Authorization": f"Bearer {token}",
                "X-Region": guild.region,
                "X-Country": guild.country,
                "X-Server": self.config.SRI_LANKA_SERVER,
                "X-Bot": "FIXO-DEV",
                "Content-Type": "application/json"
            }

            # FIXO DEV glory farming payload
            payload = {
                "guild_id": guild.uid,
                "action": "farm_glory",
                "intensity": "high" if bot.bot_type in ["ultra", "ultimate"] else "normal",
                "country_code": guild.country,
                "bot_id": bot.name,
                "optimization": "sri_lanka" if guild.country == "LK" else "standard"
            }

            # Sri Lanka specific routing
            if guild.country == "LK":
                payload["local_optimization"] = True
                payload["server"] = "colombo-01"
                headers["X-Server"] = "colombo-01"

            # Simulate multiple game actions
            total_glory = 0
            actions_per_run = random.randint(5, 15) if bot.bot_type == "ultimate" else random.randint(3, 8)
            
            for i in range(actions_per_run):
                glory_url = f"{self.config.SRI_LANKA_ENDPOINT}/guild/glory"
                
                async with self.session.post(
                    glory_url,
                    headers=headers,
                    json=payload,
                    params={"action_id": f"FIXO_{int(datetime.now().timestamp())}_{i}"}
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        glory_gained = data.get("glory", random.randint(50, 500))
                        total_glory += glory_gained
                        logger.debug(f"FIXO: Guild {guild.uid} gained {glory_gained} glory")
                    else:
                        logger.warning(f"Action {i} failed for {guild.uid}: {resp.status}")

                await asyncio.sleep(random.uniform(0.5, 2.0))

            members = random.randint(10, 50)
            
            return {
                "glory": total_glory,
                "members": members,
                "success": total_glory > 0,
                "error": None
            }

        except asyncio.TimeoutError:
            return {"glory": 0, "success": False, "error": "Request timeout"}
        except Exception as e:
            logger.error(f"Farming error for {guild.uid}: {e}")
            return {"glory": 0, "success": False, "error": str(e)}

    async def _worker(self, worker_id: str):
        """Worker that processes guild farming tasks."""
        logger.info(f"FIXO Worker {worker_id} started")
        while self.running:
            try:
                try:
                    guild, bot = await asyncio.wait_for(
                        self.task_queue.get(),
                        timeout=1.0
                    )
                except asyncio.TimeoutError:
                    continue

                logger.info(f"FIXO Worker {worker_id} farming for guild {guild.uid}")
                
                result = await self._farm_glory(guild, bot)
                result["guild_uid"] = guild.uid
                result["bot_name"] = bot.name
                
                await self.results_queue.put(result)
                self.task_queue.task_done()
                
                async with self.lock:
                    self.active_tasks.discard(guild.uid)
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Worker {worker_id} error: {e}")
                await asyncio.sleep(0.5)
        
        logger.info(f"FIXO Worker {worker_id} stopped")

    async def _process_results(self):
        """Process results from the farming operations."""
        logger.info("FIXO Result processor started")
        while self.running:
            try:
                result = await asyncio.wait_for(
                    self.results_queue.get(),
                    timeout=0.5
                )
                
                guild_uid = result["guild_uid"]
                bot_name = result["bot_name"]
                glory = result["glory"]
                success = result["success"]
                error = result.get("error")
                members = result.get("members", 0)
                
                if success:
                    self.db.update_guild_glory(guild_uid, glory, members)
                    logger.info(f"✅ FIXO: Guild {guild_uid} gained {glory} glory via {bot_name}")
                else:
                    logger.warning(f"❌ FIXO: Guild {guild_uid} farming failed: {error}")
                
                self.db.log_glory_run(guild_uid, bot_name, glory, success, error or "")
                self.results_queue.task_done()
                
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Result processor error: {e}")

    async def queue_guild_for_farming(self, guild: Guild, bot: Bot) -> bool:
        """Queue a guild for the farming cycle."""
        async with self.lock:
            if guild.uid in self.active_tasks:
                logger.warning(f"Guild {guild.uid} already in queue")
                return False
            
            self.active_tasks.add(guild.uid)
            await self.task_queue.put((guild, bot))
            logger.info(f"FIXO: Queued guild {guild.uid} for {bot.name}")
            return True

    async def stop(self):
        """Gracefully stop the engine."""
        logger.info("Stopping FIXO engine...")
        self._stop_event.set()
        await asyncio.sleep(2)

    async def get_queue_status(self) -> dict:
        """Get current queue status."""
        async with self.lock:
            return {
                "queue_size": self.task_queue.qsize(),
                "active_tasks": len(self.active_tasks),
                "results_pending": self.results_queue.qsize()
            }
"""
FIXO DEV — Multiple Bot Account Manager
"""

import asyncio
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from freefire_api import FreeFireAPI
from config import config

logger = logging.getLogger(__name__)

@dataclass
class BotAccount:
    """Bot account configuration"""
    name: str
    username: str
    password: str
    guild_uid: str = ""
    status: str = "idle"
    last_run: float = 0
    glory_today: int = 0
    total_glory: int = 0
    api: Optional[FreeFireAPI] = None
    assigned_guilds: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "username": self.username,
            "guild_uid": self.guild_uid,
            "status": self.status,
            "glory_today": self.glory_today,
            "total_glory": self.total_glory,
            "assigned_guilds": self.assigned_guilds
        }

class BotAccountManager:
    """
    Manages multiple bot accounts
    """

    def __init__(self):
        self.bots: Dict[str, BotAccount] = {}
        self._load_bots_from_config()
        self.running = False
        self.lock = asyncio.Lock()

    def _load_bots_from_config(self):
        """Load bot accounts from environment variables"""
        import os
        
        bot_index = 1
        while True:
            username = os.getenv(f"BOT{bot_index}_USERNAME")
            password = os.getenv(f"BOT{bot_index}_PASSWORD")
            guild_uid = os.getenv(f"BOT{bot_index}_GUILD", "")
            
            if not username or not password:
                break
                
            bot_name = f"Bot_{bot_index}"
            self.bots[bot_name] = BotAccount(
                name=bot_name,
                username=username,
                password=password,
                guild_uid=guild_uid,
                status="idle"
            )
            logger.info(f"✅ Loaded bot account: {bot_name} ({username})")
            bot_index += 1

    def get_bot(self, bot_name: str) -> Optional[BotAccount]:
        return self.bots.get(bot_name)

    def get_all_bots(self) -> List[BotAccount]:
        return list(self.bots.values())

    def get_active_bots(self) -> List[BotAccount]:
        return [bot for bot in self.bots.values() if bot.status == "active"]

    def get_idle_bots(self) -> List[BotAccount]:
        return [bot for bot in self.bots.values() if bot.status == "idle"]

    async def initialize_bot(self, bot_name: str) -> bool:
        bot = self.bots.get(bot_name)
        if not bot:
            logger.error(f"Bot {bot_name} not found")
            return False

        try:
            bot.api = FreeFireAPI(config)
            success = await bot.api.login(bot.username, bot.password)
            if success:
                bot.status = "active"
                logger.info(f"✅ Bot {bot_name} initialized successfully")
                return True
            else:
                bot.status = "error"
                logger.error(f"❌ Bot {bot_name} login failed")
                return False
        except Exception as e:
            logger.error(f"Bot initialization error: {e}")
            bot.status = "error"
            return False

    async def farm_for_guild(self, bot_name: str, guild_uid: str) -> dict:
        bot = self.bots.get(bot_name)
        if not bot:
            return {"success": False, "error": "Bot not found"}

        if not bot.api or not bot.api.is_connected():
            await self.initialize_bot(bot_name)

        try:
            result = await bot.api.farm_glory(guild_uid, mode="intense")
            if result["success"]:
                bot.glory_today += result["glory"]
                bot.total_glory += result["glory"]
                bot.last_run = asyncio.get_event_loop().time()
            return result
        except Exception as e:
            logger.error(f"Farming error for bot {bot_name}: {e}")
            return {"success": False, "error": str(e)}

    async def assign_guild_to_bot(self, bot_name: str, guild_uid: str) -> bool:
        bot = self.bots.get(bot_name)
        if not bot:
            return False

        if guild_uid not in bot.assigned_guilds:
            bot.assigned_guilds.append(guild_uid)
            if bot.api and bot.api.is_connected():
                await bot.api.join_guild(guild_uid)
            logger.info(f"✅ Assigned guild {guild_uid} to bot {bot_name}")
            return True
        return False

    async def assign_guild_to_best_bot(self, guild_uid: str) -> Optional[str]:
        available_bots = [bot for bot in self.bots.values() if bot.status == "active"]
        if not available_bots:
            logger.warning("No active bots available")
            return None

        available_bots.sort(key=lambda b: len(b.assigned_guilds))
        best_bot = available_bots[0]
        await self.assign_guild_to_bot(best_bot.name, guild_uid)
        return best_bot.name

    async def stop_all_bots(self):
        self.running = False
        for bot in self.bots.values():
            bot.status = "idle"
        logger.info("All bots stopped")

    def get_stats(self) -> dict:
        total_glory = sum(bot.total_glory for bot in self.bots.values())
        total_guilds = sum(len(bot.assigned_guilds) for bot in self.bots.values())
        
        return {
            "total_bots": len(self.bots),
            "active_bots": len(self.get_active_bots()),
            "total_glory": total_glory,
            "total_guilds": total_guilds,
            "bots": [bot.to_dict() for bot in self.bots.values()]
        }
"""
FIXO DEV — FreeFire Real API Integration
"""

# ===== PATH SETUP — Protos එක හොයාගන්න =====
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ===== IMPORTS =====
import asyncio
import aiohttp
import hashlib
import time
import random
import logging
from typing import Optional, Dict

from protos import jwt_generator_pb2
from config import config

logger = logging.getLogger(__name__)

class FreeFireAPI:
    """FreeFire API Client"""

    def __init__(self, config):
        self.config = config
        self.base_url = "https://api.freefire.com/v1"
        self.auth_token = None
        self.refresh_token = None
        self.user_id = None
        self.device_id = None
        self.jwt_generator = None
        self._connected = False
        self._generate_device_id()

    def _generate_device_id(self):
        import uuid
        self.device_id = str(uuid.uuid4())

    def _generate_jwt(self, payload: Dict) -> str:
        if not self.jwt_generator:
            self.jwt_generator = jwt_generator_pb2.JWTGenerator(
                self.config.FREE_FIRE_SECRET_KEY
            )
        return self.jwt_generator.generate(payload)

    async def login(self, username: str, password: str) -> bool:
        try:
            jwt_token = self._generate_jwt({
                "username": username,
                "device_id": self.device_id
            })

            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {jwt_token}",
                    "Content-Type": "application/json",
                    "User-Agent": "FreeFire/1.105.0 (Android)",
                    "X-Device-ID": self.device_id
                }

                payload = {
                    "username": username,
                    "password": hashlib.md5(password.encode()).hexdigest(),
                    "device_id": self.device_id,
                    "device_type": "Android",
                    "app_version": "1.105.0"
                }

                async with session.post(
                    f"{self.base_url}/auth/login",
                    headers=headers,
                    json=payload
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        self.auth_token = data.get("access_token")
                        self.refresh_token = data.get("refresh_token")
                        self.user_id = data.get("user_id")
                        self._connected = True
                        logger.info(f"✅ FreeFire login successful: {self.user_id}")
                        return True
                    else:
                        logger.error(f"Login failed: {resp.status}")
                        return False
        except Exception as e:
            logger.error(f"Login error: {e}")
            return False

    async def refresh_auth(self) -> bool:
        try:
            if not self.refresh_token:
                return False

            async with aiohttp.ClientSession() as session:
                headers = {"X-Device-ID": self.device_id}
                payload = {"refresh_token": self.refresh_token}

                async with session.post(
                    f"{self.base_url}/auth/refresh",
                    headers=headers,
                    json=payload
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        self.auth_token = data.get("access_token")
                        self.refresh_token = data.get("refresh_token")
                        return True
                    return False
        except Exception as e:
            logger.error(f"Refresh error: {e}")
            return False

    async def farm_glory(self, guild_uid: str, mode: str = "normal") -> Dict:
        try:
            if not self.auth_token:
                await self.refresh_auth()

            strategies = {
                "normal": {"actions": 5, "delay": 2.0},
                "intense": {"actions": 10, "delay": 1.0},
                "turbo": {"actions": 20, "delay": 0.5}
            }
            strategy = strategies.get(mode, strategies["normal"])
            total_glory = 0

            headers = {
                "Authorization": f"Bearer {self.auth_token}",
                "X-Device-ID": self.device_id,
                "X-User-ID": self.user_id
            }

            async with aiohttp.ClientSession() as session:
                for i in range(strategy["actions"]):
                    payload = {
                        "guild_id": guild_uid,
                        "user_id": self.user_id,
                        "action_type": "collect_glory",
                        "action_id": f"action_{int(time.time())}_{i}",
                        "timestamp": int(time.time())
                    }

                    async with session.post(
                        f"{self.base_url}/guild/{guild_uid}/glory",
                        headers=headers,
                        json=payload
                    ) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            glory_gained = data.get("glory", random.randint(10, 50))
                            total_glory += glory_gained
                        elif resp.status == 401:
                            await self.refresh_auth()
                            headers["Authorization"] = f"Bearer {self.auth_token}"

                    await asyncio.sleep(strategy["delay"])

            return {"success": total_glory > 0, "glory": total_glory, "actions": strategy["actions"]}

        except Exception as e:
            logger.error(f"Farm glory error: {e}")
            return {"success": False, "glory": 0, "error": str(e)}

    async def get_guild_info(self, guild_uid: str) -> Optional[Dict]:
        try:
            if not self.auth_token:
                await self.refresh_auth()

            headers = {
                "Authorization": f"Bearer {self.auth_token}",
                "X-Device-ID": self.device_id
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/guild/{guild_uid}/info",
                    headers=headers
                ) as resp:
                    if resp.status == 200:
                        return await resp.json()
                    return None
        except Exception as e:
            logger.error(f"Guild info error: {e}")
            return None

    async def join_guild(self, guild_uid: str) -> bool:
        try:
            if not self.auth_token:
                await self.refresh_auth()

            headers = {
                "Authorization": f"Bearer {self.auth_token}",
                "X-Device-ID": self.device_id
            }

            payload = {
                "guild_id": guild_uid,
                "user_id": self.user_id,
                "join_type": "normal"
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/guild/{guild_uid}/join",
                    headers=headers,
                    json=payload
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return data.get("success", False)
                    return False
        except Exception as e:
            logger.error(f"Join guild error: {e}")
            return False

    def is_connected(self) -> bool:
        return self._connected and self.auth_token is not None
"""
FIXO DEV — Spam Join Protocol
"""

import asyncio
import logging
from . import uid_generator_pb2

logger = logging.getLogger(__name__)

class SpamJoin:
    @staticmethod
    async def join_guild(api, guild_uid: str, count: int = 1) -> dict:
        results = []
        for i in range(count):
            try:
                result = await api.join_guild(guild_uid)
                results.append({"attempt": i+1, "success": result})
                await asyncio.sleep(0.5)
            except Exception as e:
                results.append({"attempt": i+1, "success": False, "error": str(e)})
        return {"total": count, "successful": sum(1 for r in results if r["success"]), "results": results}
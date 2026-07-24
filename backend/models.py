"""
FIXO DEV — Guild Glory Bot
Data Models
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel

# ===== PYDANTIC MODELS (API) =====

class GuildAddRequest(BaseModel):
    guild_uid: str
    country: str = "LK"
    device: str = "Android"
    guild_name: Optional[str] = None

class BotRegisterRequest(BaseModel):
    bot_name: str
    bot_token: str
    bot_type: str = "standard"
    max_guilds: int = 50

class FarmStartRequest(BaseModel):
    bot_name: str
    bot_type: str = "standard"

class FarmStopRequest(BaseModel):
    bot_name: Optional[str] = None

# ===== DATA CLASSES =====

@dataclass
class Guild:
    uid: str
    name: str = ""
    region: str = "ASIA"
    country: str = "LK"
    bot_assigned: str = ""
    status: str = "pending"
    glory: int = 0
    members: int = 0
    last_run: Optional[datetime] = None

    def to_dict(self) -> dict:
        return {
            "uid": self.uid,
            "name": self.name,
            "region": self.region,
            "country": self.country,
            "bot": self.bot_assigned,
            "status": self.status,
            "glory": self.glory,
            "members": self.members,
            "last_run": self.last_run.isoformat() if self.last_run else None
        }

@dataclass
class Bot:
    name: str
    token: str
    bot_type: str = "standard"
    status: str = "idle"
    max_guilds: int = 50
    region: str = "ASIA"
    assigned_guilds: List[str] = field(default_factory=list)

    def can_assign(self) -> bool:
        return len(self.assigned_guilds) < self.max_guilds

    def available_slots(self) -> int:
        return self.max_guilds - len(self.assigned_guilds)

@dataclass
class GloryLog:
    guild_uid: str
    bot_name: str
    glory_amount: int
    success: bool
    error_message: str = ""
    timestamp: datetime = field(default_factory=datetime.now)

# ===== RESPONSE MODELS =====

class StatsResponse(BaseModel):
    total_guilds: int
    active_guilds: int
    pending_guilds: int
    total_glory: int
    bot_count: int
    total_runs: int

class GuildResponse(BaseModel):
    uid: str
    name: str
    region: str
    country: str
    bot: str
    status: str
    glory: int
    members: int
    last_run: Optional[str]

class BotResponse(BaseModel):
    name: str
    bot_type: str
    status: str
    max_guilds: int
    assigned_count: int
    region: str
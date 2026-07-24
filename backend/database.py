"""
FIXO DEV — Guild Glory Bot
Database Manager
"""

import sqlite3
import logging
from datetime import datetime
from typing import List, Optional, Dict

# ===== FIXED IMPORT — backend.models වලින් ගන්නවා =====
from backend.models import Guild, Bot, GloryLog

logger = logging.getLogger(__name__)

# ===== DATABASE SCHEMA =====
DB_SCHEMA = """
CREATE TABLE IF NOT EXISTS guilds (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_uid TEXT UNIQUE NOT NULL,
    guild_name TEXT,
    region TEXT DEFAULT 'ASIA',
    country_code TEXT DEFAULT 'LK',
    bot_assigned TEXT,
    status TEXT DEFAULT 'pending',
    glory_points INTEGER DEFAULT 0,
    member_count INTEGER DEFAULT 0,
    last_run TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS bots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    bot_name TEXT UNIQUE NOT NULL,
    bot_token TEXT NOT NULL,
    bot_type TEXT DEFAULT 'standard',
    status TEXT DEFAULT 'idle',
    current_guild_count INTEGER DEFAULT 0,
    max_guilds INTEGER DEFAULT 50,
    region TEXT DEFAULT 'ASIA',
    last_active TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS glory_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_uid TEXT NOT NULL,
    bot_name TEXT NOT NULL,
    glory_amount INTEGER DEFAULT 0,
    run_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    success BOOLEAN DEFAULT 1,
    error_message TEXT,
    FOREIGN KEY (guild_uid) REFERENCES guilds(guild_uid)
);

CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_guilds_status ON guilds(status);
CREATE INDEX IF NOT EXISTS idx_guilds_region ON guilds(region);
CREATE INDEX IF NOT EXISTS idx_bots_status ON bots(status);
CREATE INDEX IF NOT EXISTS idx_glory_logs_guild ON glory_logs(guild_uid);
CREATE INDEX IF NOT EXISTS idx_glory_logs_timestamp ON glory_logs(run_timestamp);
"""

class DatabaseManager:
    def __init__(self, db_path: str = "guild_glory.db"):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        try:
            with self._get_connection() as conn:
                conn.executescript(DB_SCHEMA)
                conn.commit()
                logger.info(f"Database initialized at {self.db_path}")
        except Exception as e:
            logger.error(f"Database init error: {e}")
            raise

    # ===== GUILD OPERATIONS =====

    def add_guild(self, uid: str, name: str = "", country: str = "LK") -> bool:
        try:
            with self._get_connection() as conn:
                conn.execute(
                    """INSERT OR REPLACE INTO guilds 
                       (guild_uid, guild_name, country_code, status, updated_at)
                       VALUES (?, ?, ?, 'pending', CURRENT_TIMESTAMP)""",
                    (uid, name, country)
                )
                conn.commit()
                logger.info(f"Guild {uid} added to database")
                return True
        except Exception as e:
            logger.error(f"Failed to add guild {uid}: {e}")
            return False

    def get_pending_guilds(self, limit: int = 100) -> List[Guild]:
        with self._get_connection() as conn:
            rows = conn.execute(
                """SELECT guild_uid, guild_name, region, country_code, 
                          bot_assigned, status, glory_points, member_count, last_run
                   FROM guilds 
                   WHERE status IN ('pending', 'active')
                   ORDER BY created_at ASC
                   LIMIT ?""",
                (limit,)
            ).fetchall()
            
            return [
                Guild(
                    uid=row["guild_uid"],
                    name=row["guild_name"] or "",
                    region=row["region"] or "ASIA",
                    country=row["country_code"] or "LK",
                    bot_assigned=row["bot_assigned"] or "",
                    status=row["status"],
                    glory=row["glory_points"] or 0,
                    members=row["member_count"] or 0,
                    last_run=datetime.fromisoformat(row["last_run"]) if row["last_run"] else None
                )
                for row in rows
            ]

    def get_all_guilds(self) -> List[Guild]:
        with self._get_connection() as conn:
            rows = conn.execute(
                """SELECT guild_uid, guild_name, region, country_code, 
                          bot_assigned, status, glory_points, member_count, last_run
                   FROM guilds 
                   ORDER BY created_at DESC"""
            ).fetchall()
            
            return [
                Guild(
                    uid=row["guild_uid"],
                    name=row["guild_name"] or "",
                    region=row["region"] or "ASIA",
                    country=row["country_code"] or "LK",
                    bot_assigned=row["bot_assigned"] or "",
                    status=row["status"],
                    glory=row["glory_points"] or 0,
                    members=row["member_count"] or 0,
                    last_run=datetime.fromisoformat(row["last_run"]) if row["last_run"] else None
                )
                for row in rows
            ]

    def assign_bot_to_guild(self, guild_uid: str, bot_name: str) -> bool:
        try:
            with self._get_connection() as conn:
                conn.execute(
                    """UPDATE guilds 
                       SET bot_assigned = ?, status = 'active', updated_at = CURRENT_TIMESTAMP
                       WHERE guild_uid = ?""",
                    (bot_name, guild_uid)
                )
                conn.commit()
                logger.info(f"Assigned bot {bot_name} to guild {guild_uid}")
                return True
        except Exception as e:
            logger.error(f"Failed to assign bot: {e}")
            return False

    def update_guild_glory(self, guild_uid: str, glory_amount: int, members: int = 0) -> bool:
        try:
            with self._get_connection() as conn:
                conn.execute(
                    """UPDATE guilds 
                       SET glory_points = glory_points + ?,
                           member_count = ?,
                           last_run = CURRENT_TIMESTAMP,
                           updated_at = CURRENT_TIMESTAMP
                       WHERE guild_uid = ?""",
                    (glory_amount, members, guild_uid)
                )
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Failed to update glory for {guild_uid}: {e}")
            return False

    def update_guild_status(self, guild_uid: str, status: str) -> bool:
        try:
            with self._get_connection() as conn:
                conn.execute(
                    "UPDATE guilds SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE guild_uid = ?",
                    (status, guild_uid)
                )
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Failed to update status for {guild_uid}: {e}")
            return False

    # ===== BOT OPERATIONS =====

    def register_bot(self, bot_name: str, token: str, bot_type: str = "standard", max_guilds: int = 50) -> bool:
        try:
            with self._get_connection() as conn:
                conn.execute(
                    """INSERT OR REPLACE INTO bots 
                       (bot_name, bot_token, bot_type, status, max_guilds, region, created_at)
                       VALUES (?, ?, ?, 'idle', ?, 'ASIA', CURRENT_TIMESTAMP)""",
                    (bot_name, token, bot_type, max_guilds)
                )
                conn.commit()
                logger.info(f"Registered bot: {bot_name}")
                return True
        except Exception as e:
            logger.error(f"Failed to register bot: {e}")
            return False

    def get_bot(self, bot_name: str) -> Optional[Bot]:
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT bot_name, bot_token, bot_type, status, max_guilds, region FROM bots WHERE bot_name = ?",
                (bot_name,)
            ).fetchone()
            if row:
                return Bot(
                    name=row["bot_name"],
                    token=row["bot_token"],
                    bot_type=row["bot_type"],
                    status=row["status"],
                    max_guilds=row["max_guilds"],
                    region=row["region"]
                )
            return None

    def get_all_bots(self, status: Optional[str] = None) -> List[Bot]:
        query = "SELECT bot_name, bot_token, bot_type, status, max_guilds, region FROM bots"
        params = []
        if status:
            query += " WHERE status = ?"
            params.append(status)
        
        with self._get_connection() as conn:
            rows = conn.execute(query, params).fetchall()
            return [
                Bot(
                    name=row["bot_name"],
                    token=row["bot_token"],
                    bot_type=row["bot_type"],
                    status=row["status"],
                    max_guilds=row["max_guilds"],
                    region=row["region"]
                )
                for row in rows
            ]

    def update_bot_status(self, bot_name: str, status: str) -> bool:
        try:
            with self._get_connection() as conn:
                conn.execute(
                    "UPDATE bots SET status = ?, last_active = CURRENT_TIMESTAMP WHERE bot_name = ?",
                    (status, bot_name)
                )
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Failed to update bot status: {e}")
            return False

    # ===== GLORY LOGS =====

    def log_glory_run(self, guild_uid: str, bot_name: str, glory: int, success: bool, error: str = ""):
        try:
            with self._get_connection() as conn:
                conn.execute(
                    """INSERT INTO glory_logs 
                       (guild_uid, bot_name, glory_amount, success, error_message)
                       VALUES (?, ?, ?, ?, ?)""",
                    (guild_uid, bot_name, glory, 1 if success else 0, error)
                )
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to log glory run: {e}")

    def get_glory_history(self, guild_uid: str, limit: int = 50) -> List[GloryLog]:
        with self._get_connection() as conn:
            rows = conn.execute(
                """SELECT guild_uid, bot_name, glory_amount, run_timestamp, success, error_message
                   FROM glory_logs 
                   WHERE guild_uid = ?
                   ORDER BY run_timestamp DESC
                   LIMIT ?""",
                (guild_uid, limit)
            ).fetchall()
            return [
                GloryLog(
                    guild_uid=row["guild_uid"],
                    bot_name=row["bot_name"],
                    glory_amount=row["glory_amount"],
                    success=bool(row["success"]),
                    error_message=row["error_message"] or "",
                    timestamp=datetime.fromisoformat(row["run_timestamp"])
                )
                for row in rows
            ]

    # ===== STATS =====

    def get_stats(self) -> dict:
        with self._get_connection() as conn:
            total_guilds = conn.execute("SELECT COUNT(*) FROM guilds").fetchone()[0]
            active_guilds = conn.execute("SELECT COUNT(*) FROM guilds WHERE status = 'active'").fetchone()[0]
            pending_guilds = conn.execute("SELECT COUNT(*) FROM guilds WHERE status = 'pending'").fetchone()[0]
            total_glory = conn.execute("SELECT SUM(glory_points) FROM guilds").fetchone()[0] or 0
            bot_count = conn.execute("SELECT COUNT(*) FROM bots").fetchone()[0]
            total_runs = conn.execute("SELECT COUNT(*) FROM glory_logs").fetchone()[0]
            
            return {
                "total_guilds": total_guilds,
                "active_guilds": active_guilds,
                "pending_guilds": pending_guilds,
                "total_glory": total_glory,
                "bot_count": bot_count,
                "total_runs": total_runs
                }

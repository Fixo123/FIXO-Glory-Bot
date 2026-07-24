"""
FIXO DEV — Guild Glory Bot
Configuration Settings
"""

import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # API Settings
    API_HOST = os.getenv("API_HOST", "0.0.0.0")
    API_PORT = int(os.getenv("API_PORT", 8000))
    
    # Game Settings
    GAME_REGION = os.getenv("GAME_REGION", "ASIA")
    TARGET_COUNTRIES = ["LK", "IN", "BD", "PK"]
    
    # Bot Settings
    MAX_GUILDS_PER_BOT = int(os.getenv("MAX_GUILDS_PER_BOT", 50))
    GLORY_INTERVAL_SECONDS = int(os.getenv("GLORY_INTERVAL_SECONDS", 300))
    MAX_CONCURRENT_GUILDS = int(os.getenv("MAX_CONCURRENT_GUILDS", 10))
    REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", 15))
    RETRY_ATTEMPTS = int(os.getenv("RETRY_ATTEMPTS", 3))
    RETRY_DELAY = int(os.getenv("RETRY_DELAY", 2))
    
    # Database
    DB_PATH = os.getenv("DB_PATH", "guild_glory.db")
    
    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE = os.getenv("LOG_FILE", "../logs/app.log")
    
    # Sri Lanka Server Optimization
    SRI_LANKA_ENDPOINT = os.getenv("SRI_LANKA_ENDPOINT", "https://api.sg.freefire.com")
    SRI_LANKA_SERVER = os.getenv("SRI_LANKA_SERVER", "colombo-01")

config = Config()
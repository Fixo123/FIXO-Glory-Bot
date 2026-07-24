"""
FIXO DEV — UID Generator
"""

import random
import time

class UIDGenerator:
    @staticmethod
    def generate() -> str:
        timestamp = str(int(time.time() * 1000))
        random_part = str(random.randint(100000, 999999))
        return timestamp + random_part

    @staticmethod
    def validate(uid: str) -> bool:
        return len(uid) >= 10 and uid.isdigit()
"""
FIXO DEV — JWT Generator
"""

import time
import json
import base64
import hmac
import hashlib
from typing import Dict

class JWTGenerator:
    def __init__(self, secret_key: str):
        self.secret_key = secret_key

    def generate(self, payload: Dict, expires_in: int = 3600) -> str:
        header = {"alg": "HS256", "typ": "JWT"}
        jwt_payload = {
            "iat": int(time.time()),
            "exp": int(time.time()) + expires_in,
            **payload
        }

        header_b64 = base64.urlsafe_b64encode(json.dumps(header).encode()).decode().rstrip("=")
        payload_b64 = base64.urlsafe_b64encode(json.dumps(jwt_payload).encode()).decode().rstrip("=")

        signature = hmac.new(
            self.secret_key.encode(),
            f"{header_b64}.{payload_b64}".encode(),
            hashlib.sha256
        ).digest()
        signature_b64 = base64.urlsafe_b64encode(signature).decode().rstrip("=")

        return f"{header_b64}.{payload_b64}.{signature_b64}"
"""
FIXO DEV — Data Protocol
"""

class DataPacket:
    def __init__(self):
        self.type = 0
        self.payload = {}

    def to_dict(self) -> dict:
        return {"type": self.type, "payload": self.payload}

    @classmethod
    def from_dict(cls, data: dict):
        obj = cls()
        obj.type = data.get("type", 0)
        obj.payload = data.get("payload", {})
        return obj
"""
FIXO DEV — Message Protocol
"""

class Message:
    def __init__(self):
        self.type = 0
        self.data = b""
        self.timestamp = 0

    def serialize(self) -> bytes:
        import struct
        return struct.pack(">II", self.type, self.timestamp) + self.data

    @classmethod
    def deserialize(cls, data: bytes):
        obj = cls()
        if len(data) >= 8:
            import struct
            obj.type, obj.timestamp = struct.unpack(">II", data[:8])
            obj.data = data[8:]
        return obj
"""
FIXO DEV — Login Protocol
"""

class LoginRequest:
    def __init__(self):
        self.username = ""
        self.password = ""
        self.device_id = ""
        self.device_type = ""
        self.app_version = ""

    def serialize(self) -> bytes:
        data = bytearray()
        if self.username:
            data.extend(b'\x0a' + len(self.username).to_bytes(1, 'little') + self.username.encode())
        if self.password:
            data.extend(b'\x12' + len(self.password).to_bytes(1, 'little') + self.password.encode())
        if self.device_id:
            data.extend(b'\x1a' + len(self.device_id).to_bytes(1, 'little') + self.device_id.encode())
        if self.device_type:
            data.extend(b'\x22' + len(self.device_type).to_bytes(1, 'little') + self.device_type.encode())
        if self.app_version:
            data.extend(b'\x2a' + len(self.app_version).to_bytes(1, 'little') + self.app_version.encode())
        return bytes(data)

    @classmethod
    def deserialize(cls, data: bytes):
        obj = cls()
        try:
            i = 0
            while i < len(data):
                tag = data[i] >> 3
                length = data[i+1] if i+1 < len(data) else 0
                if tag == 1:
                    obj.username = data[i+2:i+2+length].decode()
                elif tag == 2:
                    obj.password = data[i+2:i+2+length].decode()
                elif tag == 3:
                    obj.device_id = data[i+2:i+2+length].decode()
                elif tag == 4:
                    obj.device_type = data[i+2:i+2+length].decode()
                elif tag == 5:
                    obj.app_version = data[i+2:i+2+length].decode()
                i += 2 + length
        except:
            pass
        return obj
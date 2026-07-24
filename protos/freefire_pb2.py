"""
FIXO DEV — FreeFire Protocol
"""

class FreeFireProtocol:
    MSG_LOGIN = 0x01
    MSG_GUILD_INFO = 0x02
    MSG_GUILD_JOIN = 0x03
    MSG_GUILD_GLORY = 0x04
    MSG_GUILD_MEMBERS = 0x05
    RESP_OK = 0x00
    RESP_ERROR = 0x01
    ACTION_COLLECT_GLORY = "collect_glory"

class GuildInfo:
    def __init__(self):
        self.guild_id = ""
        self.guild_name = ""
        self.member_count = 0
        self.glory_points = 0
        self.region = ""
        self.country = ""

    def to_dict(self) -> dict:
        return {
            "guild_id": self.guild_id,
            "guild_name": self.guild_name,
            "member_count": self.member_count,
            "glory_points": self.glory_points,
            "region": self.region,
            "country": self.country
        }
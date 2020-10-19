from pickle import loads
from typing import Any  # nosec

from redis import Redis

from lifecycle.migrate import BaseMigration
from passbook.lib.config import CONFIG


class Migration(BaseMigration):

    def __init__(self, cur: Any, con: Any):
        super().__init__(cur, con)
        self.redis = Redis(
            host=CONFIG.y("redis.host"),
            port=6379,
            db=CONFIG.y("redis.cache_db"),
            password=CONFIG.y("redis.password"),
        )

    def needs_migration(self) -> bool:
        keys = self.redis.keys(":1:outpost_*")
        for key in keys:
            value = loads(self.redis.get(key))  # nosec
            if isinstance(value, str):
                return True
        return False

    def run(self):
        keys_to_delete = self.redis.keys(":1:outpost_*")
        self.redis.delete(*keys_to_delete)

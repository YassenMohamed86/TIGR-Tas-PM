import json
from typing import Any
from app.cache.redis_client import get_redis_client
from app.config.settings import get_settings

class CacheManager:
    def __init__(self):
        self.client = get_redis_client()
        self.settings = get_settings()

    async def get(self, key: str) -> Any | None:
        data = await self.client.get(key)
        if data:
            return json.loads(data)
        return None

    async def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        if ttl is None:
            ttl = self.settings.cache_ttl_seconds
        await self.client.set(key, json.dumps(value), ex=ttl)

    async def delete(self, key: str) -> None:
        await self.client.delete(key)

    async def exists(self, key: str) -> bool:
        result = await self.client.exists(key)
        return result > 0

import redis.asyncio as redis
from src.config.settings import settings
import json
import logging

logger = logging.getLogger(__name__)

redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)

class CacheService:
    """Redis cache helper for DevFlow AI"""

    def __init__(self, client):
        self.redis = client

    async def get(self, key: str):
        val = await self.redis.get(key)
        if val:
            return json.loads(val)
        return None

    async def set(self, key: str, value, ttl: int = 300):
        await self.redis.set(key, json.dumps(value), ex=ttl)

    async def delete(self, key: str):
        await self.redis.delete(key)

    async def delete_pattern(self, pattern: str):
        keys = await self.redis.keys(pattern)
        if keys:
            await self.redis.delete(*keys)

    # ─── Session management ───
    async def set_session(self, user_id: str, data: dict, ttl: int = 86400):
        await self.set(f"session:{user_id}", data, ttl)

    async def get_session(self, user_id: str):
        return await self.get(f"session:{user_id}")

    async def delete_session(self, user_id: str):
        await self.delete(f"session:{user_id}")

    # ─── Rate limiting ───
    async def increment_rate(self, key: str, window: int = 60) -> int:
        pipe = self.redis.pipeline()
        pipe.incr(key)
        pipe.expire(key, window)
        results = await pipe.execute()
        return results[0]

    # ─── AI response caching ───
    async def cache_ai_response(self, prompt_hash: str, response: str, ttl: int = 3600):
        await self.set(f"ai_cache:{prompt_hash}", {"response": response}, ttl)

    async def get_cached_ai_response(self, prompt_hash: str):
        data = await self.get(f"ai_cache:{prompt_hash}")
        return data.get("response") if data else None

cache = CacheService(redis_client)

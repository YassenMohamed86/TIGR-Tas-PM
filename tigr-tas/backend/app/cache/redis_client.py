import redis.asyncio as redis
from app.config.settings import get_settings

settings = get_settings()

redis_pool = redis.ConnectionPool.from_url(
    str(settings.redis_url),
    max_connections=settings.redis_max_connections,
    decode_responses=True
)

def get_redis_client() -> redis.Redis:
    return redis.Redis(connection_pool=redis_pool)

async def close_redis_pool():
    await redis_pool.disconnect()

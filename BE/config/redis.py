from redis.asyncio import Redis

from BE.config.settings import REDIS_URL

redis_client = Redis.from_url(REDIS_URL, decode_responses=True)
# db/redis.py

import redis
from orbmem.core.config import load_config
from orbmem.utils.logger import get_logger
from orbmem.utils.exceptions import DatabaseError

logger = get_logger(__name__)

CONFIG = load_config()
REDIS_URL = CONFIG.db.redis_url


def get_redis_client():
    """Create and return a Redis client instance."""
    if not REDIS_URL:
        return None

    try:
        client = redis.Redis.from_url(REDIS_URL, decode_responses=True)
        logger.info("Redis connection established.")
        return client
    except Exception as e:
        logger.error(f"Redis connection failed: {e}")
        raise DatabaseError(f"Redis init error: {e}")

# engines/memory/redis_backend.py

import json
from typing import Any, Dict, Optional, List
from orbmem.db.redis import get_redis_client
from orbmem.utils.logger import get_logger

logger = get_logger(__name__)


class RedisMemoryBackend:
    """
    High-speed TTL memory using Redis.
    Best for short-term memory, active sessions, caching.
    """

    def __init__(self):
        self.client = get_redis_client()
        if self.client:
            logger.info("RedisMemoryBackend initialized.")
        else:
            logger.warning("REDIS_URL not configured. RedisBackend disabled.")

    # ---------------------------------------------------------
    # Core Operations
    # ---------------------------------------------------------
    def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None):
        if not self.client:
            return

        value_json = json.dumps(value)
        if ttl_seconds:
            self.client.setex(key, ttl_seconds, value_json)
        else:
            self.client.set(key, value_json)

        logger.info(f"[Redis] Set key '{key}'")

    def get(self, key: str) -> Optional[Any]:
        if not self.client:
            return None

        val = self.client.get(key)
        if val is None:
            return None

        return json.loads(val)

    def delete(self, key: str):
        if self.client:
            self.client.delete(key)
            logger.info(f"[Redis] Deleted key '{key}'")

    def keys(self) -> List[str]:
        if not self.client:
            return []
        return [k for k in self.client.keys("*")]

    # ---------------------------------------------------------
    # Session support via prefixing (session:<id>:key)
    # ---------------------------------------------------------
    def set_session(self, session_id: str, key: str, value: Any, ttl: Optional[int] = None):
        full_key = f"session:{session_id}:{key}"
        self.set(full_key, value, ttl)

    def get_session(self, session_id: str) -> Dict[str, Any]:
        if not self.client:
            return {}

        pattern = f"session:{session_id}:*"
        results = {}
        for key in self.client.keys(pattern):
            clean_key = key.decode().split(":", 2)[2]
            results[clean_key] = self.get(key)
        return results

    def delete_session(self, session_id: str):
        if not self.client:
            return

        pattern = f"session:{session_id}:*"
        for key in self.client.keys(pattern):
            self.client.delete(key)

        logger.info(f"[Redis] Deleted session '{session_id}'")

import json
import logging
from datetime import datetime, timedelta

import redis

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class CacheService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self._client: redis.Redis | None = None
        self._memory_cache: dict[str, tuple[str, datetime | None]] = {}

    def _connect(self) -> redis.Redis | None:
        if self._client is not None:
            return self._client
        try:
            self._client = redis.Redis.from_url(
                self.settings.redis_url,
                decode_responses=True,
                socket_connect_timeout=1,
                socket_timeout=1,
            )
            self._client.ping()
        except Exception as exc:  # pragma: no cover - Redis may be absent locally
            logger.warning("Redis unavailable, falling back to in-memory cache: %s", exc)
            self._client = None
        return self._client

    def get_json(self, key: str):
        client = self._connect()
        if client:
            payload = client.get(key)
            return json.loads(payload) if payload else None
        payload = self._memory_cache.get(key)
        if not payload:
            return None
        data, expires_at = payload
        if expires_at and expires_at < datetime.utcnow():
            self._memory_cache.pop(key, None)
            return None
        return json.loads(data)

    def set_json(self, key: str, value, ttl_seconds: int = 300) -> None:
        encoded = json.dumps(value, default=str)
        client = self._connect()
        if client:
            client.setex(key, ttl_seconds, encoded)
            return
        expires_at = datetime.utcnow() + timedelta(seconds=ttl_seconds) if ttl_seconds else None
        self._memory_cache[key] = (encoded, expires_at)

    def delete(self, key: str) -> None:
        client = self._connect()
        if client:
            client.delete(key)
        self._memory_cache.pop(key, None)

    def flush_prefix(self, prefix: str) -> None:
        client = self._connect()
        if client:
            for key in client.scan_iter(f"{prefix}*"):
                client.delete(key)
        for key in list(self._memory_cache):
            if key.startswith(prefix):
                self._memory_cache.pop(key, None)


cache_service = CacheService()

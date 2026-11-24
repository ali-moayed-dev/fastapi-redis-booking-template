"""Cache abstraction with Redis implementation and in-memory test fallback."""

import json
from typing import Any, Protocol


class CacheBackend(Protocol):
    """Minimal JSON cache interface used by domain services."""

    def get_json(self, key: str) -> Any | None: ...
    def set_json(self, key: str, value: Any, ttl_seconds: int) -> None: ...
    def delete_prefix(self, prefix: str) -> None: ...


class RedisCache:
    """Redis-backed JSON cache using prefix scan for safe invalidation."""

    def __init__(self, redis_client: Any) -> None:
        self._client = redis_client

    def get_json(self, key: str) -> Any | None:
        raw = self._client.get(key)
        return json.loads(raw) if raw is not None else None

    def set_json(self, key: str, value: Any, ttl_seconds: int) -> None:
        self._client.setex(key, ttl_seconds, json.dumps(value))

    def delete_prefix(self, prefix: str) -> None:
        keys = list(self._client.scan_iter(match=f"{prefix}*"))
        if keys:
            self._client.unlink(*keys)


class InMemoryCache:
    """Lightweight in-memory cache for local tests and offline execution."""

    def __init__(self) -> None:
        self._store: dict[str, str] = {}

    def get_json(self, key: str) -> Any | None:
        raw = self._store.get(key)
        return json.loads(raw) if raw is not None else None

    def set_json(self, key: str, value: Any, ttl_seconds: int) -> None:
        self._store[key] = json.dumps(value)

    def delete_prefix(self, prefix: str) -> None:
        for key in [k for k in self._store if k.startswith(prefix)]:
            del self._store[key]


def build_cache(redis_url: str) -> CacheBackend:
    """Create a RedisCache when reachable, falling back to InMemoryCache."""
    try:
        import redis  # type: ignore

        client = redis.Redis.from_url(redis_url, decode_responses=True)
        client.ping()
        return RedisCache(client)
    except Exception:
        return InMemoryCache()

"""Small in-memory cache used by the troubleshooting request pipeline."""

from dataclasses import dataclass
from copy import deepcopy
from threading import RLock
from time import monotonic
from typing import Any


@dataclass
class _CacheEntry:
    value: Any
    expires_at: float


class CacheService:
    """Thread-safe cache for validated troubleshooting responses."""

    def __init__(self, ttl_seconds: float = 300.0, max_size: int = 512):
        if ttl_seconds <= 0:
            raise ValueError("ttl_seconds must be greater than zero")
        if max_size <= 0:
            raise ValueError("max_size must be greater than zero")

        self._ttl_seconds = ttl_seconds
        self._max_size = max_size
        self._entries: dict[str, _CacheEntry] = {}
        self._lock = RLock()

    @staticmethod
    def normalize_key(key: str) -> str:
        """Normalize user queries so harmless casing and whitespace differ not."""
        if not isinstance(key, str):
            raise TypeError("cache keys must be strings")
        return " ".join(key.casefold().split())

    def get(self, key: str) -> Any | None:
        normalized_key = self.normalize_key(key)
        now = monotonic()

        with self._lock:
            entry = self._entries.get(normalized_key)
            if entry is None:
                return None
            if entry.expires_at <= now:
                del self._entries[normalized_key]
                return None
            return deepcopy(entry.value)

    def set(self, key: str, value: Any) -> None:
        normalized_key = self.normalize_key(key)
        now = monotonic()

        with self._lock:
            expired_keys = [
                entry_key
                for entry_key, entry in self._entries.items()
                if entry.expires_at <= now
            ]
            for entry_key in expired_keys:
                del self._entries[entry_key]
            if len(self._entries) >= self._max_size and normalized_key not in self._entries:
                oldest_key = min(
                    self._entries,
                    key=lambda entry_key: self._entries[entry_key].expires_at,
                )
                del self._entries[oldest_key]
            self._entries[normalized_key] = _CacheEntry(
                value=deepcopy(value),
                expires_at=now + self._ttl_seconds,
            )

    def clear(self) -> None:
        with self._lock:
            self._entries.clear()


cache_service = CacheService()


def get(key):
    """Return cached value for key, or None if not found."""
    return cache_service.get(key)


def set(key, value):
    """Store a value in the cache."""
    cache_service.set(key, value)


def clear():
    """Remove all cached values."""
    cache_service.clear()
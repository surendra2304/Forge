from __future__ import annotations

import hashlib
import threading
import time
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class IdempotencyRecord:
    key: str
    response_hash: str
    created_at: float


class IdempotencyStore:
    def __init__(self, ttl_seconds: float = 3600, max_items: int = 50000):
        self.ttl = ttl_seconds
        self.max_items = max_items
        self._items: dict[str, IdempotencyRecord] = {}
        self._lock = threading.RLock()

    @staticmethod
    def make_key(task_id: str, intent_hash: str) -> str:
        return hashlib.sha256(f"{task_id}:{intent_hash}".encode()).hexdigest()

    def seen(self, key: str) -> bool:
        with self._lock:
            rec = self._items.get(key)
            if rec is None:
                return False
            if time.monotonic() - rec.created_at > self.ttl:
                self._items.pop(key, None)
                return False
            return True

    def remember(self, key: str, response_hash: str) -> None:
        with self._lock:
            if len(self._items) >= self.max_items:
                oldest = min(self._items, key=lambda k: self._items[k].created_at)
                self._items.pop(oldest, None)
            self._items[key] = IdempotencyRecord(key, response_hash, time.monotonic())

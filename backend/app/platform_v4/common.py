from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from threading import RLock
from typing import Generic, TypeVar
import uuid

T = TypeVar("T")

def utcnow() -> datetime:
    return datetime.now(timezone.utc)

@dataclass(slots=True)
class Record:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=utcnow)
    updated_at: datetime = field(default_factory=utcnow)

class Registry(Generic[T]):
    """Thread-safe control-plane registry. Persistence adapters can replace this store."""
    def __init__(self) -> None:
        self._items: dict[str, T] = {}
        self._lock = RLock()

    def put(self, key: str, value: T) -> T:
        with self._lock:
            self._items[key] = value
        return value

    def get(self, key: str) -> T | None:
        with self._lock:
            return self._items.get(key)

    def delete(self, key: str) -> bool:
        with self._lock:
            return self._items.pop(key, None) is not None

    def list(self) -> list[T]:
        with self._lock:
            return list(self._items.values())

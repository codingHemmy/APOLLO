from __future__ import annotations

import threading
import time
from collections import OrderedDict
from typing import Generic, Optional, TypeVar

K = TypeVar("K")
V = TypeVar("V")


class LRUCache(Generic[K, V]):
    def __init__(self, maxsize: int = 128):
        self.maxsize = maxsize
        self._data: "OrderedDict[K, V]" = OrderedDict()
        self._lock = threading.Lock()

    def get(self, key: K) -> Optional[V]:
        with self._lock:
            if key not in self._data:
                return None
            value = self._data.pop(key)
            self._data[key] = value
            return value

    def set(self, key: K, value: V) -> None:
        with self._lock:
            if key in self._data:
                self._data.pop(key)
            elif len(self._data) >= self.maxsize:
                self._data.popitem(last=False)
            self._data[key] = value

    def __contains__(self, key: K) -> bool:
        with self._lock:
            return key in self._data

    def __getitem__(self, key: K) -> V:
        value = self.get(key)
        if value is None:
            raise KeyError(key)
        return value

    def __setitem__(self, key: K, value: V) -> None:
        self.set(key, value)


class TTLCache(Generic[K, V]):
    def __init__(self, maxsize: int = 128, ttl: int = 300):
        self.maxsize = maxsize
        self.ttl = ttl
        self._data: "OrderedDict[K, tuple[V, float]]" = OrderedDict()
        self._lock = threading.Lock()

    def get(self, key: K) -> Optional[V]:
        with self._lock:
            item = self._data.get(key)
            if not item:
                return None
            value, expires = item
            if expires < time.time():
                self._data.pop(key, None)
                return None
            self._data.pop(key)
            self._data[key] = (value, expires)
            return value

    def set(self, key: K, value: V) -> None:
        with self._lock:
            expires = time.time() + self.ttl
            if key in self._data:
                self._data.pop(key)
            elif len(self._data) >= self.maxsize:
                self._data.popitem(last=False)
            self._data[key] = (value, expires)

    def cleanup(self) -> None:
        with self._lock:
            now = time.time()
            keys = [k for k, (_, exp) in self._data.items() if exp < now]
            for key in keys:
                self._data.pop(key, None)

    def __setitem__(self, key: K, value: V) -> None:
        self.set(key, value)

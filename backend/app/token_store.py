from __future__ import annotations

import secrets
import threading
import time
from pathlib import Path
from typing import Dict, Tuple


class TokenStore:
    def __init__(self, ttl_seconds: int = 300):
        self.ttl = ttl_seconds
        self._tokens: Dict[str, Tuple[Path, float]] = {}
        self._lock = threading.Lock()

    def issue(self, path: Path) -> str:
        token = secrets.token_urlsafe(32)
        expires = time.time() + self.ttl
        with self._lock:
            self._tokens[token] = (path, expires)
        return token

    def resolve(self, token: str) -> Path | None:
        now = time.time()
        with self._lock:
            data = self._tokens.get(token)
            if not data:
                return None
            path, expires = data
            if expires < now:
                del self._tokens[token]
                return None
            return path

    def cleanup(self) -> None:
        now = time.time()
        with self._lock:
            expired = [t for t, (_, exp) in self._tokens.items() if exp < now]
            for token in expired:
                del self._tokens[token]

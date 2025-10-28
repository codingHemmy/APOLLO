from __future__ import annotations

import os
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Any, Literal


@dataclass
class Settings:
    ftp_host: str = "192.168.105.244"
    ftp_user: str = "fanuc"
    ftp_pass: str = "fanuc_ftp"
    ftp_port: int = 21
    ftp_passive: bool = True
    ftp_use_tls: bool = False
    ftp_max_connections: int = 4
    ftp_connect_timeout: int = 10
    ftp_data_timeout: int = 0
    ftp_chunk_size: int = 64 * 1024
    ftp_chunk_progress_interval: float = 0.1

    frontend_origin: str = "http://localhost:5173"
    backend_port: int = 8000
    allowed_machines: int = 50
    cache_ttl_seconds: int = 300
    content_cache_size: int = 64
    token_ttl_seconds: int = 300

    security_basic_user: str | None = None
    security_basic_pass: str | None = None

    log_level: Literal["debug", "info", "warning", "error"] = "info"

    def update(self, overrides: dict[str, Any]) -> None:
        for key, value in overrides.items():
            attr = key.lower()
            if hasattr(self, attr):
                setattr(self, attr, value)


def load_settings(overrides: dict[str, Any] | None = None) -> Settings:
    settings = Settings(
        ftp_host=os.getenv("FTP_HOST", Settings.ftp_host),
        ftp_user=os.getenv("FTP_USER", Settings.ftp_user),
        ftp_pass=os.getenv("FTP_PASS", Settings.ftp_pass),
        ftp_port=int(os.getenv("FTP_PORT", Settings.ftp_port)),
        ftp_passive=os.getenv("FTP_PASSIVE", str(Settings.ftp_passive)).lower() == "true",
        ftp_use_tls=os.getenv("FTP_USE_TLS", str(Settings.ftp_use_tls)).lower() == "true",
        ftp_max_connections=int(os.getenv("FTP_MAX_CONNECTIONS", Settings.ftp_max_connections)),
        ftp_connect_timeout=int(os.getenv("FTP_CONNECT_TIMEOUT", Settings.ftp_connect_timeout)),
        ftp_data_timeout=int(os.getenv("FTP_DATA_TIMEOUT", Settings.ftp_data_timeout)),
        ftp_chunk_size=int(os.getenv("FTP_CHUNK_SIZE", Settings.ftp_chunk_size)),
        ftp_chunk_progress_interval=float(
            os.getenv("FTP_CHUNK_PROGRESS_INTERVAL", Settings.ftp_chunk_progress_interval)
        ),
        frontend_origin=os.getenv("FRONTEND_ORIGIN", Settings.frontend_origin),
        backend_port=int(os.getenv("BACKEND_PORT", Settings.backend_port)),
        allowed_machines=int(os.getenv("ALLOWED_MACHINES", Settings.allowed_machines)),
        cache_ttl_seconds=int(os.getenv("CACHE_TTL_SECONDS", Settings.cache_ttl_seconds)),
        content_cache_size=int(os.getenv("CONTENT_CACHE_SIZE", Settings.content_cache_size)),
        token_ttl_seconds=int(os.getenv("TOKEN_TTL_SECONDS", Settings.token_ttl_seconds)),
        security_basic_user=os.getenv("SECURITY_BASIC_USER"),
        security_basic_pass=os.getenv("SECURITY_BASIC_PASS"),
        log_level=os.getenv("LOG_LEVEL", Settings.log_level),
    )
    if overrides:
        settings.update(overrides)
    return settings


@lru_cache()
def get_settings() -> Settings:
    return load_settings()


def refresh_settings(overrides: dict[str, Any] | None = None) -> Settings:
    get_settings.cache_clear()
    return load_settings(overrides)

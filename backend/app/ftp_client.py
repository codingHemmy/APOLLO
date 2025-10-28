from __future__ import annotations

import contextlib
import ftplib
import os
import queue
import threading
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import PurePosixPath
from typing import Callable, Optional

import asyncio
import logging

from .config import Settings
from .utils import TTLCache

logger = logging.getLogger(__name__)


@dataclass
class FTPFile:
    name: str
    path: str
    modified: Optional[datetime]
    size: Optional[int]
    type: str | None = None


class FTPConnection:
    def __init__(self, ftp: ftplib.FTP):
        self.ftp = ftp
        self.last_used = time.monotonic()

    def close(self) -> None:
        with contextlib.suppress(Exception):
            self.ftp.quit()


class FTPPool:
    def __init__(self, settings: Settings):
        self.settings = settings
        self._pool: "queue.Queue[FTPConnection]" = queue.Queue(maxsize=settings.ftp_max_connections)
        self._lock = threading.Lock()

    def _create_connection(self) -> FTPConnection:
        ftp_cls: type[ftplib.FTP] = ftplib.FTP_TLS if self.settings.ftp_use_tls else ftplib.FTP
        ftp = ftp_cls()
        ftp.timeout = self.settings.ftp_connect_timeout
        ftp.connect(self.settings.ftp_host, self.settings.ftp_port, timeout=self.settings.ftp_connect_timeout)
        if self.settings.ftp_use_tls and isinstance(ftp, ftplib.FTP_TLS):
            ftp.auth()
            ftp.prot_p()
        ftp.login(self.settings.ftp_user, self.settings.ftp_pass)
        ftp.set_pasv(self.settings.ftp_passive)
        ftp.sock.settimeout(self.settings.ftp_data_timeout or None)
        return FTPConnection(ftp)

    def _get_connection(self) -> FTPConnection:
        try:
            conn = self._pool.get_nowait()
        except queue.Empty:
            conn = self._create_connection()
        else:
            try:
                conn.ftp.voidcmd("NOOP")
            except Exception:
                logger.warning("ftp noop failed - recreating connection")
                conn.close()
                conn = self._create_connection()
        conn.last_used = time.monotonic()
        return conn

    def _return_connection(self, conn: FTPConnection) -> None:
        if conn is None:
            return
        try:
            self._pool.put_nowait(conn)
        except queue.Full:
            conn.close()

    def _normalize(self, *parts: str) -> str:
        return str(PurePosixPath("/").joinpath(*(p.strip("/") for p in parts if p)))

    async def list_directory(self, path: str) -> list[FTPFile]:
        path = self._normalize(path)

        def _list() -> list[FTPFile]:
            delay = 1.0
            for attempt in range(4):
                conn = self._get_connection()
                try:
                    files: list[FTPFile] = []
                    try:
                        for entry in conn.ftp.mlsd(path):
                            name, facts = entry
                            if name in {".", ".."}:
                                continue
                            modified = None
                            if "modify" in facts:
                                try:
                                    modified = datetime.strptime(facts["modify"], "%Y%m%d%H%M%S")
                                except ValueError:
                                    modified = None
                            size = None
                            if "size" in facts:
                                with contextlib.suppress(ValueError):
                                    size = int(facts["size"])
                            ftype = facts.get("type")
                            files.append(
                                FTPFile(
                                    name=name,
                                    path=self._normalize(path, name),
                                    modified=modified,
                                    size=size,
                                    type=ftype,
                                )
                            )
                        return files
                    except Exception as exc:  # fallback to NLST
                        logger.warning("mlsd failed, fallback to nlst", exc_info=exc)
                        names = conn.ftp.nlst(path)
                        for name in names:
                            name_only = os.path.basename(name)
                            modified = None
                            size = None
                            with contextlib.suppress(Exception):
                                mdtm_resp = conn.ftp.sendcmd(f"MDTM {self._normalize(path, name_only)}")
                                if mdtm_resp.startswith("213"):
                                    modified = datetime.strptime(mdtm_resp.split()[1], "%Y%m%d%H%M%S")
                            with contextlib.suppress(Exception):
                                size = conn.ftp.size(self._normalize(path, name_only))
                            files.append(
                                FTPFile(
                                    name=name_only,
                                    path=self._normalize(path, name_only),
                                    modified=modified,
                                    size=size,
                                    type=None,
                                )
                            )
                        return files
                except (ftplib.error_temp, ftplib.error_reply, ftplib.error_proto) as exc:
                    logger.error("ftp list failed", exc_info=exc)
                    time.sleep(delay)
                    delay *= 2
                finally:
                    self._return_connection(conn)
            raise RuntimeError("FTP list retries exhausted")

        return await asyncio.to_thread(_list)

    async def download_file(
        self,
        remote_path: str,
        local_path: str,
        progress_cb: Optional[Callable[[int], None]] = None,
    ) -> None:
        remote_path = self._normalize(remote_path)

        def _download() -> None:
            delay = 1.0
            for attempt in range(4):
                conn = self._get_connection()
                try:
                    with open(local_path, "wb") as fp:
                        total = 0

                        def _write(data: bytes) -> None:
                            nonlocal total
                            fp.write(data)
                            total += len(data)
                            if progress_cb:
                                progress_cb(total)

                        conn.ftp.retrbinary(f"RETR {remote_path}", _write, blocksize=self.settings.ftp_chunk_size)
                    return
                except (ftplib.error_temp, ftplib.error_reply, ftplib.error_proto) as exc:
                    logger.error("ftp download failed", exc_info=exc)
                    time.sleep(delay)
                    delay *= 2
                finally:
                    self._return_connection(conn)
            raise RuntimeError("FTP download retries exhausted")

        await asyncio.to_thread(_download)

    async def health_check(self) -> bool:
        def _ping() -> bool:
            try:
                conn = self._get_connection()
            except Exception as exc:  # pragma: no cover - defensive
                logger.error("failed to get ftp connection", exc_info=exc)
                return False
            try:
                conn.ftp.voidcmd("NOOP")
                return True
            except Exception:
                return False
            finally:
                self._return_connection(conn)

        return await asyncio.to_thread(_ping)


class DirectoryCache:
    def __init__(self, ttl: int):
        self.cache = TTLCache(maxsize=128, ttl=ttl)
        self._lock = threading.Lock()

    def get(self, key: str) -> list[FTPFile] | None:
        with self._lock:
            return self.cache.get(key)

    def set(self, key: str, value: list[FTPFile]) -> None:
        with self._lock:
            self.cache[key] = value

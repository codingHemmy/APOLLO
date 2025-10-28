from __future__ import annotations

import asyncio
import re
import tempfile
from collections.abc import Callable, Iterable
from datetime import datetime
from pathlib import Path

from .analysis import AnalyzedPoint, extract_value_from_file, parse_date
from .ftp_client import DirectoryCache, FTPFile, FTPPool

DAY_REGEX = re.compile(r"^\d{2}-\d{2}-\d{2}$")


class AnalysisService:
    def __init__(self, ftp_pool: FTPPool, cache: DirectoryCache, token_store, settings):
        self.ftp_pool = ftp_pool
        self.cache = cache
        self.token_store = token_store
        self.settings = settings

    async def list_days(self, machine: int) -> list[FTPFile]:
        base = self._machine_root(machine)
        cached = self.cache.get(base)
        if cached is not None:
            return cached
        entries = await self.ftp_pool.list_directory(base)
        folders = [entry for entry in entries if entry.type == "dir" or DAY_REGEX.match(entry.name or "")]
        folders.sort(key=lambda f: f.modified or datetime.min)
        self.cache.set(base, folders)
        return folders

    def _machine_root(self, machine: int) -> str:
        return f"/rd/{machine:03d}/ftp"

    async def gather_files_date_range(self, machine: int, start: str, end: str) -> list[FTPFile]:
        start_dt = parse_date(start)
        end_dt = parse_date(end)
        folders = await self.list_days(machine)
        selected: list[FTPFile] = []
        for folder in folders:
            try:
                folder_date = parse_date(folder.name)
            except Exception:
                continue
            if start_dt <= folder_date <= end_dt:
                files = await self.ftp_pool.list_directory(folder.path)
                selected.extend(self._filter_dat(files))
        selected.sort(key=lambda f: f.modified or datetime.min)
        return selected

    async def gather_files_latest(self, machine: int, last_x: int) -> list[FTPFile]:
        folders = await self.list_days(machine)
        all_files: list[FTPFile] = []
        for folder in folders:
            files = await self.ftp_pool.list_directory(folder.path)
            all_files.extend(self._filter_dat(files))
        all_files.sort(key=lambda f: f.modified or datetime.min, reverse=True)
        selected = all_files[:last_x]
        selected.sort(key=lambda f: f.modified or datetime.min)
        return selected

    def _filter_dat(self, entries: Iterable[FTPFile]) -> list[FTPFile]:
        return [e for e in entries if e.name.lower().endswith(".dat")]

    async def download_and_analyze(
        self,
        files: list[FTPFile],
        keyword: str,
        progress_cb: Callable[[float, str], None] | None = None,
    ) -> tuple[list[AnalyzedPoint], float | None, dict[str, str]]:
        if not files:
            return [], None, {}
        tmp_dir = Path(tempfile.mkdtemp(prefix="apollo_"))
        total_files = len(files)
        token_map: dict[str, str] = {}
        points: list[AnalyzedPoint] = []

        async def _download_single(index: int, file: FTPFile) -> None:
            local_path = tmp_dir / file.name

            def _progress(bytes_read: int) -> None:
                if progress_cb:
                    progress_cb((index + bytes_read / max(file.size or 1, 1)) / total_files, "downloading")

            await self.ftp_pool.download_file(file.path, str(local_path), progress_cb=_progress)
            value = await extract_value_from_file(local_path, file.size, keyword)
            if progress_cb:
                progress_cb(min((index + 1) / total_files, 0.999), "extracting")
            token = self.token_store.issue(local_path)
            token_map[file.path] = token
            if value is not None:
                point = AnalyzedPoint(
                    idx=index + 1,
                    value=value,
                    label=file.name,
                    time_iso=file.modified.isoformat() if file.modified else "",
                    local_path=local_path,
                    remote_path=file.path,
                )
                points.append(point)

        await asyncio.gather(*(_download_single(idx, file) for idx, file in enumerate(files)))

        points.sort(key=lambda p: p.idx)
        mean = sum(p.value for p in points) / len(points) if points else None
        return points, mean, token_map

    async def analyze_date_range(
        self,
        machine: int,
        start_date: str,
        end_date: str,
        keyword: str,
        progress_cb: Callable[[float, str], None] | None = None,
    ) -> tuple[list[AnalyzedPoint], float | None, dict[str, str], list[FTPFile]]:
        files = await self.gather_files_date_range(machine, start_date, end_date)
        if progress_cb:
            progress_cb(0.05, "listing")
        points, mean, tokens = await self.download_and_analyze(files, keyword, progress_cb)
        return points, mean, tokens, files

    async def analyze_last_x(
        self,
        machine: int,
        last_x: int,
        keyword: str,
        progress_cb: Callable[[float, str], None] | None = None,
    ) -> tuple[list[AnalyzedPoint], float | None, dict[str, str], list[FTPFile]]:
        files = await self.gather_files_latest(machine, last_x)
        if progress_cb:
            progress_cb(0.05, "listing")
        points, mean, tokens = await self.download_and_analyze(files, keyword, progress_cb)
        return points, mean, tokens, files

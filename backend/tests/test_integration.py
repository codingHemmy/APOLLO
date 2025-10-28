from __future__ import annotations

import asyncio
import shutil
from datetime import datetime
from pathlib import Path

import pytest

from app.analysis import extract_value_from_file, estimate_machine_runtime, compute_total_hours
from app.ftp_client import FTPFile
from app.service import AnalysisService
from app.token_store import TokenStore
from app.config import Settings
from app.ftp_client import DirectoryCache
from scripts.seed_demo import seed_demo


class FakeFTPPool:
    def __init__(self, root: Path):
        self.root = root

    async def list_directory(self, path: str):
        rel = path.strip("/")
        directory = self.root / rel
        if not directory.exists():
            return []
        entries: list[FTPFile] = []
        for child in directory.iterdir():
            stat = child.stat()
            modified = datetime.fromtimestamp(stat.st_mtime)
            size = stat.st_size if child.is_file() else None
            entries.append(
                FTPFile(
                    name=child.name,
                    path=f"/{rel}/{child.name}" if rel else f"/{child.name}",
                    modified=modified,
                    size=size,
                    type="dir" if child.is_dir() else "file",
                )
            )
        return entries

    async def download_file(self, remote_path: str, local_path: str, progress_cb=None):
        src = self.root / remote_path.strip("/")
        shutil.copyfile(src, local_path)
        if progress_cb:
            progress_cb(src.stat().st_size)

    async def health_check(self) -> bool:
        return True


@pytest.fixture()
def demo_root(tmp_path: Path) -> Path:
    seed_demo(tmp_path / "ftp")
    return tmp_path / "ftp"


def test_analyze_last_x(demo_root: Path):
    pool = FakeFTPPool(demo_root)
    settings = Settings(
        ftp_host="localhost",
        ftp_user="demo",
        ftp_pass="demo",
        ftp_port=21,
        ftp_passive=True,
        ftp_use_tls=False,
        ftp_max_connections=4,
        ftp_connect_timeout=10,
        ftp_data_timeout=0,
    )
    cache = DirectoryCache(ttl=30)
    token_store = TokenStore(ttl_seconds=60)
    service = AnalysisService(pool, cache, token_store, settings)
    async def _run():
        files = await service.gather_files_latest(1, 100)
        points, mean, tokens, _ = await service.analyze_last_x(1, 10, "Durchmesser 1")
        return files, points, mean, tokens

    files, points, mean, tokens = asyncio.run(_run())
    assert len(files) >= len(points)
    if points:
        assert all(p.value is not None for p in points)
        assert mean is None or mean > 0
        token = tokens.get(points[0].remote_path)
        assert token is not None
        path = token_store.resolve(token)
        assert path is not None and path.exists()


def test_analyze_date_range(demo_root: Path):
    pool = FakeFTPPool(demo_root)
    settings = Settings(
        ftp_host="localhost",
        ftp_user="demo",
        ftp_pass="demo",
        ftp_port=21,
        ftp_passive=True,
        ftp_use_tls=False,
        ftp_max_connections=4,
        ftp_connect_timeout=10,
        ftp_data_timeout=0,
    )
    cache = DirectoryCache(ttl=30)
    token_store = TokenStore(ttl_seconds=60)
    service = AnalysisService(pool, cache, token_store, settings)
    folders = asyncio.run(service.list_days(1))
    assert folders
    start = folders[0].name
    end = folders[-1].name
    points, mean, tokens, files = asyncio.run(
        service.analyze_date_range(1, start, end, "Durchmesser 1")
    )
    total_hours = compute_total_hours(folders[0].modified, folders[-1].modified) if folders[0].modified and folders[-1].modified else 1
    runtime = estimate_machine_runtime(files, total_hours)
    assert runtime.percent >= 0
    if points:
        token = tokens.get(points[-1].remote_path)
        assert token


def test_extract_value(tmp_path: Path):
    content = "Test\nDurchmesser 1: 2,345 mm\n"
    file_path = tmp_path / "sample.DAT"
    file_path.write_text(content, encoding="utf-8")
    value = asyncio.run(extract_value_from_file(file_path, file_path.stat().st_size, "Durchmesser 1"))
    assert value == pytest.approx(2.345)

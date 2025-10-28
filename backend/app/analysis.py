from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from statistics import median
from typing import Optional

from .ftp_client import FTPFile
from .utils import LRUCache

DECIMAL_PATTERN = re.compile(r"[+-]?\s*(?:\d+[.,]\d+|[.,]\d+)")
DATE_FORMAT = "%d-%m-%y"


@dataclass
class AnalyzedPoint:
    idx: int
    value: float
    label: str
    time_iso: str
    local_path: Path
    remote_path: str


_content_cache: LRUCache[str, str] = LRUCache(maxsize=128)


def tokenize_keyword(keyword: str) -> list[str]:
    tokens = [token for token in re.findall(r"\w+", keyword, flags=re.IGNORECASE) if token]
    return tokens


def _keyword_regex(keyword: str) -> re.Pattern[str]:
    tokens = tokenize_keyword(keyword)
    if not tokens:
        raise ValueError("Keyword must contain at least one token")
    pattern = r"\b" + r"[^\w]+".join(re.escape(token) for token in tokens) + r"\b"
    return re.compile(pattern, re.IGNORECASE)


async def read_file_content(path: Path, size: int | None) -> str:
    cache_key = f"{path}:{size}"
    if cache_key in _content_cache:
        return _content_cache[cache_key]
    import asyncio

    async def _read() -> str:
        return await asyncio.to_thread(path.read_text, encoding="utf-8", errors="ignore")

    text = await _read()
    _content_cache[cache_key] = text
    return text


async def extract_value_from_file(path: Path, size: int | None, keyword: str) -> float | None:
    text = await read_file_content(path, size)
    regex = _keyword_regex(keyword)
    matches = list(regex.finditer(text))
    if not matches:
        return None
    match = matches[-1]
    snippet = text[match.end() :]
    lines = snippet.splitlines()
    search_space = "\n".join(lines[:3])
    num_match = DECIMAL_PATTERN.search(search_space)
    if not num_match:
        return None
    value = num_match.group().replace(" ", "").replace(",", ".")
    try:
        return float(value)
    except ValueError:
        return None


@dataclass
class MachineRuntimeResult:
    percent: float


def estimate_machine_runtime(files: list[FTPFile], total_hours: float) -> MachineRuntimeResult:
    if not files or total_hours <= 0:
        return MachineRuntimeResult(percent=0.0)
    durations: list[float] = []
    gaps: list[float] = []
    last_time: Optional[datetime] = None
    for file in files:
        approx = 1.0
        if file.size:
            approx = max(file.size / (1024 * 1024), 0.1)
        durations.append(approx)
        if file.modified and last_time:
            gap = (file.modified - last_time).total_seconds() / 3600
            if gap > 0:
                gaps.append(gap)
        if file.modified:
            last_time = file.modified
    if not durations:
        return MachineRuntimeResult(percent=0.0)
    durations_sorted = sorted(durations)
    trim = max(int(0.05 * len(durations_sorted)), 0)
    trimmed = durations_sorted[trim : len(durations_sorted) - trim or None]
    t_cycle = median(trimmed) if trimmed else median(durations_sorted)
    gaps_sorted = sorted(gaps)
    idx = int(len(gaps_sorted) * 0.7)
    lower_gaps = gaps_sorted[: max(idx, 1)] if gaps_sorted else [t_cycle]
    t_change = median(lower_gaps)
    deviations = [abs(d - t_cycle) for d in trimmed or durations_sorted]
    mad = median(deviations) if deviations else 0
    tol = min((mad / t_cycle) if t_cycle else 0.3, 0.3)
    error_timeout = max(3 * t_cycle, 20 / 60)

    productive_hours = 0.0
    last_mod = None
    for file, duration in zip(files, durations):
        d = duration
        if d <= (t_cycle + t_change) * (1 + tol):
            productive_hours += d
        elif d <= error_timeout:
            productive_hours += (t_cycle + t_change) * (1 + tol)
        else:
            productive_hours += min(d, t_cycle)
        if last_mod and file.modified:
            gap = (file.modified - last_mod).total_seconds() / 3600
            if gap <= t_change * (1 + tol):
                productive_hours += gap
        if file.modified:
            last_mod = file.modified

    percent = min(productive_hours / total_hours * 100, 100.0)
    return MachineRuntimeResult(percent=percent)


def parse_date(date_str: str) -> datetime:
    return datetime.strptime(date_str, DATE_FORMAT)


def compute_total_hours(start: datetime, end: datetime) -> float:
    delta = end - start
    return max(delta.total_seconds() / 3600, 0.0001)

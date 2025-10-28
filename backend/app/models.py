from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from .analysis import DATE_FORMAT, parse_date


class MachineResponse(BaseModel):
    machines: list[int]


class HealthResponse(BaseModel):
    ok: bool
    ftp: Literal["connected", "error"]


class LatestFileResponse(BaseModel):
    filename: str
    modified: datetime | None
    size: int | None
    content: str


class AnalyzeMode(BaseModel):
    mode: Literal["date", "last_x"]
    startDate: str | None = None
    endDate: str | None = None
    lastX: int | None = Field(default=None, gt=0)

    @field_validator("startDate", "endDate")
    @classmethod
    def validate_date(cls, value: str | None) -> str | None:
        if value is None:
            return value
        parse_date(value)
        return value


class AnalyzeRequest(AnalyzeMode):
    machine: int = Field(ge=1, le=50)
    keyword: str
    maxLabels: int | None = Field(default=None, ge=10, le=1000)
    tooltipThreshold: int | None = Field(default=300, ge=10, le=2000)


class AnalyzedPointModel(BaseModel):
    idx: int
    value: float
    label: str
    timeIso: str
    localPathId: str


class AnalyzeResponse(BaseModel):
    points: list[AnalyzedPointModel]
    mean: float | None
    totalFiles: int
    machineRuntimePercent: float
    ftpStatus: Literal["ok", "error"]
    latestFileName: str | None = None


class FileToken(BaseModel):
    token: str


class ConfigResponse(BaseModel):
    FTP_HOST: str
    FTP_USER: str
    FTP_PORT: int
    FTP_PASSIVE: bool
    FTP_USE_TLS: bool
    FTP_MAX_CONNECTIONS: int
    FTP_CONNECT_TIMEOUT: int
    FTP_DATA_TIMEOUT: int


class ConfigRequest(BaseModel):
    FTP_HOST: str
    FTP_USER: str
    FTP_PASS: str
    FTP_PORT: int
    FTP_PASSIVE: bool
    FTP_USE_TLS: bool
    FTP_MAX_CONNECTIONS: int
    FTP_CONNECT_TIMEOUT: int
    FTP_DATA_TIMEOUT: int

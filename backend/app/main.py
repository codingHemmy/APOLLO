from __future__ import annotations

import asyncio
import json
import tempfile
from datetime import timedelta
from pathlib import Path
from typing import AsyncGenerator

import anyio
from fastapi import Depends, FastAPI, HTTPException, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse, StreamingResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from .analysis import compute_total_hours, estimate_machine_runtime, parse_date
from .config import get_settings, refresh_settings
from .config_store import ConfigStore
from .ftp_client import DirectoryCache, FTPPool
from .logging_config import configure_logging
from .models import (
    AnalyzeRequest,
    AnalyzeResponse,
    AnalyzedPointModel,
    ConfigRequest,
    ConfigResponse,
    HealthResponse,
    LatestFileResponse,
    MachineResponse,
)
from .service import AnalysisService
from .token_store import TokenStore

security = HTTPBasic(auto_error=False)
app = FastAPI(title="Apollo FTP Analytics")
configure_logging()
settings = get_settings()
ftp_pool = FTPPool(settings)
cache = DirectoryCache(ttl=settings.cache_ttl_seconds)
token_store = TokenStore(ttl_seconds=settings.token_ttl_seconds)
service = AnalysisService(ftp_pool, cache, token_store, settings)
config_store = ConfigStore()

if settings.frontend_origin:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.frontend_origin],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


async def verify_basic_auth(credentials: HTTPBasicCredentials | None = Depends(security)) -> None:
    if settings.security_basic_user and settings.security_basic_pass:
        if credentials is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
        if (
            credentials.username != settings.security_basic_user
            or credentials.password != settings.security_basic_pass
        ):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response: Response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "SAMEORIGIN")
    response.headers.setdefault("X-XSS-Protection", "1; mode=block")
    return response


@app.get("/api/health", response_model=HealthResponse)
async def health(_: None = Depends(verify_basic_auth)) -> HealthResponse:
    ftp_ok = await ftp_pool.health_check()
    return HealthResponse(ok=True, ftp="connected" if ftp_ok else "error")


@app.get("/api/machines", response_model=MachineResponse)
async def machines(_: None = Depends(verify_basic_auth)) -> MachineResponse:
    return MachineResponse(machines=list(range(1, settings.allowed_machines + 1)))


@app.get("/api/latest", response_model=LatestFileResponse)
async def latest(machine: int, _: None = Depends(verify_basic_auth)) -> LatestFileResponse:
    await validate_machine(machine)
    files = await service.gather_files_latest(machine, 1)
    if not files:
        raise HTTPException(status_code=404, detail="No files found")
    file = files[0]
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp_path = Path(tmp.name)
    try:
        await ftp_pool.download_file(file.path, str(tmp_path))
    except Exception as exc:
        tmp_path.unlink(missing_ok=True)
        raise HTTPException(status_code=502, detail="FTP download failed") from exc
    content = tmp_path.read_text(encoding="utf-8", errors="ignore")
    tmp_path.unlink(missing_ok=True)
    return LatestFileResponse(filename=file.name, modified=file.modified, size=file.size, content=content)


async def validate_machine(machine: int) -> None:
    if machine < 1 or machine > settings.allowed_machines:
        raise HTTPException(status_code=400, detail="Invalid machine")


@app.post("/api/analyze")
async def analyze(body: AnalyzeRequest, _: None = Depends(verify_basic_auth)):
    await validate_machine(body.machine)

    queue: asyncio.Queue[str] = asyncio.Queue()
    loop = asyncio.get_running_loop()

    def emit(payload: dict) -> None:
        loop.call_soon_threadsafe(queue.put_nowait, json.dumps(payload))

    emit({"progress": 0.01, "stage": "listing"})

    async def run_analysis() -> None:
        try:
            if body.mode == "date":
                if not body.startDate or not body.endDate:
                    raise HTTPException(status_code=400, detail="startDate and endDate required")
                points, mean, tokens, files = await service.analyze_date_range(
                    body.machine,
                    body.startDate,
                    body.endDate,
                    body.keyword,
                    lambda progress, stage: emit({"progress": progress, "stage": stage}),
                )
                start_dt = parse_date(body.startDate)
                end_dt = parse_date(body.endDate) + timedelta(days=1)
                total_hours = compute_total_hours(start_dt, end_dt)
            else:
                if not body.lastX:
                    raise HTTPException(status_code=400, detail="lastX required")
                points, mean, tokens, files = await service.analyze_last_x(
                    body.machine,
                    body.lastX,
                    body.keyword,
                    lambda progress, stage: emit({"progress": progress, "stage": stage}),
                )
                if files and any(f.modified for f in files):
                    mods = [f.modified for f in files if f.modified]
                    min_time = min(mods)
                    max_time = max(mods)
                    total_hours = compute_total_hours(min_time, max_time + timedelta(minutes=1))
                else:
                    total_hours = max(len(files), 1)
            machine_runtime = estimate_machine_runtime(files, total_hours)
            points_models = [
                AnalyzedPointModel(
                    idx=p.idx,
                    value=p.value,
                    label=p.label,
                    timeIso=p.time_iso,
                    localPathId=tokens.get(p.remote_path, ""),
                )
                for p in points
            ]
            emit(
                {
                    "result": AnalyzeResponse(
                        points=points_models,
                        mean=mean,
                        totalFiles=len(files),
                        machineRuntimePercent=machine_runtime.percent,
                        ftpStatus="ok",
                        latestFileName=files[-1].name if files else None,
                    ).model_dump(),
                    "stage": "done",
                }
            )
        except HTTPException as exc:
            emit({"error": exc.detail, "status": exc.status_code})
        except Exception as exc:  # pragma: no cover - safety
            emit({"error": str(exc), "status": 500})
        finally:
            loop.call_soon_threadsafe(queue.put_nowait, "__END__")

    asyncio.create_task(run_analysis())

    async def event_generator() -> AsyncGenerator[str, None]:
        while True:
            data = await queue.get()
            if data == "__END__":
                break
            yield f"data: {data}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.get("/api/file")
async def get_file(token: str, _: None = Depends(verify_basic_auth)):
    path = token_store.resolve(token)
    if not path or not path.exists():
        raise HTTPException(status_code=404, detail="Invalid token")
    return PlainTextResponse(path.read_text(encoding="utf-8", errors="ignore"))


@app.get("/api/config", response_model=ConfigResponse)
async def get_config(_: None = Depends(verify_basic_auth)) -> ConfigResponse:
    settings_dict = {
        "FTP_HOST": settings.ftp_host,
        "FTP_USER": settings.ftp_user,
        "FTP_PORT": settings.ftp_port,
        "FTP_PASSIVE": settings.ftp_passive,
        "FTP_USE_TLS": settings.ftp_use_tls,
        "FTP_MAX_CONNECTIONS": settings.ftp_max_connections,
        "FTP_CONNECT_TIMEOUT": settings.ftp_connect_timeout,
        "FTP_DATA_TIMEOUT": settings.ftp_data_timeout,
    }
    return ConfigResponse(**settings_dict)


@app.put("/api/config")
async def update_config(payload: ConfigRequest, _: None = Depends(verify_basic_auth)) -> ConfigResponse:
    config_store.save(payload.model_dump())
    new_settings = refresh_settings(payload.model_dump())
    global settings, ftp_pool, cache, service
    settings = new_settings
    ftp_pool = FTPPool(settings)
    cache = DirectoryCache(ttl=settings.cache_ttl_seconds)
    service = AnalysisService(ftp_pool, cache, token_store, settings)
    return await get_config()

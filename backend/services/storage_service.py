import json
import asyncio
from pathlib import Path
from typing import Optional
from datetime import datetime

from config import settings
from models.schemas import (
    AppData, Application, ApplicationStatus, RejectionNote,
    ProfileUpdate, GlobalAnalysis, StatusHistoryEntry,
)
from services.user_context import current_user_id, get_user_lock


def _resolve_path() -> Path:
    uid = current_user_id.get()
    if uid:
        from services.auth_service import user_data_path
        return user_data_path(uid)
    return Path(settings.data_file_path)


def _lock():
    uid = current_user_id.get() or "__default__"
    return get_user_lock(uid)


def _load_raw() -> dict:
    path = _resolve_path()
    if not path.exists():
        return AppData().model_dump()
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_raw(data: dict) -> None:
    path = _resolve_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    data["metadata"]["last_updated"] = datetime.utcnow().isoformat() + "Z"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


async def load_data() -> AppData:
    async with _lock():
        raw = _load_raw()
        return AppData(**raw)


async def save_data(data: AppData) -> None:
    async with _lock():
        _save_raw(data.model_dump())


async def reset_data() -> AppData:
    fresh = AppData()
    async with _lock():
        _save_raw(fresh.model_dump())
    return fresh


async def get_application(app_id: str) -> Optional[Application]:
    data = await load_data()
    return next((a for a in data.applications if a.id == app_id), None)


def _append_status_history(app: Application, status: ApplicationStatus, note: str = "") -> None:
    entry = StatusHistoryEntry(status=status, note=note)
    if not app.status_history:
        app.status_history = [entry]
    elif app.status_history[-1].status != status:
        app.status_history.append(entry)


async def upsert_application(app: Application, status_note: str = "") -> AppData:
    data = await load_data()
    idx = next((i for i, a in enumerate(data.applications) if a.id == app.id), None)
    if idx is not None:
        prev = data.applications[idx]
        if prev.status != app.status:
            _append_status_history(app, app.status, status_note)
        elif not app.status_history:
            app.status_history = prev.status_history or [
                StatusHistoryEntry(status=app.status, changed_at=app.submitted_at)
            ]
        data.applications[idx] = app
    else:
        _append_status_history(app, app.status, "Application tracked")
        data.applications.insert(0, app)
    await save_data(data)
    return data


async def upsert_rejection(rejection: RejectionNote) -> AppData:
    data = await load_data()
    idx = next((i for i, r in enumerate(data.rejections) if r.application_id == rejection.application_id), None)
    if idx is not None:
        data.rejections[idx] = rejection
    else:
        data.rejections.append(rejection)
    await save_data(data)
    return data


async def add_profile_update(update: ProfileUpdate) -> AppData:
    data = await load_data()
    data.profile_update_history.insert(0, update)
    await save_data(data)
    return data


async def update_global_analysis(analysis: GlobalAnalysis) -> AppData:
    data = await load_data()
    data.global_analysis = analysis
    await save_data(data)
    return data


async def cache_live_jobs(jobs: list, fetched_at: str) -> AppData:
    data = await load_data()
    data.cached_live_jobs = jobs
    data.live_jobs_fetched_at = fetched_at
    await save_data(data)
    return data

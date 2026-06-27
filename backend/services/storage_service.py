import json
import asyncio
from pathlib import Path
from typing import Optional
from datetime import datetime

from config import settings
from models.schemas import AppData, Application, RejectionNote, ProfileUpdate, GlobalAnalysis


_lock = asyncio.Lock()


def _load_raw() -> dict:
    path = Path(settings.data_file_path)
    if not path.exists():
        return AppData().model_dump()
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_raw(data: dict) -> None:
    path = Path(settings.data_file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    data["metadata"]["last_updated"] = datetime.utcnow().isoformat() + "Z"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


async def load_data() -> AppData:
    async with _lock:
        raw = _load_raw()
        return AppData(**raw)


async def save_data(data: AppData) -> None:
    async with _lock:
        _save_raw(data.model_dump())


async def get_application(app_id: str) -> Optional[Application]:
    data = await load_data()
    return next((a for a in data.applications if a.id == app_id), None)


async def upsert_application(app: Application) -> AppData:
    data = await load_data()
    idx = next((i for i, a in enumerate(data.applications) if a.id == app.id), None)
    if idx is not None:
        data.applications[idx] = app
    else:
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

from fastapi import APIRouter, HTTPException
from datetime import datetime

from models.schemas import Application, ApplicationStatus, UpdateStatusRequest, AppData
from services import storage_service as store

router = APIRouter(prefix="/api/tracking", tags=["tracking"])


@router.get("/applications", response_model=list[Application])
async def list_applications():
    data = await store.load_data()
    return data.applications


@router.get("/applications/{app_id}", response_model=Application)
async def get_application(app_id: str):
    app = await store.get_application(app_id)
    if not app:
        raise HTTPException(404, "Application not found")
    return app


@router.put("/applications/{app_id}/status", response_model=Application)
async def update_status(app_id: str, req: UpdateStatusRequest):
    app = await store.get_application(app_id)
    if not app:
        raise HTTPException(404, "Application not found")
    app.status = req.status
    app.updated_at = datetime.utcnow().isoformat() + "Z"
    await store.upsert_application(app)
    return app


@router.delete("/applications/{app_id}")
async def delete_application(app_id: str):
    data = await store.load_data()
    data.applications = [a for a in data.applications if a.id != app_id]
    data.rejections = [r for r in data.rejections if r.application_id != app_id]
    await store.save_data(data)
    return {"message": "Deleted"}

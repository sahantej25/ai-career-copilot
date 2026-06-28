from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime

from deps.auth import bind_user_context
from models.schemas import (
    Application, ApplicationStatus, UpdateStatusRequest,
    TrackJobRequest, UpdateApplicationRequest, RejectionNote,
)
from services import storage_service as store

router = APIRouter(prefix="/api/tracking", tags=["tracking"], dependencies=[Depends(bind_user_context)])


@router.get("/applications", response_model=list[Application])
async def list_applications(
    include_archived: bool = False,
    include_rejected: bool = True,
):
    data = await store.load_data()
    apps = data.applications
    if not include_archived:
        apps = [a for a in apps if a.status != ApplicationStatus.archived]
    if not include_rejected:
        apps = [a for a in apps if a.status != ApplicationStatus.not_selected]
    return apps


@router.get("/applications/{app_id}", response_model=Application)
async def get_application(app_id: str):
    app = await store.get_application(app_id)
    if not app:
        raise HTTPException(404, "Application not found")
    return app


@router.post("/applications/track", response_model=Application)
async def track_job(req: TrackJobRequest):
    """Log a job from Discover or paste an external URL (Jobright-style)."""
    app = Application(
        company=req.company,
        role=req.role,
        job_description=req.job_description,
        match_percentage=req.match_percentage,
        matched_skills=req.matched_skills,
        missing_skills=req.missing_skills,
        status=req.status,
        apply_url=req.apply_url,
        source=req.source,
        external_job_id=req.external_job_id,
        notes=req.notes,
    )
    await store.upsert_application(app)
    return app


@router.put("/applications/{app_id}/status", response_model=Application)
async def update_status(app_id: str, req: UpdateStatusRequest):
    app = await store.get_application(app_id)
    if not app:
        raise HTTPException(404, "Application not found")
    app.status = req.status
    app.updated_at = datetime.utcnow().isoformat() + "Z"
    await store.upsert_application(app, status_note=f"Status → {req.status.value}")

    if req.status == ApplicationStatus.not_selected:
        data = await store.load_data()
        if not any(r.application_id == app_id for r in data.rejections):
            await store.upsert_rejection(
                RejectionNote(
                    application_id=app_id,
                    missing_skills=", ".join(app.missing_skills),
                    notes=app.notes or "",
                )
            )

    return app


@router.patch("/applications/{app_id}", response_model=Application)
async def patch_application(app_id: str, req: UpdateApplicationRequest):
    app = await store.get_application(app_id)
    if not app:
        raise HTTPException(404, "Application not found")
    if req.notes is not None:
        app.notes = req.notes
    if req.follow_up_at is not None:
        app.follow_up_at = req.follow_up_at
    if req.apply_url is not None:
        app.apply_url = req.apply_url
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


@router.get("/pipeline/summary")
async def pipeline_summary():
    """Jobright-style pipeline counts by stage."""
    data = await store.load_data()
    counts: dict[str, int] = {s.value: 0 for s in ApplicationStatus}
    for app in data.applications:
        counts[app.status.value] = counts.get(app.status.value, 0) + 1
    active = sum(
        counts.get(s, 0)
        for s in ("saved", "submitted", "interview", "selected")
    )
    return {"counts": counts, "active": active, "total": len(data.applications)}

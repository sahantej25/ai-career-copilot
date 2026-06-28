from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime

from deps.auth import bind_user_context
from deps.guardrails import ai_guard
from models.schemas import (
    AnalyzeRejectionRequest, AnalyzeRejectionResponse,
    RejectionNote, GlobalAnalysis, ApplicationStatus,
)
from agents.learning_agent import analyze_rejection, build_global_analysis
from services import storage_service as store
from services.openai_service import AIConfigurationError

router = APIRouter(prefix="/api/analysis", tags=["analysis"], dependencies=[Depends(bind_user_context)])


@router.post("/rejection/analyze", response_model=AnalyzeRejectionResponse, dependencies=[Depends(ai_guard)])
async def analyze_rejection_endpoint(req: AnalyzeRejectionRequest):
    data = await store.load_data()

    if not data.current_profile_state:
        raise HTTPException(400, "No profile found. Upload resume first.")

    app = next((a for a in data.applications if a.id == req.application_id), None)
    if not app:
        raise HTTPException(404, f"Application {req.application_id} not found.")

    if not any([
        req.notes.strip(),
        req.interview_experience.strip(),
        req.rejection_email.strip(),
        req.topics_struggled.strip(),
        req.missing_skills.strip(),
        req.recruiter_feedback.strip(),
    ]):
        raise HTTPException(400, "Provide at least one rejection detail field to analyze.")

    rejection = RejectionNote(
        application_id=req.application_id,
        notes=req.notes,
        interview_experience=req.interview_experience,
        rejection_email=req.rejection_email,
        topics_struggled=req.topics_struggled,
        missing_skills=req.missing_skills,
        recruiter_feedback=req.recruiter_feedback,
        analyzed_at=datetime.utcnow().isoformat() + "Z",
    )

    try:
        profile_update, updated_profile, summary = await analyze_rejection(
            data.current_profile_state, rejection, app
        )
    except AIConfigurationError:
        raise HTTPException(503, "AI rejection analysis requires OPENAI_API_KEY to be configured.")
    except Exception as e:
        raise HTTPException(500, f"Rejection analysis failed: {e}")

    rejection.summary = summary

    data.current_profile_state = updated_profile
    await store.save_data(data)
    await store.upsert_rejection(rejection)
    await store.add_profile_update(profile_update)

    app.status = ApplicationStatus.not_selected
    app.updated_at = datetime.utcnow().isoformat() + "Z"
    await store.upsert_application(app)

    return AnalyzeRejectionResponse(
        skill_changes=profile_update.changes,
        recommendations=profile_update.recommendations,
        profile_update=profile_update,
        summary=summary,
    )


@router.get("/rejection/{app_id}", response_model=RejectionNote)
async def get_rejection(app_id: str):
    data = await store.load_data()
    rej = next((r for r in data.rejections if r.application_id == app_id), None)
    if not rej:
        raise HTTPException(404, "No rejection note found for this application.")
    return rej


@router.get("/global", response_model=GlobalAnalysis)
async def get_global_analysis():
    data = await store.load_data()
    if data.global_analysis:
        return data.global_analysis
    raise HTTPException(404, "No global analysis yet. Refresh to generate.")


@router.post("/global/refresh", response_model=GlobalAnalysis, dependencies=[Depends(ai_guard)])
async def refresh_global_analysis():
    data = await store.load_data()
    if not data.rejections:
        raise HTTPException(400, "No rejections to analyze yet.")
    try:
        analysis = await build_global_analysis(data)
    except AIConfigurationError:
        raise HTTPException(503, "AI global analysis requires OPENAI_API_KEY to be configured.")
    except Exception as e:
        raise HTTPException(500, f"Global analysis failed: {e}")
    await store.update_global_analysis(analysis)
    return analysis


@router.get("/profile-history")
async def get_profile_history():
    data = await store.load_data()
    return {"history": data.profile_update_history}

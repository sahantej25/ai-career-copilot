import os
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import Response

from config import settings
from models.schemas import (
    MatchRequest, MatchResponse, GenerateResumeRequest,
    SubmitApplicationRequest, Application, AppData,
)
from agents.profile_agent import parse_resume
from agents.job_matching_agent import match_job
from agents.resume_agent import generate_tailored_resume
from services import storage_service as store

router = APIRouter(prefix="/api/apply", tags=["apply"])


async def _require_profile() -> AppData:
    data = await store.load_data()
    if not data.current_profile_state:
        raise HTTPException(400, "No candidate profile uploaded. Please upload your resume first.")
    return data


@router.post("/upload-profile")
async def upload_profile(file: UploadFile = File(...)):
    """Parse uploaded resume and store as current_profile_state."""
    content = await file.read()
    if len(content) > settings.max_file_size_mb * 1024 * 1024:
        raise HTTPException(413, f"File exceeds {settings.max_file_size_mb}MB limit.")

    try:
        profile = await parse_resume(content, file.filename or "resume.pdf")
    except Exception as e:
        raise HTTPException(422, f"Failed to parse resume: {e}")

    data = await store.load_data()
    data.current_profile_state = profile
    await store.save_data(data)
    return {"message": "Profile parsed successfully", "profile": profile}


@router.post("/match", response_model=MatchResponse)
async def match_against_profile(req: MatchRequest, data: AppData = Depends(_require_profile)):
    try:
        result = await match_job(data.current_profile_state, req.job_description)
    except Exception as e:
        raise HTTPException(500, f"Matching failed: {e}")
    return result


@router.post("/generate-resume")
async def generate_resume(req: GenerateResumeRequest, data: AppData = Depends(_require_profile)):
    try:
        pdf_bytes = await generate_tailored_resume(data.current_profile_state, req.job_description)
    except Exception as e:
        raise HTTPException(500, f"Resume generation failed: {e}")

    filename = f"resume_{req.company.replace(' ', '_') or 'tailored'}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/submit", response_model=Application)
async def submit_application(req: SubmitApplicationRequest):
    app = Application(
        company=req.company,
        role=req.role,
        job_description=req.job_description,
        match_percentage=req.match_percentage,
        matched_skills=req.matched_skills,
        missing_skills=req.missing_skills,
        resume_filename=req.resume_filename,
    )
    await store.upsert_application(app)
    return app

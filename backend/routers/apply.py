from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import Response

from deps.auth import bind_user_context
from deps.guardrails import ai_guard
from models.schemas import (
    MatchRequest, MatchResponse, GenerateResumeRequest, ResumePreviewResponse,
    SubmitApplicationRequest, Application, AppData, CandidateProfile, SaveProfileRequest,
)
from agents.profile_agent import parse_resume, extract_resume_style
from agents.job_matching_agent import match_job
from agents.resume_agent import generate_tailored_resume, build_resume_package
from services.guardrails.files import validate_upload_file
from services import storage_service as store
from services.openai_service import AIConfigurationError

router = APIRouter(prefix="/api/apply", tags=["apply"], dependencies=[Depends(bind_user_context)])

_ALLOWED_EXT = {"pdf", "docx", "doc", "txt"}
_REFERENCE_EXT = {"pdf", "docx", "doc"}


async def _require_profile() -> AppData:
    data = await store.load_data()
    if not data.current_profile_state:
        raise HTTPException(400, "No candidate profile found. Add your profile first.")
    return data


@router.get("/profile", response_model=CandidateProfile)
async def get_profile():
    data = await store.load_data()
    if not data.current_profile_state:
        raise HTTPException(404, "No candidate profile saved yet.")
    return data.current_profile_state


@router.put("/profile", response_model=CandidateProfile)
async def save_profile(req: SaveProfileRequest):
    """Save candidate details manually without AI parsing."""
    profile = req.to_profile()
    data = await store.load_data()
    data.current_profile_state = profile
    await store.save_data(data)
    return profile


@router.delete("/profile")
async def clear_profile():
    data = await store.load_data()
    data.current_profile_state = None
    await store.save_data(data)
    return {"message": "Candidate profile cleared."}


@router.post("/upload-profile", dependencies=[Depends(ai_guard)])
async def upload_profile(file: UploadFile = File(...)):
    """Parse uploaded candidate profile → store as current_profile_state."""
    content = await file.read()
    validate_upload_file(file, content, _ALLOWED_EXT)

    try:
        profile = await parse_resume(content, file.filename or "resume.pdf")
    except AIConfigurationError:
        raise HTTPException(503, "AI profile parsing requires OPENAI_API_KEY to be configured.")
    except ValueError as e:
        raise HTTPException(422, str(e))
    except Exception as e:
        raise HTTPException(422, f"Failed to parse profile: {e}")

    data = await store.load_data()
    data.current_profile_state = profile
    await store.save_data(data)
    return {"message": "Profile parsed successfully", "profile": profile}


@router.post("/upload-reference", dependencies=[Depends(ai_guard)])
async def upload_reference(file: UploadFile = File(...)):
    """Optional reference resume → extract STYLE only (never content)."""
    content = await file.read()
    validate_upload_file(file, content, _REFERENCE_EXT)

    try:
        style = await extract_resume_style(content, file.filename or "reference.pdf")
    except AIConfigurationError:
        raise HTTPException(503, "AI style extraction requires OPENAI_API_KEY to be configured.")
    except ValueError as e:
        raise HTTPException(422, str(e))
    except Exception as e:
        raise HTTPException(422, f"Failed to read reference resume: {e}")

    data = await store.load_data()
    data.resume_style = style
    data.reference_resume_loaded = True
    data.reference_resume_name = file.filename or "reference"
    await store.save_data(data)
    return {"message": "Reference resume style captured", "style": style, "name": data.reference_resume_name}


@router.delete("/reference")
async def remove_reference():
    data = await store.load_data()
    data.resume_style = None
    data.reference_resume_loaded = False
    data.reference_resume_name = ""
    await store.save_data(data)
    return {"message": "Reference resume removed; default template will be used."}


@router.post("/match", response_model=MatchResponse, dependencies=[Depends(ai_guard)])
async def match_against_profile(req: MatchRequest, data: AppData = Depends(_require_profile)):
    try:
        result = await match_job(
            data.current_profile_state, req.job_description,
            company_hint=req.company, role_hint=req.role,
        )
    except AIConfigurationError:
        raise HTTPException(503, "AI matching requires OPENAI_API_KEY to be configured.")
    except Exception as e:
        raise HTTPException(500, f"Matching failed: {e}")
    return result


@router.post("/resume-preview", response_model=ResumePreviewResponse, dependencies=[Depends(ai_guard)])
async def resume_preview(req: GenerateResumeRequest, data: AppData = Depends(_require_profile)):
    try:
        return await build_resume_package(
            data.current_profile_state,
            req.job_description,
            data.resume_style,
            match=req.match_context,
        )
    except AIConfigurationError:
        raise HTTPException(503, "AI resume preview requires OPENAI_API_KEY to be configured.")
    except Exception as e:
        raise HTTPException(500, f"Preview failed: {e}")


@router.post("/generate-resume", dependencies=[Depends(ai_guard)])
async def generate_resume(req: GenerateResumeRequest, data: AppData = Depends(_require_profile)):
    try:
        pdf_bytes = await generate_tailored_resume(
            data.current_profile_state,
            req.job_description,
            data.resume_style,
            match=req.match_context,
        )
    except AIConfigurationError:
        raise HTTPException(503, "AI resume generation requires OPENAI_API_KEY to be configured.")
    except Exception as e:
        raise HTTPException(500, f"Resume generation failed: {e}")

    safe = (req.company or "tailored").replace(" ", "_")[:80]
    filename = f"resume_{safe}.pdf"
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
        apply_url=req.apply_url,
        source=req.source,
        external_job_id=req.external_job_id,
        notes=req.notes,
        status=req.status,
    )
    await store.upsert_application(app)
    return app

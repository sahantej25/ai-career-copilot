from fastapi import APIRouter, Depends, HTTPException

from deps.auth import bind_user_context
from models.schemas import (
    AuthResponse, GoogleAuthRequest, LoginRequest, RegisterRequest, UserPublic,
    JobPreferences,
)
from agents.location_platform_agent import apply_location_platforms
from services import storage_service as store
from services.auth_service import (
    authenticate_google_user,
    authenticate_user,
    create_access_token,
    register_user,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.get("/providers")
async def auth_providers():
    """Tell the frontend which sign-in methods are available (no secrets)."""
    from config import settings

    google = bool((settings.google_client_id or "").strip())
    return {
        "email_password": True,
        "google": google,
    }


@router.post("/register", response_model=AuthResponse)
async def register(req: RegisterRequest):
    try:
        user = register_user(req.email, req.password, req.name)
    except ValueError as e:
        raise HTTPException(400, str(e))
    token = create_access_token(user.id, user.email)
    return AuthResponse(access_token=token, user=user)


@router.post("/login", response_model=AuthResponse)
async def login(req: LoginRequest):
    try:
        user = authenticate_user(req.email, req.password)
    except ValueError as e:
        raise HTTPException(401, str(e))
    token = create_access_token(user.id, user.email)
    return AuthResponse(access_token=token, user=user)


@router.post("/google", response_model=AuthResponse)
async def google_login(req: GoogleAuthRequest):
    from config import settings

    if not (settings.google_client_id or "").strip():
        raise HTTPException(
            503,
            "Google sign-in is not configured. Use email and password, or ask your admin to set GOOGLE_CLIENT_ID.",
        )
    try:
        user = authenticate_google_user(req.credential)
    except ValueError as e:
        raise HTTPException(401, str(e))
    token = create_access_token(user.id, user.email)
    return AuthResponse(access_token=token, user=user)


@router.get("/me", response_model=UserPublic)
async def me(user: UserPublic = Depends(bind_user_context)):
    return user


@router.get("/session")
async def session_bootstrap(user: UserPublic = Depends(bind_user_context)):
    """Full user session: profile data + cached live jobs metadata."""
    data = await store.load_data()
    return {
        "user": user,
        "data": data,
        "live_jobs_count": len(data.cached_live_jobs),
        "live_jobs_fetched_at": data.live_jobs_fetched_at,
    }


@router.put("/preferences", response_model=JobPreferences)
async def update_preferences(
    prefs: JobPreferences,
    user: UserPublic = Depends(bind_user_context),
):
    prefs = await apply_location_platforms(prefs)
    data = await store.load_data()
    data.job_preferences = prefs
    await store.save_data(data)
    return prefs

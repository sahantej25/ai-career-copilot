"""FastAPI dependencies for AI guardrails."""
from fastapi import Depends, HTTPException

from config import settings
from deps.auth import get_current_user
from models.schemas import UserPublic
from services.guardrails.context import clear_guardrail_context, set_guardrail_context
from services.guardrails.rate_limit import check_ai_rate_limit


async def require_openai_configured() -> None:
    if not (settings.openai_api_key or "").strip():
        raise HTTPException(
            503,
            "AI features are not configured. Set OPENAI_API_KEY in backend/.env to enable matching, "
            "resume generation, and rejection analysis.",
        )


async def rate_limit_ai(user: UserPublic = Depends(get_current_user)) -> UserPublic:
    await check_ai_rate_limit(user.id)
    set_guardrail_context(user_id=user.id)
    return user


async def ai_guard(user: UserPublic = Depends(rate_limit_ai)) -> UserPublic:
    """Combined guard: authenticated + rate-limited + OpenAI configured."""
    await require_openai_configured()
    return user


def clear_ai_context() -> None:
    """Reset request-scoped guardrail context (tests)."""
    clear_guardrail_context()

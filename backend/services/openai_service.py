import json
from typing import Any

from openai import AsyncOpenAI

from config import settings
from services.guardrails.ai_policy import apply_agent_policy
from services.guardrails.audit import log_ai_call, log_ai_error
from services.guardrails.constants import (
    MAX_AI_INPUT_CHARS,
    OPENAI_MAX_TOKENS,
    OPENAI_MAX_TEMPERATURE,
    OPENAI_TIMEOUT_SECONDS,
)
from services.guardrails.context import current_user_id
from services.guardrails.input import injection_flags_for_content, sanitize_user_text

_client: AsyncOpenAI | None = None


class AIConfigurationError(ValueError):
    """Raised when OpenAI is not configured."""


def require_openai_key() -> None:
    if not (settings.openai_api_key or "").strip():
        raise AIConfigurationError(
            "OPENAI_API_KEY is not configured. AI features are disabled."
        )


def get_client() -> AsyncOpenAI:
    global _client
    require_openai_key()
    if _client is None:
        _client = AsyncOpenAI(
            api_key=settings.openai_api_key,
            timeout=getattr(settings, "openai_timeout_seconds", OPENAI_TIMEOUT_SECONDS),
        )
    return _client


def reset_client() -> None:
    """Test helper."""
    global _client
    _client = None


def _safe_temperature(temperature: float) -> float:
    return max(0.0, min(OPENAI_MAX_TEMPERATURE, float(temperature)))


def _prepare_messages(system: str, user: str, *, agent: str) -> tuple[str, str, bool]:
    safe_system = apply_agent_policy(system)
    safe_user = sanitize_user_text(user, MAX_AI_INPUT_CHARS)
    flags = injection_flags_for_content(user)
    injection_flagged = bool(flags)
    if injection_flagged:
        log_ai_call(
            agent=agent,
            user_id=current_user_id.get(),
            input_chars=len(safe_user),
            injection_flagged=True,
            extra={"injection_flags": flags},
        )
    return safe_system, safe_user, injection_flagged


async def chat_json(
    system: str,
    user: str,
    temperature: float = 0.3,
    *,
    agent: str = "unknown",
) -> dict[str, Any]:
    """Call OpenAI with guardrailed prompts and parse JSON response."""
    client = get_client()
    safe_system, safe_user, injection_flagged = _prepare_messages(system, user, agent=agent)
    safe_temp = _safe_temperature(temperature)
    max_tokens = getattr(settings, "openai_max_tokens", OPENAI_MAX_TOKENS)

    if not injection_flagged:
        log_ai_call(
            agent=agent,
            user_id=current_user_id.get(),
            input_chars=len(safe_user),
            injection_flagged=False,
        )

    try:
        response = await client.chat.completions.create(
            model=settings.openai_model,
            response_format={"type": "json_object"},
            temperature=safe_temp,
            max_tokens=max_tokens,
            messages=[
                {"role": "system", "content": safe_system},
                {"role": "user", "content": safe_user},
            ],
        )
    except Exception as exc:
        log_ai_error(agent, str(exc), user_id=current_user_id.get())
        raise

    raw = response.choices[0].message.content or "{}"
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        log_ai_error(agent, "invalid_json_response", user_id=current_user_id.get())
        raise ValueError("AI returned invalid JSON.") from exc


async def chat_text(
    system: str,
    user: str,
    temperature: float = 0.5,
    *,
    agent: str = "unknown",
) -> str:
    """Call OpenAI and return plain text with guardrailed prompts."""
    client = get_client()
    safe_system, safe_user, injection_flagged = _prepare_messages(system, user, agent=agent)
    safe_temp = _safe_temperature(temperature)
    max_tokens = getattr(settings, "openai_max_tokens", OPENAI_MAX_TOKENS)

    if not injection_flagged:
        log_ai_call(
            agent=agent,
            user_id=current_user_id.get(),
            input_chars=len(safe_user),
            injection_flagged=False,
        )

    try:
        response = await client.chat.completions.create(
            model=settings.openai_model,
            temperature=safe_temp,
            max_tokens=max_tokens,
            messages=[
                {"role": "system", "content": safe_system},
                {"role": "user", "content": safe_user},
            ],
        )
    except Exception as exc:
        log_ai_error(agent, str(exc), user_id=current_user_id.get())
        raise

    return response.choices[0].message.content or ""

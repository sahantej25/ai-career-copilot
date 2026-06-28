"""Structured audit logging for AI operations — never log raw prompts or PII."""
import hashlib
import logging
from typing import Any

from services.guardrails.context import current_agent, current_user_id

logger = logging.getLogger("ai.guardrails")


def _hash_user_id(user_id: str | None) -> str:
    if not user_id:
        return "anonymous"
    return hashlib.sha256(user_id.encode()).hexdigest()[:12]


def log_ai_call(
    *,
    agent: str,
    user_id: str | None = None,
    input_chars: int = 0,
    injection_flagged: bool = False,
    extra: dict[str, Any] | None = None,
) -> None:
    uid = _hash_user_id(user_id or current_user_id.get())
    payload = {
        "agent": agent or current_agent.get() or "unknown",
        "user_hash": uid,
        "input_chars": input_chars,
        "injection_flagged": injection_flagged,
        **(extra or {}),
    }
    logger.info("ai_call %s", payload)


def log_ai_error(agent: str, error: str, user_id: str | None = None) -> None:
    uid = _hash_user_id(user_id or current_user_id.get())
    logger.warning("ai_error agent=%s user_hash=%s error=%s", agent, uid, error[:200])

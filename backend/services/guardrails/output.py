"""Validate and sanitize AI agent outputs before returning to users."""
import re

from services.guardrails.constants import (
    CONFIDENCE_DELTA_MAX,
    CONFIDENCE_DELTA_MIN,
    CONFIDENCE_MAX,
    CONFIDENCE_MIN,
    FORBIDDEN_OUTPUT_PHRASES,
    MAX_LIST_ITEMS,
    MAX_SKILL_NAME_LEN,
    MAX_STRING_ITEM_LEN,
)
from services.guardrails.input import sanitize_string_list, sanitize_user_text


def clamp_percentage(value: object, default: float = 0.0) -> float:
    try:
        num = float(value)
    except (TypeError, ValueError):
        return default
    if num != num:  # NaN
        return default
    return max(CONFIDENCE_MIN, min(CONFIDENCE_MAX, num))


def clamp_confidence_delta(value: object) -> float:
    try:
        num = float(value)
    except (TypeError, ValueError):
        return 0.0
    return max(CONFIDENCE_DELTA_MIN, min(CONFIDENCE_DELTA_MAX, num))


def sanitize_ai_text(text: object, max_len: int = MAX_STRING_ITEM_LEN) -> str:
    return sanitize_user_text(str(text or ""), max_len)


def sanitize_ai_string_list(items: object, max_items: int = MAX_LIST_ITEMS) -> list[str]:
    if not isinstance(items, list):
        return []
    return sanitize_string_list(
        [str(x) for x in items if x is not None],
        max_items=max_items,
        max_item_len=MAX_SKILL_NAME_LEN,
    )


def scrub_forbidden_phrases(text: str) -> str:
    """Remove resume-facing leakage of internal system terminology."""
    result = text
    lower = text.lower()
    for phrase in FORBIDDEN_OUTPUT_PHRASES:
        if phrase in lower:
            pattern = re.compile(re.escape(phrase), re.IGNORECASE)
            result = pattern.sub("", result)
    return re.sub(r"\s{2,}", " ", result).strip()


def validate_hex_color(value: object, default: str = "#10b981") -> str:
    accent = str(value or default).strip()
    if accent.startswith("#") and len(accent) in (4, 7):
        return accent
    return default


def validate_section_order(order: object) -> list[str]:
    allowed = {"summary", "skills", "experience", "projects", "education"}
    if not isinstance(order, list):
        return ["summary", "skills", "experience", "projects", "education"]
    result = [s for s in order if s in allowed]
    for s in ["summary", "skills", "experience", "projects", "education"]:
        if s not in result:
            result.append(s)
    return result

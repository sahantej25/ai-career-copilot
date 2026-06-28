"""Input sanitization and prompt-injection hardening for user-supplied text."""
import re
from urllib.parse import urlparse

from services.guardrails.constants import (
    MAX_AI_INPUT_CHARS,
    MAX_COMPANY_ROLE_CHARS,
    MAX_JOB_DESCRIPTION_CHARS,
    MAX_LIST_ITEMS,
    MAX_NAME_CHARS,
    MAX_NOTES_CHARS,
    MAX_REJECTION_FIELD_CHARS,
    MAX_SEARCH_QUERY_CHARS,
    MAX_SKILL_NAME_LEN,
    MAX_STRING_ITEM_LEN,
    ALLOWED_JOB_SOURCES,
    ALLOWED_TRACK_SOURCES,
)
from services.guardrails.injection import scan_prompt_injection

_CONTROL_CHARS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_HTML_TAG = re.compile(r"<[^>]+>")


def sanitize_user_text(text: str, max_len: int) -> str:
    """Normalize user text: strip control chars, collapse whitespace, enforce max length."""
    if not text:
        return ""
    cleaned = _CONTROL_CHARS.sub("", str(text))
    cleaned = cleaned.replace("\u200b", "").replace("\ufeff", "")
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    if len(cleaned) > max_len:
        cleaned = cleaned[:max_len].rstrip()
    return cleaned


def sanitize_html_user_text(text: str, max_len: int) -> str:
    """Strip HTML from user paste before sending to AI or storing."""
    plain = _HTML_TAG.sub(" ", text or "")
    return sanitize_user_text(plain, max_len)


def wrap_untrusted_content(label: str, content: str, max_len: int = MAX_AI_INPUT_CHARS) -> str:
    """
    Delimit untrusted user content so agents treat it as data, not instructions.
    Label must be alphanumeric + underscore only.
    """
    safe_label = re.sub(r"[^a-z0-9_]", "_", label.lower())[:40] or "content"
    body = sanitize_html_user_text(content, max_len)
    # Strip attempts to break out of XML delimiters
    body = re.sub(r"</user_[a-z0-9_]+>", "", body, flags=re.I)
    return f"<user_{safe_label}>\n{body}\n</user_{safe_label}>"


def injection_flags_for_content(content: str) -> list[str]:
    """Scan raw user content before AI calls (for audit logging)."""
    return scan_prompt_injection(content)


def sanitize_job_description(text: str) -> str:
    return sanitize_html_user_text(text, MAX_JOB_DESCRIPTION_CHARS)


def sanitize_company_role(text: str) -> str:
    return sanitize_user_text(text, MAX_COMPANY_ROLE_CHARS)


def sanitize_notes(text: str) -> str:
    return sanitize_user_text(text, MAX_NOTES_CHARS)


def sanitize_rejection_field(text: str) -> str:
    return sanitize_user_text(text, MAX_REJECTION_FIELD_CHARS)


def sanitize_search_query(text: str) -> str:
    return sanitize_user_text(text, MAX_SEARCH_QUERY_CHARS)


def sanitize_name(text: str) -> str:
    return sanitize_user_text(text, MAX_NAME_CHARS)


def sanitize_string_list(
    items: list[str] | None,
    *,
    max_items: int = MAX_LIST_ITEMS,
    max_item_len: int = MAX_SKILL_NAME_LEN,
) -> list[str]:
    if not items:
        return []
    out: list[str] = []
    seen: set[str] = set()
    for raw in items[:max_items]:
        item = sanitize_user_text(str(raw), max_item_len)
        key = item.lower()
        if item and key not in seen:
            seen.add(key)
            out.append(item)
    return out


def validate_apply_url(url: str) -> str:
    """Allow http(s) URLs only; reject javascript/data schemes."""
    url = (url or "").strip()
    if not url:
        return ""
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise ValueError("Apply URL must use http or https.")
    if not parsed.netloc:
        raise ValueError("Apply URL is invalid.")
    return url[:2048]


def filter_job_sources(sources: list[str] | None) -> list[str]:
    if not sources:
        return list(ALLOWED_JOB_SOURCES)
    filtered = [s for s in sources if s in ALLOWED_JOB_SOURCES]
    return filtered or list(ALLOWED_JOB_SOURCES)


def validate_track_source(source: str) -> str:
    normalized = (source or "manual").strip().lower()
    if normalized not in ALLOWED_TRACK_SOURCES:
        return "manual"
    return normalized

"""Validate resource identifiers to prevent path traversal and injection."""
import re

_ID_PATTERN = re.compile(r"^[a-zA-Z0-9_-]{1,64}$")


def sanitize_resource_id(value: str, *, field_name: str = "id") -> str:
    candidate = (value or "").strip()
    if not candidate or not _ID_PATTERN.match(candidate):
        raise ValueError(f"Invalid {field_name}.")
    return candidate


def sanitize_job_id(value: str) -> str:
    """Job IDs are `source:external_id` — validate each segment."""
    raw = (value or "").strip()
    if not raw or len(raw) > 256:
        raise ValueError("Invalid job ID.")
    if ":" in raw:
        source, rest = raw.split(":", 1)
        if not source or not rest:
            raise ValueError("Invalid job ID.")
        if not re.match(r"^[a-z0-9_]+$", source):
            raise ValueError("Invalid job source in ID.")
        if not re.match(r"^[a-zA-Z0-9_.-]{1,200}$", rest):
            raise ValueError("Invalid job ID.")
        return raw
    if not _ID_PATTERN.match(raw):
        raise ValueError("Invalid job ID.")
    return raw


def sanitize_external_job_id(value: str) -> str:
    """Accept plain app IDs or feed IDs like `linkedin:12345`."""
    raw = (value or "").strip()
    if not raw:
        return ""
    if ":" in raw:
        return sanitize_job_id(raw)
    return sanitize_resource_id(raw, field_name="external_job_id")

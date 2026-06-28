"""Normalize and parse job posted dates from heterogeneous upstream sources."""
from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from typing import Optional

_RELATIVE = re.compile(
    r"(?P<n>\d+)\s+(?P<unit>second|minute|hour|day|week|month|year)s?\s+ago",
    re.I,
)
_EPOCH_MS = re.compile(r"^\d{13}$")
_EPOCH_S = re.compile(r"^\d{10}$")


def _to_utc_iso(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _parse_relative(text: str, *, reference: datetime) -> datetime | None:
    match = _RELATIVE.search(text.strip())
    if not match:
        return None
    amount = int(match.group("n"))
    unit = match.group("unit").lower()
    delta = {
        "second": timedelta(seconds=amount),
        "minute": timedelta(minutes=amount),
        "hour": timedelta(hours=amount),
        "day": timedelta(days=amount),
        "week": timedelta(weeks=amount),
        "month": timedelta(days=amount * 30),
        "year": timedelta(days=amount * 365),
    }.get(unit)
    if delta is None:
        return None
    return reference - delta


def parse_published_at(
    raw: object,
    *,
    reference: datetime | None = None,
) -> datetime | None:
    """Parse upstream posted-date values into UTC datetimes."""
    ref = reference or datetime.now(timezone.utc)

    if raw is None:
        return None
    if isinstance(raw, (int, float)):
        ts = float(raw)
        if ts > 1e12:
            ts /= 1000.0
        try:
            return datetime.fromtimestamp(ts, tz=timezone.utc)
        except (OSError, OverflowError, ValueError):
            return None

    text = str(raw).strip()
    if not text:
        return None

    if _EPOCH_MS.match(text):
        try:
            return datetime.fromtimestamp(int(text) / 1000.0, tz=timezone.utc)
        except (OSError, OverflowError, ValueError):
            return None
    if _EPOCH_S.match(text):
        try:
            return datetime.fromtimestamp(int(text), tz=timezone.utc)
        except (OSError, OverflowError, ValueError):
            return None

    relative = _parse_relative(text, reference=ref)
    if relative is not None:
        return relative

    normalized = text.replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(normalized)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except ValueError:
        pass

    for fmt in (
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
        "%b %d, %Y",
        "%B %d, %Y",
        "%d %b %Y",
    ):
        try:
            dt = datetime.strptime(text, fmt)
            return dt.replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return None


def normalize_published_at(
    raw: object,
    *,
    reference: datetime | None = None,
) -> str:
    """Return canonical ISO-8601 UTC string for storage, or empty if unknown."""
    parsed = parse_published_at(raw, reference=reference)
    return _to_utc_iso(parsed) if parsed else ""


def published_at_timestamp(raw: str) -> float:
    """Sort key — undated jobs sort last."""
    parsed = parse_published_at(raw)
    return parsed.timestamp() if parsed else 0.0


def has_published_at(raw: str) -> bool:
    return parse_published_at(raw) is not None

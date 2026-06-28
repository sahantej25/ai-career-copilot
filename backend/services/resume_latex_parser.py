"""Extract preserve-only sections from the original uploaded resume text."""
import re

_STOP_HEADINGS = (
    r"professional\s+summary",
    r"publications?",
    r"technical\s+skills?",
    r"skills?",
    r"experience",
    r"projects?",
    r"education",
    r"certifications?",
    r"objective",
)

_STOP_PATTERN = re.compile(
    rf"^\s*(?:{'|'.join(_STOP_HEADINGS)})\s*$",
    re.IGNORECASE | re.MULTILINE,
)


def _extract_between(raw: str, start_heading: str, stop_headings: tuple[str, ...] | None = None) -> str:
    if not raw.strip():
        return ""
    start = re.search(rf"^\s*{start_heading}\s*$", raw, re.IGNORECASE | re.MULTILINE)
    if not start:
        return ""
    body_start = start.end()
    tail = raw[body_start:]
    stops = stop_headings or _STOP_HEADINGS
    stop_pattern = re.compile(
        rf"^\s*(?:{'|'.join(stops)})\s*$",
        re.IGNORECASE | re.MULTILINE,
    )
    stop = stop_pattern.search(tail)
    section = tail[: stop.start()] if stop else tail
    return section.strip()


def _split_enumerated_items(text: str) -> list[str]:
    if not text.strip():
        return []
    if "\\item" in text:
        items = re.findall(r"\\item\s+(.*?)(?=\\item|\\end|$)", text, re.DOTALL)
        return [i.strip() for i in items if i.strip()]
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    items: list[str] = []
    buf: list[str] = []
    for line in lines:
        if re.match(r"^\d+[\.\)]\s+", line) or line.startswith("•") or line.startswith("-"):
            if buf:
                items.append(" ".join(buf).strip())
                buf = []
            line = re.sub(r"^\d+[\.\)]\s+", "", line)
            line = line.lstrip("•- ").strip()
            if line:
                buf.append(line)
        elif buf:
            buf.append(line)
    if buf:
        items.append(" ".join(buf).strip())
    if not items and text.strip():
        items = [text.strip()]
    return items


def extract_publications_items(raw_text: str) -> list[str]:
    block = _extract_between(
        raw_text,
        r"publications?",
        (
            r"technical\s+skills?",
            r"skills?",
            r"experience",
            r"projects?",
            r"education",
            r"certifications?",
        ),
    )
    return _split_enumerated_items(block)


def extract_certifications_text(raw_text: str) -> str:
    return _extract_between(
        raw_text,
        r"certifications?",
        (r"references?", r"awards?", r"interests?"),
    )


def extract_linkedin_url(raw_text: str) -> str:
    match = re.search(r"https?://(?:www\.)?linkedin\.com/\S+", raw_text, re.IGNORECASE)
    return match.group(0).rstrip(".,)") if match else ""


def extract_scholar_url(raw_text: str) -> str:
    match = re.search(r"https?://scholar\.google\.com/\S+", raw_text, re.IGNORECASE)
    return match.group(0).rstrip(".,)") if match else ""


def extract_credly_or_cert_link(raw_text: str, cert_block: str) -> str:
    haystack = cert_block or raw_text
    match = re.search(r"https?://(?:www\.)?credly\.com/\S+", haystack, re.IGNORECASE)
    return match.group(0).rstrip(".,)") if match else ""

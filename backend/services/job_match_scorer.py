"""Fast heuristic job–profile match scoring (Jobright-style 0–100 feed scores)."""
import re
from html import unescape

from models.schemas import CandidateProfile, JobListing


def strip_html(text: str) -> str:
    if not text:
        return ""
    decoded = unescape(text)
    decoded = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", decoded, flags=re.I | re.S)
    decoded = re.sub(r"<!--.*?-->", " ", decoded, flags=re.S)
    cleaned = re.sub(r"<[^>]+>", " ", decoded)
    cleaned = unescape(cleaned)
    cleaned = cleaned.replace("\xa0", " ")
    return re.sub(r"\s+", " ", cleaned).strip()


def job_excerpt(text: str, max_len: int = 220) -> str:
    plain = strip_html(text)
    if len(plain) <= max_len:
        return plain
    snippet = plain[:max_len]
    if " " in snippet:
        snippet = snippet.rsplit(" ", 1)[0]
    return snippet + "…"


def _normalize_token(value: str) -> str:
    return re.sub(r"[^a-z0-9+#.\-]", "", value.lower())


def _extract_job_tokens(job: JobListing) -> set[str]:
    tokens: set[str] = set()
    for tag in job.tags:
        norm = _normalize_token(tag)
        if len(norm) >= 2:
            tokens.add(norm)

    blob = " ".join(
        filter(
            None,
            [job.title, job.excerpt, strip_html(job.description), " ".join(job.tags)],
        )
    ).lower()

    # Common tech tokens from description/title
    for word in re.findall(r"[a-zA-Z][a-zA-Z0-9+#.\-]{1,24}", blob):
        norm = _normalize_token(word)
        if len(norm) >= 2:
            tokens.add(norm)

    return tokens


def _profile_skill_map(profile: CandidateProfile) -> dict[str, float]:
    out: dict[str, float] = {}
    for skill in profile.skills:
        key = _normalize_token(skill.name)
        if key:
            out[key] = max(out.get(key, 0), skill.confidence)
    for domain in profile.domains:
        key = _normalize_token(domain)
        if key:
            out[key] = max(out.get(key, 0), 60.0)
    for project in profile.projects:
        for tech in project.technologies:
            key = _normalize_token(tech)
            if key:
                out[key] = max(out.get(key, 0), 70.0)
    return out


def _fuzzy_match(token: str, skill_keys: set[str]) -> str | None:
    if token in skill_keys:
        return token
    for key in skill_keys:
        if token in key or key in token:
            return key
    return None


def score_job_for_profile(job: JobListing, profile: CandidateProfile | None) -> JobListing:
    if not profile or not profile.skills:
        return job

    job_tokens = _extract_job_tokens(job)
    skill_map = _profile_skill_map(profile)
    skill_keys = set(skill_map.keys())

    matched: list[str] = []
    missing: list[str] = []
    weighted_sum = 0.0
    weight_total = 0.0

    for token in sorted(job_tokens):
        hit = _fuzzy_match(token, skill_keys)
        if hit:
            conf = skill_map[hit]
            matched.append(next((s.name for s in profile.skills if _normalize_token(s.name) == hit), token))
            weighted_sum += conf
            weight_total += 1.0
        elif len(token) >= 3:
            missing.append(token)

    # Title / experience alignment bonus
    title_blob = job.title.lower()
    title_bonus = 0.0
    for exp in profile.experience:
        role_words = [w for w in re.findall(r"[a-zA-Z]{3,}", exp.role.lower())]
        if any(w in title_blob for w in role_words):
            title_bonus = 12.0
            break

    overlap_pct = (weighted_sum / weight_total) if weight_total else 0.0
    coverage = (len(matched) / max(len(job_tokens), 1)) * 100
    raw = overlap_pct * 0.65 + coverage * 0.25 + title_bonus
    score = max(0.0, min(100.0, round(raw, 1)))

    # Deduplicate display names
    seen: set[str] = set()
    matched_display: list[str] = []
    for m in matched:
        key = m.lower()
        if key not in seen:
            seen.add(key)
            matched_display.append(m)

    job.match_percentage = score
    job.matched_skills = matched_display[:12]
    job.missing_skills = [m for m in missing[:12] if m not in {_normalize_token(x) for x in matched_display}]
    return job

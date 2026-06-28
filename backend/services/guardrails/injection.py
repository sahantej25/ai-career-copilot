"""Heuristic prompt-injection detection for untrusted user content."""
import re

# Patterns commonly used to hijack LLM behavior — logged, not blocked (false-positive safe).
_INJECTION_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("ignore_instructions", re.compile(r"ignore\s+(all\s+)?(previous|prior|above)\s+instructions?", re.I)),
    ("disregard_system", re.compile(r"disregard\s+(the\s+)?(system|developer)\s+(prompt|message)", re.I)),
    ("reveal_prompt", re.compile(r"(reveal|show|print|output)\s+(the\s+)?(system|hidden)\s+prompt", re.I)),
    ("role_override", re.compile(r"you\s+are\s+now\s+(a|an)\s+", re.I)),
    ("jailbreak", re.compile(r"\bjailbreak\b", re.I)),
    ("api_key_request", re.compile(r"(api[_\s-]?key|secret[_\s-]?key|openai[_\s-]?key)", re.I)),
    ("xml_escape", re.compile(r"</user_[a-z0-9_]+>", re.I)),
)


def scan_prompt_injection(text: str) -> list[str]:
    """Return labels of matched injection heuristics (empty = clean)."""
    if not text:
        return []
    hits: list[str] = []
    for label, pattern in _INJECTION_PATTERNS:
        if pattern.search(text):
            hits.append(label)
    return hits


def has_prompt_injection(text: str) -> bool:
    return bool(scan_prompt_injection(text))

"""Central limits for AI agentic guardrails."""

# ── Text input limits ───────────────────────────────────────────────────────
MAX_JOB_DESCRIPTION_CHARS = 32_000
MAX_REJECTION_FIELD_CHARS = 8_000
MAX_NOTES_CHARS = 4_000
MAX_COMPANY_ROLE_CHARS = 200
MAX_NAME_CHARS = 120
MAX_SEARCH_QUERY_CHARS = 200
MAX_AI_INPUT_CHARS = 24_000
MAX_RESUME_TEXT_CHARS = 8_000
MAX_REFERENCE_TEXT_CHARS = 6_000
MAX_LATEX_SOURCE_CHARS = 50_000
MAX_EXPERIENCE_BULLETS = 15

# ── List / collection limits ──────────────────────────────────────────────────
MAX_SKILLS = 80
MAX_LIST_ITEMS = 50
MAX_SKILL_NAME_LEN = 100
MAX_STRING_ITEM_LEN = 500

# ── File upload limits ────────────────────────────────────────────────────────
MAX_PDF_PAGES = 40
MIN_UPLOAD_BYTES = 32

# ── AI output bounds ──────────────────────────────────────────────────────────
CONFIDENCE_DELTA_MIN = -30.0
CONFIDENCE_DELTA_MAX = 15.0
CONFIDENCE_MIN = 0.0
CONFIDENCE_MAX = 100.0

# ── Rate limiting (per authenticated user) ────────────────────────────────────
AI_RATE_LIMIT_REQUESTS = 30
AI_RATE_LIMIT_WINDOW_SECONDS = 3600

# ── OpenAI call bounds ────────────────────────────────────────────────────────
OPENAI_MAX_TOKENS = 4096
OPENAI_TIMEOUT_SECONDS = 60.0
OPENAI_MAX_TEMPERATURE = 1.0

# ── HTTP request bounds ───────────────────────────────────────────────────────
MAX_REQUEST_BODY_MB = 12

# ── Allowed job feed / tracking sources ───────────────────────────────────────
ALLOWED_JOB_SOURCES = frozenset({
    "linkedin", "greenhouse", "hiringcafe", "shine", "naukri", "indeed_india",
})
ALLOWED_TRACK_SOURCES = frozenset({
    "manual", "linkedin", "greenhouse", "hiringcafe", "shine", "naukri", "indeed_india", "",
})

# ── Phrases AI must never emit in resume/candidate-facing output ──────────────
FORBIDDEN_OUTPUT_PHRASES = (
    "confidence score",
    "confidence scores",
    "system note",
    "system flag",
    "internal flag",
    "rejection annotation",
    "api key",
    "openai",
    "ignore previous",
    "jailbreak",
)

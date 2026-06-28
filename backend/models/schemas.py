from pydantic import BaseModel, Field, field_validator
from typing import Optional
from enum import Enum
import uuid
from datetime import datetime

from services.guardrails.constants import (
    MAX_COMPANY_ROLE_CHARS,
    MAX_JOB_DESCRIPTION_CHARS,
)
from services.guardrails.input import (
    filter_job_sources,
    sanitize_company_role,
    sanitize_job_description,
    sanitize_name,
    sanitize_notes,
    sanitize_rejection_field,
    sanitize_search_query,
    sanitize_string_list,
    validate_apply_url,
    validate_track_source,
)
from services.guardrails.ids import sanitize_external_job_id, sanitize_job_id, sanitize_resource_id
from services.guardrails.output import clamp_percentage


def generate_id() -> str:
    return str(uuid.uuid4())[:8]


def now_iso() -> str:
    return datetime.utcnow().isoformat() + "Z"


# ── Core domain models ──────────────────────────────────────────────────────

class Skill(BaseModel):
    name: str
    confidence: float = Field(ge=0, le=100)
    category: str = "general"


class Project(BaseModel):
    name: str
    description: str
    technologies: list[str] = []


class Experience(BaseModel):
    company: str
    role: str
    duration: str
    description: list[str] = []


class Education(BaseModel):
    degree: str
    institution: str
    year: str


class CandidateProfile(BaseModel):
    name: str = ""
    email: str = ""
    phone: str = ""
    location: str = ""
    summary: str = ""
    skills: list[Skill] = []
    projects: list[Project] = []
    experience: list[Experience] = []
    education: list[Education] = []
    domains: list[str] = []


class ApplicationStatus(str, Enum):
    saved = "saved"
    submitted = "submitted"       # Applied (Jobright)
    interview = "interview"       # Interviewing
    selected = "selected"         # Offer Received
    not_selected = "not_selected" # Rejected
    archived = "archived"


class Application(BaseModel):
    id: str = Field(default_factory=generate_id)
    company: str
    role: str
    job_description: str
    match_percentage: float = 0.0
    matched_skills: list[str] = []
    missing_skills: list[str] = []
    status: ApplicationStatus = ApplicationStatus.submitted
    submitted_at: str = Field(default_factory=now_iso)
    updated_at: str = Field(default_factory=now_iso)
    resume_filename: Optional[str] = None
    apply_url: str = ""
    source: str = ""
    external_job_id: str = ""
    notes: str = ""
    follow_up_at: Optional[str] = None
    status_history: list["StatusHistoryEntry"] = []


class StatusHistoryEntry(BaseModel):
    status: ApplicationStatus
    changed_at: str = Field(default_factory=now_iso)
    note: str = ""


class RejectionNote(BaseModel):
    application_id: str
    notes: str = ""
    interview_experience: str = ""
    rejection_email: str = ""
    topics_struggled: str = ""
    missing_skills: str = ""
    recruiter_feedback: str = ""
    summary: str = ""
    analyzed_at: Optional[str] = None


class SkillChange(BaseModel):
    skill: str
    previous_confidence: float
    new_confidence: float
    reason: str


class ProfileUpdate(BaseModel):
    id: str = Field(default_factory=generate_id)
    timestamp: str = Field(default_factory=now_iso)
    triggered_by: str  # application ID
    company: str = ""
    changes: list[SkillChange] = []
    recommendations: list[str] = []


class RadarDataPoint(BaseModel):
    subject: str
    value: float
    full_mark: float = 100


class GlobalAnalysis(BaseModel):
    summary: str = ""
    recurring_missing_skills: list[str] = []
    common_interview_topics: list[str] = []
    frequent_weaknesses: list[str] = []
    career_recommendations: list[str] = []
    skill_radar_data: list[RadarDataPoint] = []
    last_updated: str = Field(default_factory=now_iso)


class ResumeStyle(BaseModel):
    """Stylistic inspiration extracted from an optional reference resume."""
    section_order: list[str] = []        # e.g. ["summary","skills","experience","projects","education"]
    tone: str = ""                       # e.g. "concise & impact-driven"
    accent_hex: str = "#10b981"
    notes: str = ""


class JobPreferences(BaseModel):
    search_query: str = ""
    location: str = "United States"
    remote_only: bool = False
    posted_within: str = "anytime"  # 24h | 3d | 7d | anytime
    preferred_sources: list[str] = Field(default_factory=lambda: ["linkedin", "greenhouse", "hiringcafe"])

    @field_validator("search_query")
    @classmethod
    def _sanitize_search(cls, v: str) -> str:
        return sanitize_search_query(v)

    @field_validator("location")
    @classmethod
    def _sanitize_location(cls, v: str) -> str:
        return sanitize_search_query(v) or "United States"

    @field_validator("posted_within")
    @classmethod
    def _validate_posted_within(cls, v: str) -> str:
        from services.job_recency import normalize_posted_within

        return normalize_posted_within(v)

    @field_validator("preferred_sources")
    @classmethod
    def _sanitize_sources(cls, v: list[str]) -> list[str]:
        return filter_job_sources(v)


class AppData(BaseModel):
    metadata: dict = Field(default_factory=lambda: {
        "version": "1.0.0",
        "created_at": now_iso(),
        "last_updated": now_iso(),
    })
    current_profile_state: Optional[CandidateProfile] = None
    applications: list[Application] = []
    rejections: list[RejectionNote] = []
    profile_update_history: list[ProfileUpdate] = []
    global_analysis: Optional[GlobalAnalysis] = None
    resume_style: Optional[ResumeStyle] = None
    reference_resume_loaded: bool = False
    reference_resume_name: str = ""
    job_preferences: JobPreferences = Field(default_factory=JobPreferences)
    cached_live_jobs: list["JobListing"] = []
    live_jobs_fetched_at: Optional[str] = None


# ── Request/Response schemas ─────────────────────────────────────────────────

class MatchRequest(BaseModel):
    job_description: str
    company: str = ""
    role: str = ""

    @field_validator("job_description")
    @classmethod
    def _sanitize_jd(cls, v: str) -> str:
        cleaned = sanitize_job_description(v)
        if not cleaned.strip():
            raise ValueError("Job description is required.")
        return cleaned

    @field_validator("company", "role")
    @classmethod
    def _sanitize_short_text(cls, v: str) -> str:
        return sanitize_company_role(v)


class MatchStep(BaseModel):
    step: int
    title: str
    summary: str


class MatchResponse(BaseModel):
    match_percentage: float
    matched_skills: list[str]
    missing_skills: list[str]
    job_required_skills: list[str]
    recommendation: str
    company: str = ""
    role: str = ""
    matching_steps: list[MatchStep] = []
    experience_highlights: list[str] = []
    score_breakdown: dict[str, float] = {}


class MatchContextInput(BaseModel):
    """Prior match analysis passed into resume tailoring."""
    match_percentage: float = 0.0
    matched_skills: list[str] = []
    missing_skills: list[str] = []
    job_required_skills: list[str] = []
    experience_highlights: list[str] = []
    score_breakdown: dict[str, float] = {}

    @field_validator("match_percentage")
    @classmethod
    def _clamp_match(cls, v: float) -> float:
        return clamp_percentage(v)

    @field_validator("matched_skills", "missing_skills", "job_required_skills", "experience_highlights")
    @classmethod
    def _sanitize_lists(cls, v: list[str]) -> list[str]:
        return sanitize_string_list(v)


class GenerateResumeRequest(BaseModel):
    job_description: str
    company: str = ""
    role: str = ""
    skills_required: list[str] = []
    match_context: Optional["MatchContextInput"] = None

    @field_validator("job_description")
    @classmethod
    def _sanitize_jd(cls, v: str) -> str:
        cleaned = sanitize_job_description(v)
        if not cleaned.strip():
            raise ValueError("Job description is required.")
        return cleaned

    @field_validator("company", "role")
    @classmethod
    def _sanitize_short_text(cls, v: str) -> str:
        return sanitize_company_role(v)

    @field_validator("skills_required")
    @classmethod
    def _sanitize_skills(cls, v: list[str]) -> list[str]:
        return sanitize_string_list(v)


class TailoredExperienceEntry(BaseModel):
    company: str
    role: str
    duration: str
    bullets: list[str] = []


class ResumePreviewResponse(BaseModel):
    tailored_summary: str
    ordered_skills: list[str]
    highlighted_projects: list[str] = []
    key_achievements: list[str] = []
    emphasis: str = ""
    tailored_experience: list[TailoredExperienceEntry] = []
    tailoring_steps: list[MatchStep] = []


class SubmitApplicationRequest(BaseModel):
    company: str
    role: str
    job_description: str
    match_percentage: float
    matched_skills: list[str]
    missing_skills: list[str]
    resume_filename: Optional[str] = None
    apply_url: str = ""
    source: str = ""
    external_job_id: str = ""
    notes: str = ""
    status: ApplicationStatus = ApplicationStatus.submitted

    @field_validator("company", "role")
    @classmethod
    def _sanitize_short(cls, v: str) -> str:
        cleaned = sanitize_company_role(v)
        if not cleaned:
            raise ValueError("Company and role are required.")
        return cleaned

    @field_validator("job_description")
    @classmethod
    def _sanitize_jd(cls, v: str) -> str:
        return sanitize_job_description(v)

    @field_validator("matched_skills", "missing_skills")
    @classmethod
    def _sanitize_lists(cls, v: list[str]) -> list[str]:
        return sanitize_string_list(v)

    @field_validator("notes")
    @classmethod
    def _sanitize_notes(cls, v: str) -> str:
        return sanitize_notes(v)

    @field_validator("apply_url")
    @classmethod
    def _validate_url(cls, v: str) -> str:
        if not v:
            return ""
        return validate_apply_url(v)

    @field_validator("match_percentage")
    @classmethod
    def _clamp_match(cls, v: float) -> float:
        return clamp_percentage(v)

    @field_validator("source")
    @classmethod
    def _validate_source(cls, v: str) -> str:
        return validate_track_source(v)

    @field_validator("external_job_id")
    @classmethod
    def _sanitize_external_id(cls, v: str) -> str:
        if not v:
            return ""
        return sanitize_external_job_id(v)


class TrackJobRequest(BaseModel):
    """Log a job from Discover or an external URL (Jobright-style tracker)."""
    company: str
    role: str
    job_description: str = ""
    apply_url: str = ""
    source: str = "manual"
    external_job_id: str = ""
    match_percentage: float = 0.0
    matched_skills: list[str] = []
    missing_skills: list[str] = []
    status: ApplicationStatus = ApplicationStatus.submitted
    notes: str = ""

    @field_validator("company", "role")
    @classmethod
    def _sanitize_short(cls, v: str) -> str:
        cleaned = sanitize_company_role(v)
        if not cleaned:
            raise ValueError("Company and role are required.")
        return cleaned

    @field_validator("job_description")
    @classmethod
    def _sanitize_jd(cls, v: str) -> str:
        return sanitize_job_description(v)

    @field_validator("matched_skills", "missing_skills")
    @classmethod
    def _sanitize_lists(cls, v: list[str]) -> list[str]:
        return sanitize_string_list(v)

    @field_validator("notes")
    @classmethod
    def _sanitize_notes(cls, v: str) -> str:
        return sanitize_notes(v)

    @field_validator("apply_url")
    @classmethod
    def _validate_url(cls, v: str) -> str:
        if not v:
            return ""
        return validate_apply_url(v)

    @field_validator("match_percentage")
    @classmethod
    def _clamp_match(cls, v: float) -> float:
        return clamp_percentage(v)

    @field_validator("source")
    @classmethod
    def _validate_source(cls, v: str) -> str:
        return validate_track_source(v)

    @field_validator("external_job_id")
    @classmethod
    def _sanitize_external_id(cls, v: str) -> str:
        if not v:
            return ""
        return sanitize_external_job_id(v)


class UpdateApplicationRequest(BaseModel):
    notes: Optional[str] = None
    follow_up_at: Optional[str] = None
    apply_url: Optional[str] = None

    @field_validator("notes")
    @classmethod
    def _sanitize_notes(cls, v: Optional[str]) -> Optional[str]:
        return sanitize_notes(v) if v is not None else None

    @field_validator("apply_url")
    @classmethod
    def _validate_url(cls, v: Optional[str]) -> Optional[str]:
        if v is None or not v.strip():
            return v
        return validate_apply_url(v)


class UpdateStatusRequest(BaseModel):
    status: ApplicationStatus


class AnalyzeRejectionRequest(BaseModel):
    application_id: str
    notes: str = ""
    interview_experience: str = ""
    rejection_email: str = ""
    topics_struggled: str = ""
    missing_skills: str = ""
    recruiter_feedback: str = ""

    @field_validator("application_id")
    @classmethod
    def _sanitize_app_id(cls, v: str) -> str:
        return sanitize_resource_id(v, field_name="application_id")

    @field_validator(
        "notes",
        "interview_experience",
        "rejection_email",
        "topics_struggled",
        "missing_skills",
        "recruiter_feedback",
    )
    @classmethod
    def _sanitize_rejection_fields(cls, v: str) -> str:
        return sanitize_rejection_field(v)


class AnalyzeRejectionResponse(BaseModel):
    skill_changes: list[SkillChange]
    recommendations: list[str]
    profile_update: ProfileUpdate
    summary: str


# ── Job discovery (Jobright-style feed) ─────────────────────────────────────

class JobListing(BaseModel):
    id: str
    title: str
    company: str
    location: str = ""
    remote: bool = True
    job_type: str = ""
    salary: str = ""
    description: str = ""
    excerpt: str = ""
    tags: list[str] = []
    apply_url: str
    source: str
    company_logo: str = ""
    published_at: str = ""
    match_percentage: float | None = None
    matched_skills: list[str] = []
    missing_skills: list[str] = []


class JobFeedResponse(BaseModel):
    total: int
    sources: list[str]
    jobs: list[JobListing]
    fetched_at: str = Field(default_factory=now_iso)


class LiveJobsResponse(JobFeedResponse):
    from_cache: bool = False
    preferences: Optional[JobPreferences] = None


# ── Auth ────────────────────────────────────────────────────────────────────

class UserPublic(BaseModel):
    id: str
    email: str
    name: str
    auth_provider: str = "local"  # local | google | linked
    picture: str = ""


class RegisterRequest(BaseModel):
    email: str
    password: str
    name: str = ""

    @field_validator("email")
    @classmethod
    def _normalize_email(cls, v: str) -> str:
        email = v.strip().lower()
        if "@" not in email or len(email) > 254:
            raise ValueError("Invalid email address.")
        return email

    @field_validator("password")
    @classmethod
    def _validate_password(cls, v: str) -> str:
        if len(v) < 6:
            raise ValueError("Password must be at least 6 characters.")
        if len(v) > 128:
            raise ValueError("Password is too long.")
        return v

    @field_validator("name")
    @classmethod
    def _sanitize_name(cls, v: str) -> str:
        return sanitize_name(v)


class LoginRequest(BaseModel):
    email: str
    password: str

    @field_validator("email")
    @classmethod
    def _normalize_email(cls, v: str) -> str:
        return v.strip().lower()

    @field_validator("password")
    @classmethod
    def _limit_password(cls, v: str) -> str:
        if len(v) > 128:
            raise ValueError("Invalid credentials.")
        return v


class GoogleAuthRequest(BaseModel):
    credential: str

    @field_validator("credential")
    @classmethod
    def _limit_credential(cls, v: str) -> str:
        token = (v or "").strip()
        if not token or len(token) > 8192:
            raise ValueError("Invalid Google credential.")
        return token


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserPublic


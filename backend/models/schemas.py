from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum
import uuid
from datetime import datetime


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
    preferred_sources: list[str] = Field(default_factory=lambda: ["linkedin", "greenhouse", "hiringcafe"])


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


class MatchResponse(BaseModel):
    match_percentage: float
    matched_skills: list[str]
    missing_skills: list[str]
    job_required_skills: list[str]
    recommendation: str
    company: str = ""
    role: str = ""


class GenerateResumeRequest(BaseModel):
    job_description: str
    company: str = ""
    role: str = ""
    skills_required: list[str] = []


class ResumePreviewResponse(BaseModel):
    tailored_summary: str
    ordered_skills: list[str]
    highlighted_projects: list[str] = []
    key_achievements: list[str] = []
    emphasis: str = ""


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


class UpdateApplicationRequest(BaseModel):
    notes: Optional[str] = None
    follow_up_at: Optional[str] = None
    apply_url: Optional[str] = None


class UpdateStatusRequest(BaseModel):
    status: ApplicationStatus


class AnalyzeRejectionRequest(BaseModel):
    application_id: str
    notes: str = ""                      # free-text rejection notes (primary input)
    interview_experience: str = ""
    rejection_email: str = ""
    topics_struggled: str = ""
    missing_skills: str = ""
    recruiter_feedback: str = ""


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


class RegisterRequest(BaseModel):
    email: str
    password: str
    name: str = ""


class LoginRequest(BaseModel):
    email: str
    password: str


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserPublic


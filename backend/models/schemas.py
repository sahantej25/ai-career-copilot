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
    submitted = "submitted"
    interview = "interview"
    selected = "selected"
    not_selected = "not_selected"


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


class RejectionNote(BaseModel):
    application_id: str
    interview_experience: str = ""
    rejection_email: str = ""
    topics_struggled: str = ""
    missing_skills: str = ""
    recruiter_feedback: str = ""
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
    recurring_missing_skills: list[str] = []
    common_interview_topics: list[str] = []
    frequent_weaknesses: list[str] = []
    career_recommendations: list[str] = []
    skill_radar_data: list[RadarDataPoint] = []
    last_updated: str = Field(default_factory=now_iso)


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


class GenerateResumeRequest(BaseModel):
    job_description: str
    company: str = ""
    role: str = ""


class SubmitApplicationRequest(BaseModel):
    company: str
    role: str
    job_description: str
    match_percentage: float
    matched_skills: list[str]
    missing_skills: list[str]
    resume_filename: Optional[str] = None


class UpdateStatusRequest(BaseModel):
    status: ApplicationStatus


class AnalyzeRejectionRequest(BaseModel):
    application_id: str
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

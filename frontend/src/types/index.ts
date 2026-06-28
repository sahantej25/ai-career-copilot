export interface Skill {
  name: string;
  confidence: number;
  category: string;
}

export interface Project {
  name: string;
  description: string;
  technologies: string[];
}

export interface Experience {
  company: string;
  role: string;
  duration: string;
  description: string[];
}

export interface Education {
  degree: string;
  institution: string;
  year: string;
}

export interface CandidateProfile {
  name: string;
  email: string;
  phone: string;
  location: string;
  summary: string;
  skills: Skill[];
  projects: Project[];
  experience: Experience[];
  education: Education[];
  domains: string[];
}

export type ApplicationStatus =
  | "saved"
  | "submitted"
  | "interview"
  | "selected"
  | "not_selected"
  | "archived";

export interface Application {
  id: string;
  company: string;
  role: string;
  job_description: string;
  match_percentage: number;
  matched_skills: string[];
  missing_skills: string[];
  status: ApplicationStatus;
  submitted_at: string;
  updated_at: string;
  resume_filename?: string;
  apply_url?: string;
  source?: string;
  external_job_id?: string;
  notes?: string;
  follow_up_at?: string;
  status_history?: StatusHistoryEntry[];
}

export interface StatusHistoryEntry {
  status: ApplicationStatus;
  changed_at: string;
  note?: string;
}

export interface RejectionNote {
  application_id: string;
  notes?: string;
  interview_experience: string;
  rejection_email: string;
  topics_struggled: string;
  missing_skills: string;
  recruiter_feedback: string;
  summary?: string;
  analyzed_at?: string;
}

export interface SkillChange {
  skill: string;
  previous_confidence: number;
  new_confidence: number;
  reason: string;
}

export interface ProfileUpdate {
  id: string;
  timestamp: string;
  triggered_by: string;
  company: string;
  changes: SkillChange[];
  recommendations: string[];
}

export interface RadarDataPoint {
  subject: string;
  value: number;
  full_mark: number;
}

export interface GlobalAnalysis {
  summary?: string;
  recurring_missing_skills: string[];
  common_interview_topics: string[];
  frequent_weaknesses: string[];
  career_recommendations: string[];
  skill_radar_data: RadarDataPoint[];
  last_updated: string;
}

export interface MatchResult {
  match_percentage: number;
  matched_skills: string[];
  missing_skills: string[];
  job_required_skills: string[];
  recommendation: string;
  company?: string;
  role?: string;
}

export interface ResumePreview {
  tailored_summary: string;
  ordered_skills: string[];
  highlighted_projects: string[];
  key_achievements: string[];
  emphasis: string;
}

export interface ResumeStyle {
  section_order: string[];
  tone: string;
  accent_hex: string;
  notes: string;
}

export interface AnalyzeRejectionResponse {
  skill_changes: SkillChange[];
  recommendations: string[];
  profile_update: ProfileUpdate;
  summary: string;
}

export type TabId = "discover" | "apply" | "tracking" | "not-selected" | "global-analysis";

export interface JobListing {
  id: string;
  title: string;
  company: string;
  location: string;
  remote: boolean;
  job_type: string;
  salary: string;
  description: string;
  excerpt: string;
  tags: string[];
  apply_url: string;
  source: string;
  company_logo: string;
  published_at: string;
  match_percentage?: number | null;
  matched_skills: string[];
  missing_skills: string[];
}

export interface JobFeedResponse {
  total: number;
  sources: string[];
  jobs: JobListing[];
  fetched_at: string;
}

export interface JobPreferences {
  search_query: string;
  location: string;
  remote_only: boolean;
  preferred_sources: string[];
}

export interface LiveJobsResponse extends JobFeedResponse {
  from_cache?: boolean;
  preferences?: JobPreferences | null;
}

export interface AuthUser {
  id: string;
  email: string;
  name: string;
  auth_provider?: "local" | "google" | "linked";
  picture?: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: AuthUser;
}

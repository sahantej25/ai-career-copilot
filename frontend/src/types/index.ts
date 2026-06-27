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

export type ApplicationStatus = "submitted" | "interview" | "selected" | "not_selected";

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
}

export interface RejectionNote {
  application_id: string;
  interview_experience: string;
  rejection_email: string;
  topics_struggled: string;
  missing_skills: string;
  recruiter_feedback: string;
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
}

export interface AnalyzeRejectionResponse {
  skill_changes: SkillChange[];
  recommendations: string[];
  profile_update: ProfileUpdate;
  summary: string;
}

export type TabId = "apply" | "tracking" | "not-selected" | "global-analysis";

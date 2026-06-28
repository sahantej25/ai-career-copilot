import axios from "axios";
import type {
  CandidateProfile, MatchResult, MatchContextInput, Application, ApplicationStatus,
  AnalyzeRejectionResponse, GlobalAnalysis, ProfileUpdate, RejectionNote,
  ResumePreview, ResumeStyle, JobFeedResponse, LiveJobsResponse, AuthResponse,
} from "@/types";

const BASE = import.meta.env.VITE_API_URL || "";

const http = axios.create({
  baseURL: BASE,
  timeout: 60000,
});

let authToken: string | null = null;

export function setAuthToken(token: string | null) {
  authToken = token;
}

http.interceptors.request.use((config) => {
  if (authToken) {
    config.headers.Authorization = `Bearer ${authToken}`;
  }
  return config;
});

http.interceptors.response.use(
  (res) => res,
  (err) => {
    const msg =
      err.response?.data?.detail ||
      err.response?.data?.message ||
      err.message ||
      "Request failed";
    return Promise.reject(new Error(typeof msg === "string" ? msg : JSON.stringify(msg)));
  }
);

// ── Auth ──────────────────────────────────────────────────────────────────

export async function login(email: string, password: string): Promise<AuthResponse> {
  const { data } = await http.post("/api/auth/login", { email, password });
  return data as AuthResponse;
}

export async function register(email: string, password: string, name: string): Promise<AuthResponse> {
  const { data } = await http.post("/api/auth/register", { email, password, name });
  return data as AuthResponse;
}

export async function loginWithGoogle(credential: string): Promise<AuthResponse> {
  const { data } = await http.post("/api/auth/google", { credential });
  return data as AuthResponse;
}

export async function getSession() {
  const { data } = await http.get("/api/auth/session");
  return data as {
    user: AuthResponse["user"];
    data: Record<string, unknown> & { job_preferences?: import("@/types").JobPreferences; cached_live_jobs?: import("@/types").JobListing[] };
    live_jobs_count: number;
    live_jobs_fetched_at: string | null;
  };
}

export async function fetchLiveJobs(refresh = false): Promise<LiveJobsResponse> {
  const { data } = await http.get("/api/jobs/live", {
    params: { refresh },
    timeout: 90000,
  });
  return data as LiveJobsResponse;
}

export async function updateJobPreferences(
  prefs: import("@/types").JobPreferences
): Promise<import("@/types").JobPreferences> {
  const { data } = await http.put("/api/auth/preferences", prefs);
  return data as import("@/types").JobPreferences;
}

// ── Apply ─────────────────────────────────────────────────────────────────

export async function uploadProfile(file: File): Promise<CandidateProfile> {
  const form = new FormData();
  form.append("file", file);
  const { data } = await http.post("/api/apply/upload-profile", form, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data.profile as CandidateProfile;
}

export async function uploadReference(
  file: File
): Promise<{ style: ResumeStyle; name: string }> {
  const form = new FormData();
  form.append("file", file);
  const { data } = await http.post("/api/apply/upload-reference", form, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return { style: data.style as ResumeStyle, name: data.name as string };
}

export async function removeReference(): Promise<void> {
  await http.delete("/api/apply/reference");
}

export async function matchJob(
  jobDescription: string,
  company: string,
  role: string
): Promise<MatchResult> {
  const { data } = await http.post("/api/apply/match", {
    job_description: jobDescription,
    company,
    role,
  });
  return data as MatchResult;
}

function toMatchContext(match: MatchResult | null | undefined): MatchContextInput | undefined {
  if (!match) return undefined;
  return {
    match_percentage: match.match_percentage,
    matched_skills: match.matched_skills,
    missing_skills: match.missing_skills,
    job_required_skills: match.job_required_skills,
    experience_highlights: match.experience_highlights,
    score_breakdown: match.score_breakdown,
  };
}

export async function resumePreview(
  jobDescription: string,
  company: string,
  role: string,
  skillsRequired: string[] = [],
  matchContext?: MatchResult | null
): Promise<ResumePreview> {
  const { data } = await http.post("/api/apply/resume-preview", {
    job_description: jobDescription,
    company,
    role,
    skills_required: skillsRequired,
    match_context: toMatchContext(matchContext),
  });
  return data as ResumePreview;
}

export async function generateResume(
  jobDescription: string,
  company: string,
  role: string,
  skillsRequired: string[] = [],
  matchContext?: MatchResult | null
): Promise<Blob> {
  const { data } = await http.post(
    "/api/apply/generate-resume",
    {
      job_description: jobDescription,
      company,
      role,
      skills_required: skillsRequired,
      match_context: toMatchContext(matchContext),
    },
    { responseType: "blob" }
  );
  return data as Blob;
}

export async function submitApplication(payload: {
  company: string;
  role: string;
  job_description: string;
  match_percentage: number;
  matched_skills: string[];
  missing_skills: string[];
  resume_filename?: string;
  apply_url?: string;
  source?: string;
  external_job_id?: string;
  notes?: string;
  status?: ApplicationStatus;
}): Promise<Application> {
  const { data } = await http.post("/api/apply/submit", payload);
  return data as Application;
}

// ── Tracking ──────────────────────────────────────────────────────────────

export async function getApplications(includeArchived = false): Promise<Application[]> {
  const { data } = await http.get("/api/tracking/applications", {
    params: { include_archived: includeArchived },
  });
  return data as Application[];
}

export async function trackJob(payload: {
  company: string;
  role: string;
  job_description?: string;
  apply_url?: string;
  source?: string;
  external_job_id?: string;
  match_percentage?: number;
  matched_skills?: string[];
  missing_skills?: string[];
  status?: ApplicationStatus;
  notes?: string;
}): Promise<Application> {
  const { data } = await http.post("/api/tracking/applications/track", payload);
  return data as Application;
}

export async function patchApplication(
  id: string,
  payload: { notes?: string; follow_up_at?: string; apply_url?: string }
): Promise<Application> {
  const { data } = await http.patch(`/api/tracking/applications/${id}`, payload);
  return data as Application;
}

export async function getPipelineSummary(): Promise<{
  counts: Record<string, number>;
  active: number;
  total: number;
}> {
  const { data } = await http.get("/api/tracking/pipeline/summary");
  return data;
}

export async function updateApplicationStatus(
  id: string,
  status: ApplicationStatus
): Promise<Application> {
  const { data } = await http.put(`/api/tracking/applications/${id}/status`, { status });
  return data as Application;
}

export async function deleteApplication(id: string): Promise<void> {
  await http.delete(`/api/tracking/applications/${id}`);
}

// ── Analysis ──────────────────────────────────────────────────────────────

export async function analyzeRejection(payload: {
  application_id: string;
  notes?: string;
  interview_experience?: string;
  rejection_email?: string;
  topics_struggled?: string;
  missing_skills?: string;
  recruiter_feedback?: string;
}): Promise<AnalyzeRejectionResponse> {
  const { data } = await http.post("/api/analysis/rejection/analyze", payload);
  return data as AnalyzeRejectionResponse;
}

export async function getRejection(appId: string): Promise<RejectionNote> {
  const { data } = await http.get(`/api/analysis/rejection/${appId}`);
  return data as RejectionNote;
}

export async function getGlobalAnalysis(): Promise<GlobalAnalysis> {
  const { data } = await http.get("/api/analysis/global");
  return data as GlobalAnalysis;
}

export async function refreshGlobalAnalysis(): Promise<GlobalAnalysis> {
  const { data } = await http.post("/api/analysis/global/refresh");
  return data as GlobalAnalysis;
}

export async function getProfileHistory(): Promise<ProfileUpdate[]> {
  const { data } = await http.get("/api/analysis/profile-history");
  return data.history as ProfileUpdate[];
}

export async function getAllData() {
  const { data } = await http.get("/api/data");
  return data;
}

// ── Data management ─────────────────────────────────────────────────────────

export async function clearAllData(): Promise<void> {
  await http.post("/api/data/clear");
}

// ── Job discovery ─────────────────────────────────────────────────────────

export async function fetchJobFeed(params?: {
  search?: string;
  sources?: string;
  limit?: number;
  remoteOnly?: boolean;
  location?: string;
  match?: boolean;
}): Promise<JobFeedResponse> {
  const { data } = await http.get("/api/jobs", {
    params: {
      search: params?.search ?? "",
      sources: params?.sources ?? "",
      limit: params?.limit ?? 24,
      remote_only: params?.remoteOnly ?? false,
      location: params?.location ?? "",
      match: params?.match ?? true,
    },
    timeout: 45000,
  });
  return data as JobFeedResponse;
}

export async function getJobSources(): Promise<string[]> {
  const { data } = await http.get("/api/jobs/sources");
  return (data as { sources: string[] }).sources;
}

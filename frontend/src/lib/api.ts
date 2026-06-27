import axios from "axios";
import type {
  CandidateProfile, MatchResult, Application, ApplicationStatus,
  AnalyzeRejectionResponse, GlobalAnalysis, ProfileUpdate, RejectionNote,
} from "@/types";

const BASE = import.meta.env.VITE_API_URL || "";

const http = axios.create({
  baseURL: BASE,
  timeout: 60000,
});

http.interceptors.response.use(
  (res) => res,
  (err) => {
    const msg =
      err.response?.data?.detail ||
      err.response?.data?.message ||
      err.message ||
      "Request failed";
    return Promise.reject(new Error(msg));
  }
);

// ── Apply ─────────────────────────────────────────────────────────────────

export async function uploadProfile(file: File): Promise<CandidateProfile> {
  const form = new FormData();
  form.append("file", file);
  const { data } = await http.post("/api/apply/upload-profile", form, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data.profile as CandidateProfile;
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

export async function generateResume(
  jobDescription: string,
  company: string,
  role: string
): Promise<Blob> {
  const { data } = await http.post(
    "/api/apply/generate-resume",
    { job_description: jobDescription, company, role },
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
}): Promise<Application> {
  const { data } = await http.post("/api/apply/submit", payload);
  return data as Application;
}

// ── Tracking ──────────────────────────────────────────────────────────────

export async function getApplications(): Promise<Application[]> {
  const { data } = await http.get("/api/tracking/applications");
  return data as Application[];
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
  interview_experience: string;
  rejection_email: string;
  topics_struggled: string;
  missing_skills: string;
  recruiter_feedback: string;
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
  const { data } = await http.get("/api/analysis/data");
  return data;
}

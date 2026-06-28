import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";
import { ApplicationStatus } from "@/types";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatDate(iso: string): string {
  const parsed = new Date(iso);
  if (Number.isNaN(parsed.getTime())) return "";
  return parsed.toLocaleDateString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

export function formatRelativeTime(iso: string): string {
  const parsed = new Date(iso);
  if (Number.isNaN(parsed.getTime())) return "";
  const diffMs = Date.now() - parsed.getTime();
  if (diffMs < 0) return "Just posted";
  const minutes = Math.floor(diffMs / 60000);
  if (minutes < 1) return "Just now";
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  if (days === 1) return "Yesterday";
  if (days < 7) return `${days} days ago`;
  if (days < 30) return `${Math.floor(days / 7)}w ago`;
  return `${Math.floor(days / 30)}mo ago`;
}

export function formatPostedDate(iso: string): string {
  const relative = formatRelativeTime(iso);
  const absolute = formatDate(iso);
  if (relative && absolute) return `${relative} · ${absolute}`;
  return relative || absolute;
}

export const STATUS_CONFIG: Record<
  ApplicationStatus,
  { label: string; color: string; bg: string; border: string; dot: string; column?: string }
> = {
  saved: {
    label: "Saved",
    color: "text-violet-700",
    bg: "bg-violet-50",
    border: "border-violet-200",
    dot: "bg-violet-500",
    column: "Saved",
  },
  submitted: {
    label: "Applied",
    color: "text-sky-700",
    bg: "bg-sky-50",
    border: "border-sky-200",
    dot: "bg-sky-500",
    column: "Applied",
  },
  interview: {
    label: "Interviewing",
    color: "text-amber-700",
    bg: "bg-amber-50",
    border: "border-amber-200",
    dot: "bg-amber-500",
    column: "Interviewing",
  },
  selected: {
    label: "Offer Received",
    color: "text-emerald-700",
    bg: "bg-emerald-50",
    border: "border-emerald-200",
    dot: "bg-emerald-500",
    column: "Offer",
  },
  not_selected: {
    label: "Rejected",
    color: "text-rose-600",
    bg: "bg-rose-50",
    border: "border-rose-200",
    dot: "bg-rose-500",
    column: "Rejected",
  },
  archived: {
    label: "Archived",
    color: "text-ink-500",
    bg: "bg-slate-100",
    border: "border-slate-200",
    dot: "bg-slate-400",
    column: "Archived",
  },
};

export const SOURCE_LABELS: Record<string, string> = {
  linkedin: "LinkedIn",
  greenhouse: "Greenhouse",
  hiringcafe: "Hiring Cafe",
  manual: "External",
  remotive: "Remotive",
  jobicy: "Jobicy",
  remoteok: "RemoteOK",
  arbeitnow: "Arbeitnow",
};

export function getMatchColor(pct: number): string {
  if (pct >= 75) return "text-emerald-600";
  if (pct >= 50) return "text-amber-600";
  return "text-rose-600";
}

export function getMatchBg(pct: number): string {
  if (pct >= 75) return "bg-emerald-500";
  if (pct >= 50) return "bg-amber-500";
  return "bg-rose-500";
}

/** Guardrail limits — keep in sync with backend/services/guardrails/constants.py */
export const INPUT_LIMITS = {
  jobDescription: 32_000,
  companyRole: 200,
  notes: 4_000,
  rejectionField: 8_000,
  searchQuery: 200,
} as const;

/** Truncate user input to a safe max length before API calls. */
export function clampInput(text: string, maxLen: number): string {
  const trimmed = (text || "").replace(/\s+/g, " ").trim();
  if (trimmed.length <= maxLen) return trimmed;
  return trimmed.slice(0, maxLen).trim();
}

/** Strip HTML tags and entities from pasted content. */
export function stripHtml(text: string): string {
  if (!text) return "";
  const decoded = text
    .replace(/&nbsp;/gi, " ")
    .replace(/&amp;/gi, "&")
    .replace(/&lt;/gi, "<")
    .replace(/&gt;/gi, ">")
    .replace(/&quot;/gi, '"')
    .replace(/&#39;/gi, "'");
  const noTags = decoded.replace(/<[^>]+>/g, " ");
  return noTags.replace(/\s+/g, " ").trim();
}

/** Strip HTML tags from pasted job descriptions before sending to API. */
export function sanitizeUserInput(text: string, maxLen: number): string {
  const plain = stripHtml(text);
  return clampInput(plain, maxLen);
}

export function jobPreviewText(job: { excerpt?: string; description?: string }, maxLen = 220): string {
  const plain = stripHtml(job.excerpt || job.description || "");
  if (plain.length <= maxLen) return plain;
  const snippet = plain.slice(0, maxLen);
  return (snippet.includes(" ") ? snippet.slice(0, snippet.lastIndexOf(" ")) : snippet) + "…";
}

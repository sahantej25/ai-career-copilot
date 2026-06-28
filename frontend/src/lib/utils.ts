import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";
import { ApplicationStatus } from "@/types";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

export function formatRelativeTime(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const days = Math.floor(diff / 86400000);
  if (days === 0) return "Today";
  if (days === 1) return "Yesterday";
  if (days < 7) return `${days} days ago`;
  if (days < 30) return `${Math.floor(days / 7)}w ago`;
  return `${Math.floor(days / 30)}mo ago`;
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

/** Strip HTML tags/entities for safe plain-text job previews. */
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

export function jobPreviewText(job: { excerpt?: string; description?: string }, maxLen = 220): string {
  const plain = stripHtml(job.excerpt || job.description || "");
  if (plain.length <= maxLen) return plain;
  const snippet = plain.slice(0, maxLen);
  return (snippet.includes(" ") ? snippet.slice(0, snippet.lastIndexOf(" ")) : snippet) + "…";
}

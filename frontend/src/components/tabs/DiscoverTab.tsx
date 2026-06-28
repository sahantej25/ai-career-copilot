import { useCallback, useEffect, useMemo, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Search, RefreshCw, MapPin, Building2, ExternalLink, Sparkles,
  Zap, Globe, Filter, Briefcase, ArrowRight, Clock, TrendingUp, BookmarkCheck,
} from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Card, CardContent } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Progress } from "@/components/ui/Progress";
import { useAppStore } from "@/hooks/useAppStore";
import { useAuthStore } from "@/hooks/useAuthStore";
import { cn, formatRelativeTime, getMatchColor, jobPreviewText, SOURCE_LABELS, stripHtml } from "@/lib/utils";
import * as api from "@/lib/api";
import type { JobListing } from "@/types";

function MatchBadge({ score }: { score?: number | null }) {
  if (score == null) return null;
  const tone =
    score >= 75 ? "success" : score >= 50 ? "warning" : "danger";
  return (
    <Badge variant={tone} className="tabular-nums font-bold">
      {score.toFixed(0)}% match
    </Badge>
  );
}

function JobCard({
  job,
  onTailorApply,
  onExternalApply,
  onTrack,
  tracking,
}: {
  job: JobListing;
  onTailorApply: (job: JobListing) => void;
  onExternalApply: (url: string) => void;
  onTrack: (job: JobListing) => void;
  tracking?: boolean;
}) {
  const score = job.match_percentage ?? null;

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -8 }}
    >
      <Card interactive className="overflow-hidden">
        <CardContent className="p-0">
          <div className="flex flex-col gap-4 p-5 sm:flex-row sm:items-start">
            {/* Logo / avatar */}
            <div className="flex h-12 w-12 shrink-0 items-center justify-center overflow-hidden rounded-xl border border-slate-200 bg-white">
              {job.company_logo ? (
                <img
                  src={job.company_logo}
                  alt=""
                  className="h-full w-full object-contain p-1"
                  onError={(e) => { (e.target as HTMLImageElement).style.display = "none"; }}
                />
              ) : (
                <Building2 className="h-5 w-5 text-brand-600" />
              )}
            </div>

            <div className="min-w-0 flex-1 space-y-3">
              <div className="flex flex-wrap items-start justify-between gap-2">
                <div className="min-w-0">
                  <h3 className="font-display text-lg font-semibold leading-snug text-ink-900">
                    {job.title}
                  </h3>
                  <p className="mt-0.5 text-sm font-medium text-ink-600">{job.company}</p>
                </div>
                <MatchBadge score={score} />
              </div>

              <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-ink-500">
                {job.location && (
                  <span className="inline-flex items-center gap-1">
                    <MapPin className="h-3.5 w-3.5" /> {job.location}
                  </span>
                )}
                {job.remote && (
                  <span className="inline-flex items-center gap-1 text-emerald-600">
                    <Globe className="h-3.5 w-3.5" /> Remote
                  </span>
                )}
                {job.salary && (
                  <span className="font-medium text-brand-700">{job.salary}</span>
                )}
                {job.published_at && (
                  <span className="inline-flex items-center gap-1">
                    <Clock className="h-3.5 w-3.5" />
                    {formatRelativeTime(job.published_at)}
                  </span>
                )}
                <Badge variant="default" className="text-[10px]">
                  {SOURCE_LABELS[job.source] || job.source}
                </Badge>
              </div>

              <p className="text-sm leading-relaxed text-ink-500 line-clamp-2">
                {jobPreviewText(job)}
              </p>

              {score != null && (
                <div className="max-w-xs">
                  <Progress value={score} colorByValue size="sm" />
                </div>
              )}

              {(job.matched_skills.length > 0 || job.tags.length > 0) && (
                <div className="flex flex-wrap gap-1.5">
                  {(job.matched_skills.length ? job.matched_skills : job.tags).slice(0, 8).map((tag) => (
                    <Badge
                      key={tag}
                      variant={job.matched_skills.includes(tag) ? "success" : "default"}
                      className="text-[10px]"
                    >
                      {tag}
                    </Badge>
                  ))}
                </div>
              )}

              <div className="flex flex-col gap-2 pt-1 sm:flex-row sm:flex-wrap">
                <Button size="sm" className="flex-1 sm:flex-none" onClick={() => onTailorApply(job)}>
                  <Zap className="h-4 w-4" /> Tailor & Apply <ArrowRight className="h-3.5 w-3.5 opacity-70" />
                </Button>
                <Button size="sm" variant="outline" className="flex-1 sm:flex-none" onClick={() => onExternalApply(job.apply_url)}>
                  <ExternalLink className="h-4 w-4" /> Apply on {SOURCE_LABELS[job.source] || "Site"}
                </Button>
                <Button size="sm" variant="secondary" className="flex-1 sm:flex-none" onClick={() => onTrack(job)} loading={tracking} disabled={job.id === "hiringcafe:search-portal"}>
                  <BookmarkCheck className="h-4 w-4" /> Track
                </Button>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}

export function DiscoverTab() {
  const { profile, startApplicationFromJob, upsertApplication, addToast, isLoading, setLoading } = useAppStore();
  const liveJobs = useAuthStore((s) => s.liveJobs);
  const liveJobsFetchedAt = useAuthStore((s) => s.liveJobsFetchedAt);
  const liveJobsFromCache = useAuthStore((s) => s.liveJobsFromCache);
  const refreshLiveJobs = useAuthStore((s) => s.refreshLiveJobs);
  const jobPreferences = useAuthStore((s) => s.jobPreferences);

  const [jobs, setJobs] = useState<JobListing[]>([]);
  const [sources, setSources] = useState<string[]>(["linkedin", "greenhouse", "hiringcafe"]);
  const [search, setSearch] = useState("");
  const [draftSearch, setDraftSearch] = useState(jobPreferences?.search_query || "");
  const [location, setLocation] = useState(jobPreferences?.location || "United States");
  const [remoteOnly, setRemoteOnly] = useState(jobPreferences?.remote_only || false);
  const [trackingId, setTrackingId] = useState<string | null>(null);

  const loading = isLoading["jobs"] ?? false;

  const loadJobs = useCallback(async (force = false, prefsOverride?: { search?: string; location?: string; remoteOnly?: boolean }) => {
    setLoading("jobs", true);
    try {
      const prefs = {
        search_query: prefsOverride?.search ?? draftSearch.trim(),
        location: prefsOverride?.location ?? location,
        remote_only: prefsOverride?.remoteOnly ?? remoteOnly,
        preferred_sources: jobPreferences?.preferred_sources || ["linkedin", "greenhouse", "hiringcafe"],
      };
      await api.updateJobPreferences(prefs);
      useAuthStore.getState().setJobPreferences(prefs);
      await refreshLiveJobs(force);
      const storeJobs = useAuthStore.getState().liveJobs;
      setJobs(storeJobs);
      setSources(prefs.preferred_sources);
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "Failed to load jobs";
      addToast({ type: "error", message: msg });
    } finally {
      setLoading("jobs", false);
    }
  }, [refreshLiveJobs, jobPreferences, draftSearch, location, remoteOnly, addToast, setLoading]);

  useEffect(() => {
    setJobs(liveJobs);
  }, [liveJobs]);

  useEffect(() => {
    const interval = setInterval(() => loadJobs(true), 30 * 60 * 1000);
    return () => clearInterval(interval);
  }, [loadJobs]);

  const filteredJobs = useMemo(() => {
    if (!search.trim()) return jobs;
    const q = search.toLowerCase();
    return jobs.filter((j) =>
      `${j.title} ${j.company} ${j.tags.join(" ")} ${j.excerpt}`.toLowerCase().includes(q)
    );
  }, [jobs, search]);

  const stats = useMemo(() => {
    const withScore = filteredJobs.filter((j) => j.match_percentage != null);
    const strong = withScore.filter((j) => (j.match_percentage ?? 0) >= 75).length;
    const avg =
      withScore.length > 0
        ? withScore.reduce((s, j) => s + (j.match_percentage ?? 0), 0) / withScore.length
        : 0;
    return { total: filteredJobs.length, strong, avg };
  }, [filteredJobs]);

  useEffect(() => {
    if (!jobPreferences) return;
    setDraftSearch(jobPreferences.search_query || "");
    setLocation(jobPreferences.location || "United States");
    setRemoteOnly(jobPreferences.remote_only || false);
  }, [jobPreferences]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setSearch("");
    loadJobs(true);
  };

  const handleExternalApply = (url: string) => {
    if (!url) {
      addToast({ type: "error", message: "No application URL available for this listing." });
      return;
    }
    window.open(url, "_blank", "noopener,noreferrer");
    addToast({ type: "info", message: "Opened company application page in a new tab." });
  };

  const handleTrack = async (job: JobListing) => {
    setTrackingId(job.id);
    try {
      const plainDesc = stripHtml(job.description || job.excerpt || "");
      const app = await api.trackJob({
        company: job.company,
        role: job.title,
        job_description: plainDesc,
        apply_url: job.apply_url,
        source: job.source,
        external_job_id: job.id,
        match_percentage: job.match_percentage ?? 0,
        matched_skills: job.matched_skills,
        missing_skills: job.missing_skills,
        status: "saved",
      });
      upsertApplication(app);
      addToast({ type: "success", message: `Saved ${job.company} to your pipeline — view in Tracker` });
    } catch (e: unknown) {
      addToast({ type: "error", message: e instanceof Error ? e.message : "Failed to track" });
    } finally {
      setTrackingId(null);
    }
  };

  return (
    <div className="mx-auto w-full max-w-5xl space-y-6 p-4 py-6 sm:p-6">
      {/* Hero — Jobright-style discovery header */}
      <div className="space-y-3">
        <Badge variant="success" className="text-[10px]">
          <Sparkles className="h-2.5 w-2.5" /> Live Job Feed
        </Badge>
        <h1 className="font-display text-3xl font-bold tracking-tightest text-ink-900 sm:text-4xl">
          Discover <span className="gradient-text-brand">Matched Jobs</span>
        </h1>
        <p className="max-w-2xl text-sm leading-relaxed text-ink-500">
          Real postings from LinkedIn, Greenhouse career pages, and Hiring Cafe — ranked by profile fit. Track every application in your Jobright-style pipeline.
        </p>
      </div>

      {/* Stats strip */}
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        {[
          { label: "Open roles", value: stats.total, icon: Briefcase },
          { label: "Strong matches", value: stats.strong, icon: TrendingUp },
          { label: "Avg match", value: profile ? `${stats.avg.toFixed(0)}%` : "—", icon: Zap },
          { label: "Sources live", value: sources.length, icon: Globe },
        ].map(({ label, value, icon: Icon }) => (
          <div key={label} className="glass glass-edge rounded-2xl p-4">
            <div className="mb-2 flex items-center gap-2 text-ink-400">
              <Icon className="h-4 w-4" />
              <span className="text-[10px] font-semibold uppercase tracking-wider">{label}</span>
            </div>
            <p className="font-display text-2xl font-bold tabular-nums text-ink-900">{value}</p>
          </div>
        ))}
      </div>

      {/* Search & filters */}
      <Card>
        <CardContent className="space-y-4 p-5">
          <form onSubmit={handleSearch} className="flex flex-col gap-3 sm:flex-row">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-ink-400" />
            <input
              className="input-field pl-10"
              placeholder="Search roles & skills (e.g. React, Stripe, Data Engineer)…"
              value={draftSearch}
              onChange={(e) => setDraftSearch(e.target.value)}
            />
          </div>
          <input
            className="input-field sm:w-48"
            placeholder="Location (LinkedIn)"
            value={location}
            onChange={(e) => setLocation(e.target.value)}
          />
            <div className="flex gap-2">
              <Button type="submit" disabled={loading}>
                <Search className="h-4 w-4" /> Search
              </Button>
              <Button type="button" variant="secondary" onClick={() => loadJobs(true)} loading={loading}>
                <RefreshCw className="h-4 w-4" /> Live refresh
              </Button>
            </div>
          </form>

          <div className="flex flex-wrap items-center gap-3">
            <span className="inline-flex items-center gap-1.5 text-xs text-ink-500">
              <Filter className="h-3.5 w-3.5" /> Filters
            </span>
            <button
              type="button"
              onClick={() => {
                const next = !remoteOnly;
                setRemoteOnly(next);
                loadJobs(true, { remoteOnly: next });
              }}
              className={cn(
                "rounded-lg border px-3 py-1.5 text-xs font-medium transition-colors cursor-pointer",
                remoteOnly
                  ? "border-emerald-300 bg-emerald-50 text-emerald-700"
                  : "border-slate-200 bg-white text-ink-600 hover:border-slate-300"
              )}
            >
              Remote only
            </button>
            {sources.map((s) => (
              <Badge key={s} variant="info" className="text-[10px]">
                {SOURCE_LABELS[s] || s}
              </Badge>
            ))}
            {liveJobsFetchedAt && (
              <span className="ml-auto text-[10px] text-ink-400">
                {liveJobsFromCache ? "Cached · " : "Live · "}
                Updated {formatRelativeTime(liveJobsFetchedAt)}
              </span>
            )}
          </div>

          {!profile && (
            <div className="rounded-xl border border-amber-200 bg-amber-50/60 px-4 py-3 text-xs text-amber-800">
              Upload your profile in the <strong>Apply</strong> tab to unlock personalized match scores on every listing.
            </div>
          )}
        </CardContent>
      </Card>

      {/* Job list */}
      {loading && filteredJobs.length === 0 ? (
        <div className="space-y-4 py-8 text-center">
          <RefreshCw className="mx-auto h-8 w-8 animate-spin text-brand-500" />
          <p className="text-sm text-ink-500">Fetching latest jobs from {sources.length || 4} sources…</p>
        </div>
      ) : filteredJobs.length === 0 ? (
        <div className="py-16 text-center">
          <Briefcase className="mx-auto mb-3 h-10 w-10 text-ink-300" />
          <p className="font-medium text-ink-700">No jobs found</p>
          <p className="mt-1 text-sm text-ink-400">Try a broader search or refresh the feed.</p>
        </div>
      ) : (
        <div className="space-y-4">
          <AnimatePresence mode="popLayout">
            {filteredJobs.map((job) => (
              <JobCard
                key={job.id}
                job={job}
                onTailorApply={startApplicationFromJob}
                onExternalApply={handleExternalApply}
                onTrack={handleTrack}
                tracking={trackingId === job.id}
              />
            ))}
          </AnimatePresence>
        </div>
      )}

      {/* How it works — Jobright parity callout */}
      <Card className="border-brand-100 bg-brand-50/30">
        <CardContent className="grid gap-4 p-5 sm:grid-cols-3">
          {[
            {
              step: "1",
              title: "Discover real roles",
              desc: "LinkedIn guest search, Greenhouse boards (Stripe, Figma…), and Hiring Cafe.",
            },
            {
              step: "2",
              title: "Apply & track",
              desc: "Open the company application page, then Track to log it in your pipeline.",
            },
            {
              step: "3",
              title: "Manage like Jobright",
              desc: "Saved → Applied → Interviewing → Offer → Rejected → Archived.",
            },
          ].map(({ step, title, desc }) => (
            <div key={step} className="space-y-1.5">
              <span className="inline-flex h-6 w-6 items-center justify-center rounded-full bg-brand-500 text-[11px] font-bold text-white">
                {step}
              </span>
              <p className="text-sm font-semibold text-ink-800">{title}</p>
              <p className="text-xs leading-relaxed text-ink-500">{desc}</p>
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}

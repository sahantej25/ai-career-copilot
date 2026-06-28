import { useState, useCallback } from "react";
import { useDropzone } from "react-dropzone";
import { motion, AnimatePresence } from "framer-motion";
import {
  Upload, FileText, Briefcase, Zap, Download, CheckCircle2,
  UploadCloud, X, RefreshCw, Target, AlertCircle, Sparkles,
  Plus, FileCheck2, Wand2, ListChecks, ExternalLink, User,
} from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Progress, AnimatedCounter } from "@/components/ui/Progress";
import { useAppStore } from "@/hooks/useAppStore";
import { cn, getMatchColor, INPUT_LIMITS, sanitizeUserInput } from "@/lib/utils";
import * as api from "@/lib/api";
import type { ResumePreview } from "@/types";

/* ───────────────────────── File dropzone ───────────────────────── */
function FileDropZone({ onFile, file, label, hint, accept, tone = "brand" }: {
  onFile: (f: File) => void;
  file: File | null;
  label: string;
  hint: string;
  accept: Record<string, string[]>;
  tone?: "brand" | "violet";
}) {
  const onDrop = useCallback((accepted: File[]) => {
    if (accepted[0]) onFile(accepted[0]);
  }, [onFile]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({ onDrop, maxFiles: 1, accept });

  return (
    <div
      {...getRootProps()}
      className={cn(
        "group relative cursor-pointer overflow-hidden rounded-2xl border border-dashed p-6 text-center transition-all duration-300 ease-out-expo",
        isDragActive
          ? "border-brand-400 bg-brand-50"
          : file
          ? "border-emerald-300 bg-emerald-50/60"
          : "border-slate-300 bg-white/40 hover:border-brand-400 hover:bg-brand-50/40"
      )}
    >
      <input {...getInputProps()} />
      <AnimatePresence mode="wait">
        {file ? (
          <motion.div key="f" initial={{ opacity: 0, scale: 0.96 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0 }} className="flex items-center gap-3 text-left">
            <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-emerald-100">
              <FileCheck2 className="h-5 w-5 text-emerald-600" />
            </div>
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-semibold text-emerald-700">{file.name}</p>
              <p className="text-xs text-ink-400">{(file.size / 1024).toFixed(0)} KB · ready</p>
            </div>
            <CheckCircle2 className="h-5 w-5 shrink-0 text-emerald-500" />
          </motion.div>
        ) : (
          <motion.div key="e" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
            <div className={cn(
              "mx-auto mb-2.5 flex h-12 w-12 items-center justify-center rounded-2xl transition-all duration-300",
              isDragActive ? "scale-110" : "",
              tone === "violet" ? "bg-violet-100 text-violet-600" : "bg-brand-100 text-brand-600"
            )}>
              <UploadCloud className="h-6 w-6" />
            </div>
            <p className="text-sm font-medium text-ink-700">{label}</p>
            <p className="mt-0.5 text-xs text-ink-400">{hint}</p>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

/* ───────────────────────── Editable chips ───────────────────────── */
function EditableChips({ items, onChange, tone = "sky" }: {
  items: string[];
  onChange: (next: string[]) => void;
  tone?: "sky" | "emerald";
}) {
  const [draft, setDraft] = useState("");
  const add = () => {
    const v = draft.trim();
    if (v && !items.some((i) => i.toLowerCase() === v.toLowerCase())) onChange([...items, v]);
    setDraft("");
  };
  const toneCls = tone === "emerald"
    ? "bg-emerald-50 text-emerald-700 border-emerald-200"
    : "bg-sky-50 text-sky-700 border-sky-200";

  return (
    <div>
      <div className="flex flex-wrap gap-1.5">
        {items.map((s) => (
          <span key={s} className={cn("inline-flex items-center gap-1 rounded-lg border px-2.5 py-1 text-xs font-medium", toneCls)}>
            {s}
            <button onClick={() => onChange(items.filter((i) => i !== s))} className="rounded-full p-0.5 hover:bg-black/5 cursor-pointer" aria-label={`Remove ${s}`}>
              <X className="h-3 w-3" />
            </button>
          </span>
        ))}
        {items.length === 0 && <span className="text-xs text-ink-400">No skills yet — extract from the JD or add manually.</span>}
      </div>
      <div className="mt-2.5 flex gap-2">
        <input
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && (e.preventDefault(), add())}
          placeholder="Add a skill and press Enter"
          className="input-field flex-1 py-1.5 text-xs"
        />
        <Button size="sm" variant="secondary" onClick={add} disabled={!draft.trim()}>
          <Plus className="h-3.5 w-3.5" /> Add
        </Button>
      </div>
    </div>
  );
}

/* ───────────────────────── Gating checklist ───────────────────────── */
function ChecklistItem({ done, label }: { done: boolean; label: string }) {
  return (
    <div className={cn("flex items-center gap-2 text-xs", done ? "text-emerald-600" : "text-ink-400")}>
      <span className={cn("flex h-4 w-4 items-center justify-center rounded-full text-[9px] font-bold",
        done ? "bg-emerald-500 text-white" : "bg-slate-200 text-slate-400")}>
        {done ? "✓" : ""}
      </span>
      {label}
    </div>
  );
}

export function ApplyTab() {
  const {
    profile, setProfile, currentJD, setCurrentJD,
    currentCompany, setCurrentCompany, currentRole, setCurrentRole,
    currentSkillsRequired, setCurrentSkillsRequired,
    referenceLoaded, referenceName, setReference,
    currentMatch, setCurrentMatch, upsertApplication, setActiveTab,
    addToast, isLoading, setLoading,
    pendingJob, clearPendingJob, setProfileModalOpen,
  } = useAppStore();

  const [resumeFile, setResumeFile] = useState<File | null>(null);
  const [refFile, setRefFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<ResumePreview | null>(null);
  const [resumeDownloaded, setResumeDownloaded] = useState(false);
  const [submitted, setSubmitted] = useState(false);

  const loading = (k: string) => isLoading[k] ?? false;

  /* ---- conditions (PRD §6.1) ---- */
  const c = {
    profile: !!profile,
    jd: currentJD.trim().length > 0,
    company: currentCompany.trim().length > 0,
    role: currentRole.trim().length > 0,
    skillsRequired: currentSkillsRequired.length > 0,
    userSkills: (profile?.skills.length ?? 0) > 0,
    match: !!currentMatch,
  };
  const canPrepare = Object.values(c).every(Boolean);
  const canSubmit = resumeDownloaded && c.company && c.role && c.match;

  /* ---- handlers ---- */
  const handleRemoveProfile = async () => {
    try {
      await api.clearProfile();
    } catch { /* ignore if already cleared */ }
    setProfile(null);
    setResumeFile(null);
    addToast({ type: "info", message: "Profile removed." });
  };

  const handleUploadProfile = async () => {
    if (!resumeFile) return;
    setLoading("upload", true);
    try {
      const parsed = await api.uploadProfile(resumeFile);
      setProfile(parsed);
      addToast({ type: "success", message: `Profile loaded: ${parsed.name || "Candidate"}` });
    } catch (e: any) {
      addToast({ type: "error", message: e.message });
    } finally {
      setLoading("upload", false);
    }
  };

  const handleUploadReference = async (f: File) => {
    setRefFile(f);
    setLoading("reference", true);
    try {
      const { name } = await api.uploadReference(f);
      setReference(true, name);
      addToast({ type: "success", message: "Reference resume style captured." });
    } catch (e: any) {
      setRefFile(null);
      addToast({ type: "error", message: e.message });
    } finally {
      setLoading("reference", false);
    }
  };

  const handleRemoveReference = async () => {
    try {
      await api.removeReference();
    } catch { /* ignore */ }
    setRefFile(null);
    setReference(false, "");
    addToast({ type: "info", message: "Reference removed — default template will be used." });
  };

  const handleMatch = async () => {
    if (!currentJD.trim()) return;
    setLoading("match", true);
    setPreview(null);
    setResumeDownloaded(false);
    const jd = sanitizeUserInput(currentJD, INPUT_LIMITS.jobDescription);
    const company = sanitizeUserInput(currentCompany, INPUT_LIMITS.companyRole);
    const role = sanitizeUserInput(currentRole, INPUT_LIMITS.companyRole);
    try {
      const result = await api.matchJob(jd, company, role);
      setCurrentMatch(result);
      if (result.company && !currentCompany.trim()) setCurrentCompany(result.company);
      if (result.role && !currentRole.trim()) setCurrentRole(result.role);
      if (result.job_required_skills?.length) setCurrentSkillsRequired(result.job_required_skills);
      addToast({ type: "success", message: "Skills extracted & match calculated!" });
      // Auto-load resume preview (what it will emphasize)
      try {
        const pv = await api.resumePreview(
          jd, result.company || company, result.role || role,
          result.job_required_skills || [], result,
        );
        setPreview(pv);
      } catch { /* preview is best-effort */ }
    } catch (e: any) {
      addToast({ type: "error", message: e.message });
    } finally {
      setLoading("match", false);
    }
  };

  const handleDownloadResume = async () => {
    setLoading("generate", true);
    const jd = sanitizeUserInput(currentJD, INPUT_LIMITS.jobDescription);
    const company = sanitizeUserInput(currentCompany, INPUT_LIMITS.companyRole);
    const role = sanitizeUserInput(currentRole, INPUT_LIMITS.companyRole);
    try {
      const blob = await api.generateResume(jd, company, role, currentSkillsRequired, currentMatch);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `resume_${currentCompany.replace(/\s+/g, "_") || "tailored"}.pdf`;
      a.click();
      URL.revokeObjectURL(url);
      setResumeDownloaded(true);
      addToast({ type: "success", message: "Tailored resume downloaded!" });
    } catch (e: any) {
      addToast({ type: "error", message: e.message });
    } finally {
      setLoading("generate", false);
    }
  };

  const handleSubmit = async () => {
    if (!currentMatch) return;
    setLoading("submit", true);
    const jd = sanitizeUserInput(currentJD, INPUT_LIMITS.jobDescription);
    const company = sanitizeUserInput(currentCompany, INPUT_LIMITS.companyRole);
    const role = sanitizeUserInput(currentRole, INPUT_LIMITS.companyRole);
    try {
      const app = await api.submitApplication({
        company,
        role,
        job_description: jd,
        match_percentage: currentMatch.match_percentage,
        matched_skills: currentMatch.matched_skills,
        missing_skills: currentMatch.missing_skills,
        apply_url: pendingJob?.apply_url || "",
        source: pendingJob?.source || "",
        external_job_id: pendingJob?.id || "",
        status: "submitted",
      });
      upsertApplication(app);
      setSubmitted(true);
      addToast({ type: "success", message: `Application to ${currentCompany} logged!` });
    } catch (e: any) {
      addToast({ type: "error", message: e.message });
    } finally {
      setLoading("submit", false);
    }
  };

  const handleReset = () => {
    setCurrentJD(""); setCurrentCompany(""); setCurrentRole("");
    setCurrentSkillsRequired([]); setCurrentMatch(null);
    setPreview(null); setResumeDownloaded(false); setSubmitted(false);
    clearPendingJob();
  };

  return (
    <div className="mx-auto w-full max-w-4xl space-y-6 p-4 py-6 sm:p-6">
      {/* Pre-filled from Discover feed */}
      {pendingJob && (
        <motion.div initial={{ opacity: 0, y: -8 }} animate={{ opacity: 1, y: 0 }}>
          <Card className="border-brand-200 bg-brand-50/40">
            <CardContent className="flex flex-col gap-3 p-4 sm:flex-row sm:items-center sm:justify-between">
              <div className="min-w-0">
                <p className="text-xs font-semibold uppercase tracking-wider text-brand-700">
                  From job feed
                </p>
                <p className="truncate font-semibold text-ink-900">
                  {pendingJob.title} · {pendingJob.company}
                </p>
                <p className="text-xs text-ink-500">
                  JD pre-filled — run match analysis, tailor your resume, then apply on the company site.
                </p>
              </div>
              <div className="flex shrink-0 gap-2">
                {pendingJob.apply_url && (
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => window.open(pendingJob.apply_url, "_blank", "noopener,noreferrer")}
                  >
                    <ExternalLink className="h-4 w-4" /> Company Site
                  </Button>
                )}
                <Button size="sm" variant="ghost" onClick={clearPendingJob}>
                  <X className="h-4 w-4" />
                </Button>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      )}

      {/* Heading */}
      <div className="space-y-2">
        <Badge variant="success" className="text-[10px]"><Sparkles className="h-2.5 w-2.5" /> AI Workflow</Badge>
        <h1 className="font-display text-3xl font-bold tracking-tightest text-ink-900 sm:text-4xl">
          Prepare & <span className="gradient-text-brand">Apply</span>
        </h1>
        <p className="max-w-2xl text-sm leading-relaxed text-ink-500">
          Upload your profile, optionally guide the style with a reference resume, match against any job description, then generate a tailored PDF — all in one intelligent flow.
        </p>
      </div>

      {/* Step 1: Inputs */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2.5">
              <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-brand-100 text-brand-700"><Upload className="h-4 w-4" /></span>
              Candidate Profile
            </CardTitle>
            {profile && <Badge variant="success" dot>Profile loaded</Badge>}
          </div>
        </CardHeader>
        <CardContent>
          {profile ? (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-5">
              <div className="flex items-center gap-4 rounded-2xl border border-emerald-200 bg-emerald-50/60 p-4">
                <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-brand-400 to-teal-500 text-lg font-bold text-white">
                  {profile.name?.charAt(0).toUpperCase() || "?"}
                </div>
                <div className="min-w-0 flex-1">
                  <p className="font-semibold text-ink-900">{profile.name}</p>
                  <p className="truncate text-sm text-ink-500">{profile.email}</p>
                  <div className="mt-2 flex flex-wrap gap-1.5">
                    {profile.domains.slice(0, 4).map((d) => <Badge key={d} variant="purple">{d}</Badge>)}
                  </div>
                </div>
                <div className="flex shrink-0 gap-1">
                  <button onClick={() => setProfileModalOpen(true)} className="rounded-lg p-1.5 text-ink-400 transition-colors hover:bg-slate-100 hover:text-ink-700 cursor-pointer" aria-label="Edit profile">
                    <User className="h-4 w-4" />
                  </button>
                  <button onClick={handleRemoveProfile} className="rounded-lg p-1.5 text-ink-400 transition-colors hover:bg-slate-100 hover:text-ink-700 cursor-pointer" aria-label="Remove profile">
                    <X className="h-4 w-4" />
                  </button>
                </div>
              </div>
              <div>
                <p className="section-label mb-2.5">Extracted Skills · {profile.skills.length}</p>
                <div className="flex flex-wrap gap-2">
                  {profile.skills.slice(0, 20).map((s) => (
                    <div key={s.name} className="flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white/70 px-2.5 py-1">
                      <span className="text-xs text-ink-700">{s.name}</span>
                      <span className="text-[10px] font-bold text-brand-600 tabular-nums">{s.confidence.toFixed(0)}%</span>
                    </div>
                  ))}
                  {profile.skills.length > 20 && <span className="py-1 text-xs text-ink-400">+{profile.skills.length - 20} more</span>}
                </div>
              </div>
            </motion.div>
          ) : (
            <div className="space-y-4">
              <FileDropZone
                onFile={setResumeFile} file={resumeFile}
                label="Drop your profile / resume here or click to browse"
                hint="PDF, DOCX, TXT · Max 10MB"
                accept={{
                  "application/pdf": [".pdf"],
                  "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [".docx"],
                  "text/plain": [".txt"],
                }}
              />
              <Button onClick={handleUploadProfile} disabled={!resumeFile} loading={loading("upload")} className="w-full">
                <Upload className="h-4 w-4" />
                {loading("upload") ? "Parsing with AI..." : "Parse Profile"}
              </Button>
              <div className="relative flex items-center py-1">
                <div className="flex-1 border-t border-slate-200" />
                <span className="px-3 text-xs text-ink-400">or</span>
                <div className="flex-1 border-t border-slate-200" />
              </div>
              <Button variant="secondary" onClick={() => setProfileModalOpen(true)} className="w-full">
                <User className="h-4 w-4" />
                Enter profile manually
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Reference resume (optional) */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2.5">
              <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-violet-100 text-violet-600"><FileText className="h-4 w-4" /></span>
              Reference Resume <span className="text-sm font-normal text-ink-400">· optional</span>
            </CardTitle>
            {referenceLoaded && <Badge variant="purple" dot>Reference loaded</Badge>}
          </div>
        </CardHeader>
        <CardContent>
          {referenceLoaded ? (
            <div className="flex items-center gap-3 rounded-2xl border border-violet-200 bg-violet-50/60 p-4">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-violet-100"><FileCheck2 className="h-5 w-5 text-violet-600" /></div>
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-semibold text-violet-700">{referenceName || "Reference resume"}</p>
                <p className="text-xs text-ink-400">Style & structure will inspire your generated resume.</p>
              </div>
              <button onClick={handleRemoveReference} className="shrink-0 rounded-lg p-1.5 text-ink-400 hover:bg-white hover:text-ink-700 cursor-pointer" aria-label="Remove reference">
                <X className="h-4 w-4" />
              </button>
            </div>
          ) : (
            <FileDropZone
              onFile={handleUploadReference} file={refFile}
              label={loading("reference") ? "Reading style..." : "Drop a reference resume for style inspiration"}
              hint="PDF, DOCX · We borrow structure & tone, never content"
              tone="violet"
              accept={{
                "application/pdf": [".pdf"],
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [".docx"],
              }}
            />
          )}
        </CardContent>
      </Card>

      {/* Step 2: JD */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2.5">
            <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-brand-100 text-brand-700"><Briefcase className="h-4 w-4" /></span>
            Job Description
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div>
              <label className="section-label mb-1.5 block">Company {currentMatch?.company && !currentCompany && <span className="text-brand-600">· auto</span>}</label>
              <input className="input-field" placeholder="e.g. Google" value={currentCompany} onChange={(e) => setCurrentCompany(e.target.value)} />
            </div>
            <div>
              <label className="section-label mb-1.5 block">Role</label>
              <input className="input-field" placeholder="e.g. Senior Software Engineer" value={currentRole} onChange={(e) => setCurrentRole(e.target.value)} />
            </div>
          </div>
          <div>
            <label className="section-label mb-1.5 block">Job Description</label>
            <textarea className="input-field resize-none" rows={8} placeholder="Paste the full job description here..." value={currentJD} onChange={(e) => setCurrentJD(e.target.value)} />
          </div>
          <Button onClick={handleMatch} disabled={!currentJD.trim() || !profile} loading={loading("match")} className="w-full">
            <Zap className="h-4 w-4" />
            {loading("match") ? "Analyzing fit (3 steps)..." : "Analyze Profile vs Job Description"}
          </Button>
          {!profile && (
            <p className="flex items-center justify-center gap-1 text-xs text-amber-600">
              <AlertCircle className="h-3 w-3" /> Upload your profile first.
            </p>
          )}
        </CardContent>
      </Card>

      {/* Step 3: Match */}
      <AnimatePresence>
        {currentMatch && (
          <motion.div initial={{ opacity: 0, y: 24 }} animate={{ opacity: 1, y: 0 }}>
            <Card glow className="border-brand-200">
              <CardHeader>
                <CardTitle className="flex items-center gap-2.5">
                  <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-brand-100 text-brand-700"><Target className="h-4 w-4" /></span>
                  Match Analysis
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="flex flex-col items-center gap-6 sm:flex-row">
                  <div className="relative h-28 w-28 shrink-0">
                    <svg className="h-28 w-28 -rotate-90" viewBox="0 0 80 80">
                      <circle cx="40" cy="40" r="34" fill="none" stroke="#e2e8f0" strokeWidth="7" />
                      <motion.circle
                        cx="40" cy="40" r="34" fill="none"
                        stroke={currentMatch.match_percentage >= 75 ? "#10b981" : currentMatch.match_percentage >= 50 ? "#f59e0b" : "#f43f5e"}
                        strokeWidth="7" strokeLinecap="round"
                        strokeDasharray={`${2 * Math.PI * 34}`}
                        initial={{ strokeDashoffset: 2 * Math.PI * 34 }}
                        animate={{ strokeDashoffset: 2 * Math.PI * 34 * (1 - currentMatch.match_percentage / 100) }}
                        transition={{ duration: 1.6, ease: [0.16, 1, 0.3, 1] }}
                      />
                    </svg>
                    <div className="absolute inset-0 flex items-center justify-center">
                      <AnimatedCounter value={currentMatch.match_percentage} suffix="%" className={cn("font-display text-2xl font-bold", getMatchColor(currentMatch.match_percentage))} />
                    </div>
                  </div>
                  <div className="flex-1 text-center sm:text-left">
                    <p className="font-display text-xl font-semibold text-ink-900">
                      {currentMatch.match_percentage >= 75 ? "Strong Match" : currentMatch.match_percentage >= 50 ? "Moderate Match" : "Low Match"}
                    </p>
                    <p className="mt-1.5 text-sm leading-relaxed text-ink-500">{currentMatch.recommendation}</p>
                  </div>
                </div>

                {currentMatch.score_breakdown && Object.keys(currentMatch.score_breakdown).length > 0 && (
                  <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
                    {Object.entries(currentMatch.score_breakdown).map(([key, val]) => (
                      <div key={key} className="rounded-xl border border-slate-200 bg-white/60 px-3 py-2.5 text-center">
                        <p className="text-[10px] font-semibold uppercase tracking-wider text-ink-400">{key}</p>
                        <p className={cn("font-display text-lg font-bold tabular-nums", getMatchColor(val))}>{val.toFixed(0)}%</p>
                      </div>
                    ))}
                  </div>
                )}

                {currentMatch.matching_steps && currentMatch.matching_steps.length > 0 && (
                  <div className="rounded-2xl border border-brand-100 bg-brand-50/40 p-4">
                    <p className="section-label mb-3 text-brand-700">Step-by-step analysis</p>
                    <ol className="space-y-2">
                      {currentMatch.matching_steps.map((step) => (
                        <li key={step.step} className="flex gap-3 text-sm">
                          <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-brand-500 text-[11px] font-bold text-white">{step.step}</span>
                          <div>
                            <p className="font-medium text-ink-800">{step.title}</p>
                            <p className="text-xs leading-relaxed text-ink-500">{step.summary}</p>
                          </div>
                        </li>
                      ))}
                    </ol>
                  </div>
                )}

                {currentMatch.experience_highlights && currentMatch.experience_highlights.length > 0 && (
                  <div className="rounded-2xl border border-violet-100 bg-violet-50/40 p-4">
                    <p className="section-label mb-2 text-violet-700">Strongest experience for this role</p>
                    <ul className="space-y-1.5 text-sm text-ink-600">
                      {currentMatch.experience_highlights.map((h) => (
                        <li key={h} className="flex gap-2"><span className="text-violet-500">•</span>{h}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Editable Skills Required (PRD: editable list) */}
                <div className="rounded-2xl border border-sky-100 bg-sky-50/50 p-4">
                  <p className="section-label mb-2.5 flex items-center gap-1.5 text-sky-700"><ListChecks className="h-3.5 w-3.5" /> Skills Required (editable)</p>
                  <EditableChips items={currentSkillsRequired} onChange={setCurrentSkillsRequired} tone="sky" />
                </div>

                <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                  <div className="rounded-2xl border border-emerald-100 bg-emerald-50/50 p-4">
                    <p className="section-label mb-2.5 flex items-center gap-1.5 text-emerald-700"><CheckCircle2 className="h-3.5 w-3.5" /> Matched · {currentMatch.matched_skills.length}</p>
                    <div className="flex flex-wrap gap-1.5">{currentMatch.matched_skills.map((s) => <Badge key={s} variant="success">{s}</Badge>)}</div>
                  </div>
                  <div className="rounded-2xl border border-rose-100 bg-rose-50/50 p-4">
                    <p className="section-label mb-2.5 flex items-center gap-1.5 text-rose-600"><AlertCircle className="h-3.5 w-3.5" /> Missing · {currentMatch.missing_skills.length}</p>
                    <div className="flex flex-wrap gap-1.5">{currentMatch.missing_skills.map((s) => <Badge key={s} variant="danger">{s}</Badge>)}</div>
                  </div>
                </div>

                <div>
                  <div className="mb-2 flex justify-between text-xs text-ink-500"><span>Overall match score</span><span className="tabular-nums">{currentMatch.match_percentage.toFixed(0)}%</span></div>
                  <Progress value={currentMatch.match_percentage} colorByValue size="lg" />
                </div>
              </CardContent>
            </Card>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Resume preview */}
      <AnimatePresence>
        {preview && (
          <motion.div initial={{ opacity: 0, y: 24 }} animate={{ opacity: 1, y: 0 }}>
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2.5">
                  <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-violet-100 text-violet-600"><Wand2 className="h-4 w-4" /></span>
                  Tailored Resume Preview
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {preview.emphasis && (
                  <div className="rounded-xl border border-violet-100 bg-violet-50/50 p-3.5 text-sm text-ink-700">{preview.emphasis}</div>
                )}
                <div>
                  <p className="section-label mb-1.5">Tailored summary</p>
                  <p className="text-sm leading-relaxed text-ink-600">{preview.tailored_summary}</p>
                </div>
                {preview.ordered_skills.length > 0 && (
                  <div>
                    <p className="section-label mb-2">Skills prioritized for this role</p>
                    <div className="flex flex-wrap gap-1.5">
                      {preview.ordered_skills.slice(0, 14).map((s, i) => (
                        <Badge key={s} variant={i < 5 ? "success" : "default"}>{s}</Badge>
                      ))}
                    </div>
                  </div>
                )}
                {preview.highlighted_projects.length > 0 && (
                  <div>
                    <p className="section-label mb-2">Highlighted projects</p>
                    <div className="flex flex-wrap gap-1.5">{preview.highlighted_projects.map((p) => <Badge key={p} variant="info">{p}</Badge>)}</div>
                  </div>
                )}
                {preview.key_achievements && preview.key_achievements.length > 0 && (
                  <div>
                    <p className="section-label mb-2">Key achievements for this role</p>
                    <ul className="space-y-1 text-sm text-ink-600">
                      {preview.key_achievements.map((a) => (
                        <li key={a} className="flex gap-2"><span className="text-brand-500">•</span>{a}</li>
                      ))}
                    </ul>
                  </div>
                )}
                {preview.tailoring_steps && preview.tailoring_steps.length > 0 && (
                  <div className="rounded-xl border border-violet-100 bg-violet-50/40 p-3.5">
                    <p className="section-label mb-2 text-violet-700">Tailoring steps</p>
                    <ol className="space-y-1.5">
                      {preview.tailoring_steps.map((step) => (
                        <li key={step.step} className="text-xs text-ink-600">
                          <span className="font-semibold text-ink-800">{step.title}:</span> {step.summary}
                        </li>
                      ))}
                    </ol>
                  </div>
                )}
                {preview.tailored_experience && preview.tailored_experience.length > 0 && (
                  <div>
                    <p className="section-label mb-2">Tailored experience (preview)</p>
                    <div className="space-y-3">
                      {preview.tailored_experience.slice(0, 2).map((exp) => (
                        <div key={`${exp.company}-${exp.role}`} className="rounded-lg border border-slate-200 bg-white/50 p-3">
                          <p className="text-sm font-semibold text-ink-800">{exp.role} · {exp.company}</p>
                          <ul className="mt-1.5 space-y-1 text-xs text-ink-500">
                            {exp.bullets.slice(0, 2).map((b) => <li key={b}>• {b}</li>)}
                          </ul>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Step 4: Prepare + Submit (gated) */}
      <AnimatePresence>
        {currentMatch && !submitted && (
          <motion.div initial={{ opacity: 0, y: 24 }} animate={{ opacity: 1, y: 0 }}>
            <Card>
              <CardContent className="space-y-5">
                {/* Activation checklist */}
                <div className="grid grid-cols-2 gap-x-4 gap-y-1.5 sm:grid-cols-4">
                  <ChecklistItem done={c.profile} label="Profile" />
                  <ChecklistItem done={c.jd} label="JD pasted" />
                  <ChecklistItem done={c.company} label="Company" />
                  <ChecklistItem done={c.role} label="Role" />
                  <ChecklistItem done={c.skillsRequired} label="Skills required" />
                  <ChecklistItem done={c.userSkills} label="Profile skills" />
                  <ChecklistItem done={c.match} label="Match calculated" />
                  <ChecklistItem done={resumeDownloaded} label="Resume downloaded" />
                </div>

                <div className="flex flex-col gap-3 sm:flex-row">
                  <Button onClick={handleDownloadResume} disabled={!canPrepare} loading={loading("generate")} className="flex-1">
                    <Download className="h-4 w-4" />
                    {loading("generate") ? "Generating Resume..." : "Prepare & Download Resume"}
                  </Button>
                  <Button variant={canSubmit ? "primary" : "secondary"} onClick={handleSubmit} disabled={!canSubmit} loading={loading("submit")} className="flex-1">
                    <CheckCircle2 className="h-4 w-4" /> Mark as Submitted
                  </Button>
                </div>
                <p className="text-center text-xs text-ink-400">
                  Apply on the company portal first, then click <span className="font-medium text-ink-600">Submitted</span> to log it. Submitted unlocks only after the resume is downloaded.
                </p>
              </CardContent>
            </Card>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Success */}
      <AnimatePresence>
        {submitted && (
          <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} className="py-8 text-center">
            <motion.div initial={{ scale: 0 }} animate={{ scale: 1 }} transition={{ type: "spring", stiffness: 300, damping: 20 }} className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-emerald-100">
              <CheckCircle2 className="h-8 w-8 text-emerald-600" />
            </motion.div>
            <h3 className="font-display text-xl font-bold text-ink-900">Application Logged</h3>
            <p className="mb-6 mt-1 text-sm text-ink-500">{currentCompany} → {currentRole} has been added to your tracker.</p>
            <div className="flex items-center justify-center gap-3">
              <Button onClick={() => setActiveTab("tracking")}>View in Tracker</Button>
              <Button variant="secondary" onClick={handleReset}><RefreshCw className="h-4 w-4" /> New Application</Button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

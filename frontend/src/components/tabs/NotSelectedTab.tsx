import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  XCircle, Brain, TrendingDown, TrendingUp, Lightbulb,
  ChevronDown, Clock, Sparkles, AlertCircle,
} from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Progress } from "@/components/ui/Progress";
import { AIThinkingAnimation } from "@/components/ui/Spinner";
import { useAppStore } from "@/hooks/useAppStore";
import { cn, formatRelativeTime, getMatchColor, INPUT_LIMITS, sanitizeUserInput } from "@/lib/utils";
import * as api from "@/lib/api";
import type { Application, SkillChange, ProfileUpdate } from "@/types";

interface RowAnalysis {
  summary: string;
  skill_changes: SkillChange[];
  recommendations: string[];
}

function SkillChangeRow({ change }: { change: SkillChange }) {
  const delta = change.new_confidence - change.previous_confidence;
  const isDown = delta < 0;
  return (
    <motion.div initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }} className="flex items-center gap-3 rounded-xl border border-slate-200 bg-white/60 p-3">
      <div className={cn("flex h-8 w-8 shrink-0 items-center justify-center rounded-lg", isDown ? "bg-rose-50" : "bg-emerald-50")}>
        {isDown ? <TrendingDown className="h-4 w-4 text-rose-500" /> : <TrendingUp className="h-4 w-4 text-emerald-500" />}
      </div>
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2">
          <span className="text-sm font-semibold text-ink-800">{change.skill}</span>
          <span className={cn("text-xs font-bold tabular-nums", isDown ? "text-rose-500" : "text-emerald-600")}>{delta > 0 ? "+" : ""}{delta.toFixed(0)}%</span>
        </div>
        <p className="truncate text-xs text-ink-400">{change.reason}</p>
      </div>
      <div className="flex shrink-0 items-center gap-1 text-xs tabular-nums">
        <span className="text-ink-400">{change.previous_confidence.toFixed(0)}%</span>
        <span className="text-ink-300">→</span>
        <span className={cn("font-bold", isDown ? "text-rose-500" : "text-emerald-600")}>{change.new_confidence.toFixed(0)}%</span>
      </div>
    </motion.div>
  );
}

function RejectionRow({ app, onAnalyzed }: { app: Application; onAnalyzed: () => void }) {
  const { profile, setProfile, isLoading, setLoading, addToast } = useAppStore();
  const [notes, setNotes] = useState("");
  const [result, setResult] = useState<RowAnalysis | null>(null);
  const busy = isLoading[`analyze-${app.id}`];

  // Load any previously saved rejection note/summary for this row.
  useEffect(() => {
    api.getRejection(app.id)
      .then((r) => {
        if (r.notes) setNotes(r.notes);
        if (r.summary) setResult((prev) => prev ?? { summary: r.summary || "", skill_changes: [], recommendations: [] });
      })
      .catch(() => { /* none yet */ });
  }, [app.id]);

  const analyze = async () => {
    if (!profile) { addToast({ type: "error", message: "Upload a profile first." }); return; }
    setLoading(`analyze-${app.id}`, true);
    setResult(null);
    try {
      const res = await api.analyzeRejection({
        application_id: app.id,
        notes: sanitizeUserInput(notes, INPUT_LIMITS.rejectionField),
      });
      setResult({ summary: res.summary, skill_changes: res.skill_changes, recommendations: res.recommendations });
      // refresh living profile
      try {
        const data = await api.getAllData();
        if (data.current_profile_state) setProfile(data.current_profile_state);
      } catch { /* ignore */ }
      addToast({ type: "success", message: `Analyzed rejection from ${app.company}.` });
      onAnalyzed();
    } catch (e: any) {
      addToast({ type: "error", message: e.message });
    } finally {
      setLoading(`analyze-${app.id}`, false);
    }
  };

  return (
    <Card>
      <div className="mb-4 flex items-start justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-slate-100 to-slate-200 text-sm font-bold text-ink-600">
            {app.company?.charAt(0).toUpperCase() || "?"}
          </div>
          <div>
            <p className="font-semibold text-ink-900">{app.company || "Unknown"}</p>
            <p className="text-xs text-ink-400">{app.role || "—"}</p>
          </div>
        </div>
        <div className="text-right">
          <p className="section-label">Experience Match</p>
          <p className={cn("font-display text-lg font-bold tabular-nums", getMatchColor(app.match_percentage))}>{app.match_percentage.toFixed(0)}%</p>
        </div>
      </div>

      <label className="section-label mb-1.5 block">Rejection Notes</label>
      <textarea
        className="input-field resize-none"
        rows={4}
        placeholder="Write freely: interview experience, questions you couldn't answer, topics you felt weak in, the rejection email, recruiter feedback, anything you observed..."
        value={notes}
        onChange={(e) => setNotes(e.target.value)}
        maxLength={INPUT_LIMITS.rejectionField}
      />

      <div className="mt-3 flex items-center justify-between gap-3">
        {app.missing_skills.length > 0 && (
          <div className="flex flex-wrap gap-1">
            {app.missing_skills.slice(0, 4).map((s) => <Badge key={s} variant="danger" className="text-[10px]">{s}</Badge>)}
          </div>
        )}
        <Button onClick={analyze} disabled={!notes.trim() || busy} loading={busy} className="ml-auto">
          <Brain className="h-4 w-4" /> {busy ? "Analyzing..." : "Analyze"}
        </Button>
      </div>

      <AnimatePresence>
        {busy && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
            <AIThinkingAnimation label="Learning from this rejection..." />
          </motion.div>
        )}
        {result && !busy && (
          <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="mt-4 space-y-3 border-t border-slate-200 pt-4">
            {result.summary && (
              <div className="rounded-xl border border-brand-200 bg-brand-50/60 p-3.5">
                <p className="section-label mb-1 flex items-center gap-1.5 text-brand-700"><Sparkles className="h-3.5 w-3.5" /> Analysis</p>
                <p className="text-sm leading-relaxed text-ink-700">{result.summary}</p>
              </div>
            )}
            {result.skill_changes.length > 0 && (
              <div className="space-y-2">
                <p className="section-label">Profile changes</p>
                {result.skill_changes.map((c, i) => <SkillChangeRow key={i} change={c} />)}
              </div>
            )}
            {result.recommendations.length > 0 && (
              <div>
                <p className="section-label mb-2 flex items-center gap-1.5"><Lightbulb className="h-3.5 w-3.5 text-amber-500" /> Recommendations</p>
                <ul className="space-y-2">
                  {result.recommendations.map((r, i) => (
                    <li key={i} className="flex items-start gap-2.5 rounded-lg border border-amber-100 bg-amber-50/60 p-2.5 text-sm text-ink-700">
                      <span className="mt-0.5 shrink-0 font-bold text-amber-600">{i + 1}.</span>{r}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </Card>
  );
}

function ProfileUpdateCard({ update }: { update: ProfileUpdate }) {
  const [expanded, setExpanded] = useState(false);
  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="glass glass-edge overflow-hidden">
      <button className="flex w-full items-center justify-between p-4 text-left transition-colors hover:bg-white/60 cursor-pointer" onClick={() => setExpanded(!expanded)}>
        <div className="flex items-center gap-3">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-violet-100"><Brain className="h-4 w-4 text-violet-600" /></div>
          <div>
            <p className="text-sm font-semibold text-ink-800">Updated after {update.company}</p>
            <p className="text-xs text-ink-400">{formatRelativeTime(update.timestamp)}</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant={update.changes.length > 0 ? "danger" : "default"}>{update.changes.length} changes</Badge>
          <ChevronDown className={cn("h-4 w-4 text-ink-400 transition-transform", expanded && "rotate-180")} />
        </div>
      </button>
      <AnimatePresence>
        {expanded && (
          <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: "auto", opacity: 1 }} exit={{ height: 0, opacity: 0 }} className="overflow-hidden">
            <div className="space-y-3 border-t border-slate-200 px-4 pb-4 pt-3">
              {update.changes.map((c, i) => <SkillChangeRow key={i} change={c} />)}
              {update.recommendations.length > 0 && (
                <ul className="space-y-1.5">
                  {update.recommendations.map((r, i) => (
                    <li key={i} className="flex items-start gap-2 text-sm text-ink-600"><Lightbulb className="mt-0.5 h-3.5 w-3.5 shrink-0 text-amber-500" />{r}</li>
                  ))}
                </ul>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}

export function NotSelectedTab() {
  const { applications, profile, profileHistory, setProfileHistory, setActiveTab } = useAppStore();

  const refreshHistory = () => { api.getProfileHistory().then(setProfileHistory).catch(() => {}); };
  useEffect(() => { refreshHistory(); }, []);

  const rejected = applications.filter((a) => a.status === "not_selected");

  return (
    <div className="mx-auto w-full max-w-6xl space-y-6 p-4 py-6 sm:p-6">
      <div className="space-y-2">
        <Badge variant="danger" className="text-[10px]"><Brain className="h-2.5 w-2.5" /> Learning Engine</Badge>
        <h1 className="font-display text-3xl font-bold tracking-tightest text-ink-900 sm:text-4xl">
          Learn from <span className="gradient-text-brand">Rejections</span>
        </h1>
        <p className="max-w-2xl text-sm leading-relaxed text-ink-500">
          Each rejected application appears here. Write notes freely and click Analyze — the AI recalibrates your living profile and suggests what to improve.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-5">
        {/* Left: per-row rejections */}
        <div className="space-y-4 lg:col-span-3">
          {rejected.length === 0 ? (
            <Card>
              <div className="flex flex-col items-center py-12 text-center">
                <div className="mb-3 flex h-14 w-14 items-center justify-center rounded-2xl bg-slate-100"><XCircle className="h-7 w-7 text-ink-400" /></div>
                <h3 className="font-display text-base font-semibold text-ink-800">No rejections to analyze</h3>
                <p className="mt-1 max-w-xs text-sm text-ink-500">
                  Mark an application as <span className="font-medium text-rose-600">Not Selected</span> in the{" "}
                  <button onClick={() => setActiveTab("tracking")} className="font-medium text-brand-600 hover:underline">Tracking</button> tab to start learning.
                </p>
              </div>
            </Card>
          ) : (
            <>
              {!profile && (
                <div className="flex items-center gap-2 rounded-xl border border-amber-200 bg-amber-50 p-3 text-xs text-amber-700">
                  <AlertCircle className="h-4 w-4 shrink-0" /> Upload your profile in the Apply tab so analysis can update it.
                </div>
              )}
              {rejected.map((app) => <RejectionRow key={app.id} app={app} onAnalyzed={refreshHistory} />)}
            </>
          )}
        </div>

        {/* Right: evolution + live skills */}
        <div className="space-y-4 lg:col-span-2">
          <Card>
            <CardHeader><CardTitle className="flex items-center gap-2 text-base"><Clock className="h-4 w-4 text-brand-600" /> Profile Evolution</CardTitle></CardHeader>
            <CardContent>
              {profileHistory.length === 0 ? (
                <div className="py-8 text-center">
                  <Brain className="mx-auto mb-2 h-8 w-8 text-slate-300" />
                  <p className="text-sm text-ink-500">No updates yet.<br />Analyze a rejection to start evolving.</p>
                </div>
              ) : (
                <div className="max-h-[55vh] space-y-3 overflow-y-auto pr-1">
                  {profileHistory.map((u) => <ProfileUpdateCard key={u.id} update={u} />)}
                </div>
              )}
            </CardContent>
          </Card>

          {profile && (
            <Card>
              <CardHeader><CardTitle className="text-base">Current Skill Confidence</CardTitle></CardHeader>
              <CardContent>
                <div className="max-h-64 space-y-2.5 overflow-y-auto pr-1">
                  {[...profile.skills].sort((a, b) => b.confidence - a.confidence).slice(0, 12).map((s) => (
                    <div key={s.name} className="flex items-center gap-3">
                      <span className="w-28 shrink-0 truncate text-xs text-ink-600">{s.name}</span>
                      <Progress value={s.confidence} colorByValue size="sm" className="flex-1" />
                      <span className="w-9 shrink-0 text-right text-xs font-bold text-ink-500 tabular-nums">{s.confidence.toFixed(0)}%</span>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}

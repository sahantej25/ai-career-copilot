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
import { cn, formatRelativeTime } from "@/lib/utils";
import * as api from "@/lib/api";
import type { Application, SkillChange, ProfileUpdate } from "@/types";

function SkillChangeRow({ change }: { change: SkillChange }) {
  const delta = change.new_confidence - change.previous_confidence;
  const isDown = delta < 0;

  return (
    <motion.div
      initial={{ opacity: 0, x: -10 }}
      animate={{ opacity: 1, x: 0 }}
      className="flex items-center gap-3 p-3 bg-slate-800/40 rounded-xl"
    >
      <div className={cn(
        "w-8 h-8 rounded-lg flex items-center justify-center shrink-0",
        isDown ? "bg-red-500/15" : "bg-emerald-500/15"
      )}>
        {isDown
          ? <TrendingDown className="w-4 h-4 text-red-400" />
          : <TrendingUp className="w-4 h-4 text-emerald-400" />
        }
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className="text-sm font-semibold text-slate-200">{change.skill}</span>
          <span className={cn(
            "text-xs font-bold",
            isDown ? "text-red-400" : "text-emerald-400"
          )}>
            {delta > 0 ? "+" : ""}{delta.toFixed(0)}%
          </span>
        </div>
        <p className="text-xs text-slate-500 truncate">{change.reason}</p>
      </div>
      <div className="flex items-center gap-1 shrink-0">
        <span className="text-xs text-slate-500">{change.previous_confidence.toFixed(0)}%</span>
        <span className="text-slate-600">→</span>
        <span className={cn("text-xs font-bold", isDown ? "text-red-400" : "text-emerald-400")}>
          {change.new_confidence.toFixed(0)}%
        </span>
      </div>
    </motion.div>
  );
}

function ProfileUpdateCard({ update }: { update: ProfileUpdate }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="glass-card"
    >
      <button
        className="w-full flex items-center justify-between p-4 text-left"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-purple-500/15 flex items-center justify-center">
            <Brain className="w-4 h-4 text-purple-400" />
          </div>
          <div>
            <p className="text-sm font-semibold text-slate-200">
              Profile updated after {update.company}
            </p>
            <p className="text-xs text-slate-500">{formatRelativeTime(update.timestamp)}</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant={update.changes.length > 0 ? "danger" : "default"}>
            {update.changes.length} changes
          </Badge>
          <ChevronDown className={cn("w-4 h-4 text-slate-500 transition-transform", expanded && "rotate-180")} />
        </div>
      </button>

      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="overflow-hidden"
          >
            <div className="px-4 pb-4 space-y-3 border-t border-slate-800/60 pt-3">
              {update.changes.length > 0 && (
                <div className="space-y-2">
                  <p className="section-label">Skill Changes</p>
                  {update.changes.map((c, i) => (
                    <SkillChangeRow key={i} change={c} />
                  ))}
                </div>
              )}
              {update.recommendations.length > 0 && (
                <div>
                  <p className="section-label mb-2">Recommendations</p>
                  <ul className="space-y-1.5">
                    {update.recommendations.map((r, i) => (
                      <li key={i} className="flex items-start gap-2 text-sm text-slate-300">
                        <Lightbulb className="w-3.5 h-3.5 text-amber-400 shrink-0 mt-0.5" />
                        {r}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}

export function NotSelectedTab() {
  const {
    applications, profile, profileHistory, setProfileHistory,
    setProfile, addToast, isLoading, setLoading,
  } = useAppStore();

  const [selectedAppId, setSelectedAppId] = useState<string>("");
  const [form, setForm] = useState({
    interview_experience: "",
    rejection_email: "",
    topics_struggled: "",
    missing_skills: "",
    recruiter_feedback: "",
  });
  const [analysisResult, setAnalysisResult] = useState<{
    skill_changes: SkillChange[];
    recommendations: string[];
    summary: string;
  } | null>(null);

  const rejectedApps = applications.filter(
    (a) => a.status === "not_selected" || a.status === "submitted" || a.status === "interview"
  );

  const selectedApp = applications.find((a) => a.id === selectedAppId);

  useEffect(() => {
    // Load profile history from backend
    api.getProfileHistory()
      .then(setProfileHistory)
      .catch(() => {});
  }, []);

  const handleAnalyze = async () => {
    if (!selectedAppId) return;
    setLoading("analyze", true);
    setAnalysisResult(null);
    try {
      const result = await api.analyzeRejection({
        application_id: selectedAppId,
        ...form,
      });
      setAnalysisResult({
        skill_changes: result.skill_changes,
        recommendations: result.recommendations,
        summary: result.summary,
      });
      // Update profile in store
      if (profile) {
        // Re-fetch updated profile via full data
        const data = await api.getAllData();
        if (data.current_profile_state) setProfile(data.current_profile_state);
      }
      setProfileHistory([result.profile_update, ...profileHistory]);
      addToast({ type: "success", message: "Rejection analyzed & profile updated!" });

      // Clear form
      setForm({ interview_experience: "", rejection_email: "", topics_struggled: "", missing_skills: "", recruiter_feedback: "" });
    } catch (e: any) {
      addToast({ type: "error", message: e.message });
    } finally {
      setLoading("analyze", false);
    }
  };

  const isAnalyzing = isLoading["analyze"];

  const textAreaClasses = "input-field resize-none text-sm";

  return (
    <div className="p-6 space-y-6 max-w-4xl">
      {/* Title */}
      <div>
        <h1 className="text-2xl font-bold gradient-text">Not Selected — Learn & Grow</h1>
        <p className="text-slate-400 text-sm mt-1">
          Turn every rejection into intelligence. AI analyzes your feedback and evolves your profile.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
        {/* Left: Rejection form */}
        <div className="lg:col-span-3 space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <XCircle className="w-5 h-5 text-red-400" />
                Log Rejection Feedback
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Application selector */}
              <div>
                <label className="section-label block mb-1.5">Select Application</label>
                <select
                  className="input-field"
                  value={selectedAppId}
                  onChange={(e) => setSelectedAppId(e.target.value)}
                >
                  <option value="">Choose an application...</option>
                  {rejectedApps.map((a) => (
                    <option key={a.id} value={a.id}>
                      {a.company} — {a.role} ({a.status.replace("_", " ")})
                    </option>
                  ))}
                </select>
                {rejectedApps.length === 0 && (
                  <p className="text-xs text-slate-500 mt-1 flex items-center gap-1">
                    <AlertCircle className="w-3 h-3" />
                    No applications found. Submit one in the Apply tab first.
                  </p>
                )}
              </div>

              {selectedApp && (
                <div className="flex items-center gap-3 p-3 bg-red-500/5 border border-red-500/20 rounded-xl">
                  <div className="w-8 h-8 rounded-lg bg-slate-800 flex items-center justify-center text-sm font-bold text-slate-300">
                    {selectedApp.company?.charAt(0)}
                  </div>
                  <div>
                    <p className="text-sm font-medium text-slate-200">{selectedApp.company}</p>
                    <p className="text-xs text-slate-500">{selectedApp.role} · {selectedApp.match_percentage.toFixed(0)}% match</p>
                  </div>
                  <div className="ml-auto flex flex-wrap gap-1">
                    {selectedApp.missing_skills.slice(0, 3).map((s) => (
                      <Badge key={s} variant="danger" className="text-[10px]">{s}</Badge>
                    ))}
                  </div>
                </div>
              )}

              {/* Feedback fields */}
              <div>
                <label className="section-label block mb-1.5">Interview Experience</label>
                <textarea
                  className={textAreaClasses}
                  rows={3}
                  placeholder="Describe the interview process, rounds, topics asked..."
                  value={form.interview_experience}
                  onChange={(e) => setForm({ ...form, interview_experience: e.target.value })}
                />
              </div>
              <div>
                <label className="section-label block mb-1.5">Rejection Email / Feedback</label>
                <textarea
                  className={textAreaClasses}
                  rows={3}
                  placeholder="Paste the rejection email or summarize what they said..."
                  value={form.rejection_email}
                  onChange={(e) => setForm({ ...form, rejection_email: e.target.value })}
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="section-label block mb-1.5">Topics You Struggled With</label>
                  <textarea
                    className={textAreaClasses}
                    rows={3}
                    placeholder="System design, coding, behavioral..."
                    value={form.topics_struggled}
                    onChange={(e) => setForm({ ...form, topics_struggled: e.target.value })}
                  />
                </div>
                <div>
                  <label className="section-label block mb-1.5">Missing Skills You Noticed</label>
                  <textarea
                    className={textAreaClasses}
                    rows={3}
                    placeholder="Docker, Kubernetes, React..."
                    value={form.missing_skills}
                    onChange={(e) => setForm({ ...form, missing_skills: e.target.value })}
                  />
                </div>
              </div>
              <div>
                <label className="section-label block mb-1.5">Recruiter Feedback</label>
                <textarea
                  className={textAreaClasses}
                  rows={2}
                  placeholder="Any direct feedback from the recruiter or hiring manager..."
                  value={form.recruiter_feedback}
                  onChange={(e) => setForm({ ...form, recruiter_feedback: e.target.value })}
                />
              </div>

              <Button
                onClick={handleAnalyze}
                disabled={!selectedAppId || !profile}
                loading={isAnalyzing}
                className="w-full"
              >
                <Brain className="w-4 h-4" />
                {isAnalyzing ? "AI is analyzing..." : "Analyze & Update Profile"}
              </Button>

              {!profile && (
                <p className="text-xs text-amber-400 text-center flex items-center justify-center gap-1">
                  <AlertCircle className="w-3 h-3" />
                  Upload a resume in the Apply tab first.
                </p>
              )}
            </CardContent>
          </Card>

          {/* AI Analysis Result */}
          <AnimatePresence>
            {isAnalyzing && (
              <Card>
                <CardContent>
                  <AIThinkingAnimation label="Learning from your rejection feedback..." />
                </CardContent>
              </Card>
            )}

            {analysisResult && !isAnalyzing && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
              >
                <Card className="border-indigo-500/20">
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Sparkles className="w-5 h-5 text-indigo-400" />
                      AI Analysis Results
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="p-3 bg-indigo-500/8 border border-indigo-500/20 rounded-xl">
                      <p className="text-sm text-slate-300">{analysisResult.summary}</p>
                    </div>

                    {analysisResult.skill_changes.length > 0 && (
                      <div>
                        <p className="section-label mb-2">Profile Changes</p>
                        <div className="space-y-2">
                          {analysisResult.skill_changes.map((c, i) => (
                            <SkillChangeRow key={i} change={c} />
                          ))}
                        </div>
                      </div>
                    )}

                    {analysisResult.recommendations.length > 0 && (
                      <div>
                        <p className="section-label mb-2 flex items-center gap-1.5">
                          <Lightbulb className="w-3.5 h-3.5 text-amber-400" />
                          Action Recommendations
                        </p>
                        <ul className="space-y-2">
                          {analysisResult.recommendations.map((r, i) => (
                            <motion.li
                              key={i}
                              initial={{ opacity: 0, x: -10 }}
                              animate={{ opacity: 1, x: 0 }}
                              transition={{ delay: i * 0.08 }}
                              className="flex items-start gap-2 text-sm text-slate-300 p-2.5 bg-amber-500/5 border border-amber-500/15 rounded-lg"
                            >
                              <span className="text-amber-400 font-bold shrink-0 mt-0.5">{i + 1}.</span>
                              {r}
                            </motion.li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </CardContent>
                </Card>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* Right: Profile evolution timeline */}
        <div className="lg:col-span-2 space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base">
                <Clock className="w-4 h-4 text-indigo-400" />
                Profile Evolution
              </CardTitle>
            </CardHeader>
            <CardContent>
              {profileHistory.length === 0 ? (
                <div className="text-center py-8">
                  <Brain className="w-8 h-8 text-slate-700 mx-auto mb-2" />
                  <p className="text-sm text-slate-500">
                    No profile updates yet.<br />
                    Analyze a rejection to start evolving.
                  </p>
                </div>
              ) : (
                <div className="space-y-3 max-h-[60vh] overflow-y-auto pr-1">
                  {profileHistory.map((upd) => (
                    <ProfileUpdateCard key={upd.id} update={upd} />
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Current profile skills (live) */}
          {profile && (
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Current Skill Confidence</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2 max-h-64 overflow-y-auto pr-1">
                  {[...profile.skills]
                    .sort((a, b) => b.confidence - a.confidence)
                    .slice(0, 12)
                    .map((s) => (
                      <div key={s.name} className="flex items-center gap-3">
                        <span className="text-xs text-slate-400 w-28 truncate shrink-0">{s.name}</span>
                        <Progress
                          value={s.confidence}
                          colorByValue
                          size="sm"
                          className="flex-1"
                        />
                        <span className="text-xs font-bold text-slate-400 w-8 text-right shrink-0">
                          {s.confidence.toFixed(0)}%
                        </span>
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

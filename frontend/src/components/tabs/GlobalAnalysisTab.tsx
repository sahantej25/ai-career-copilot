import { useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
  ResponsiveContainer, Tooltip as RechartsTooltip,
} from "recharts";
import {
  BarChart3, RefreshCw, Lightbulb, AlertTriangle,
  MessageSquare, TrendingUp, Target, Sparkles, Clock,
} from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { AIThinkingAnimation } from "@/components/ui/Spinner";
import { useAppStore } from "@/hooks/useAppStore";
import { cn, formatRelativeTime } from "@/lib/utils";
import * as api from "@/lib/api";

function RadarChartSection({ data }: { data: { subject: string; value: number; full_mark: number }[] }) {
  if (!data.length) return null;
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2.5">
          <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-brand-100 text-brand-700"><Target className="h-4 w-4" /></span>
          Skill Radar
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="h-72">
          <ResponsiveContainer width="100%" height="100%">
            <RadarChart data={data}>
              <defs>
                <linearGradient id="radarFill" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#10b981" stopOpacity={0.45} />
                  <stop offset="100%" stopColor="#14b8a6" stopOpacity={0.1} />
                </linearGradient>
              </defs>
              <PolarGrid stroke="rgba(15,23,42,0.08)" />
              <PolarAngleAxis dataKey="subject" tick={{ fill: "#475569", fontSize: 11 }} />
              <PolarRadiusAxis angle={90} domain={[0, 100]} tick={{ fill: "#94a3b8", fontSize: 9 }} tickCount={5} axisLine={false} />
              <Radar name="Current Skills" dataKey="value" stroke="#10b981" fill="url(#radarFill)" fillOpacity={1} strokeWidth={2} dot={{ r: 3, fill: "#10b981", strokeWidth: 0 }} />
              <RechartsTooltip
                contentStyle={{ backgroundColor: "rgba(255,255,255,0.95)", backdropFilter: "blur(12px)", border: "1px solid rgba(15,23,42,0.1)", borderRadius: "12px", color: "#0f172a", fontSize: "12px", boxShadow: "0 8px 24px -8px rgba(2,6,23,0.2)" }}
                formatter={(v: number) => [`${v}%`, "Score"]}
              />
            </RadarChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  );
}

function InsightCard({ icon, title, items, variant }: {
  icon: React.ReactNode; title: string; items: string[];
  variant: "danger" | "warning" | "info" | "success";
}) {
  const iconBg = {
    danger: "bg-rose-50 text-rose-600",
    warning: "bg-amber-50 text-amber-600",
    info: "bg-sky-50 text-sky-600",
    success: "bg-emerald-50 text-emerald-600",
  };
  const itemStyle = {
    danger: "border-rose-100 bg-rose-50/60 text-ink-700",
    warning: "border-amber-100 bg-amber-50/60 text-ink-700",
    info: "border-sky-100 bg-sky-50/60 text-ink-700",
    success: "border-emerald-100 bg-emerald-50/60 text-ink-700",
  };
  return (
    <Card>
      <CardHeader className="mb-4">
        <CardTitle className="flex items-center gap-2.5 text-base">
          <span className={cn("flex h-8 w-8 items-center justify-center rounded-lg", iconBg[variant])}>{icon}</span>
          {title}
          <Badge variant={variant} className="ml-auto">{items.length}</Badge>
        </CardTitle>
      </CardHeader>
      <CardContent>
        {items.length === 0 ? (
          <p className="py-4 text-center text-sm text-ink-400">None identified yet.</p>
        ) : (
          <ul className="space-y-2">
            {items.map((item, i) => (
              <motion.li key={i} initial={{ opacity: 0, x: -8 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: i * 0.06 }} className={cn("flex items-start gap-2 rounded-lg border p-2.5 text-sm", itemStyle[variant])}>
                <span className="mt-0.5 shrink-0 font-bold opacity-60">{i + 1}.</span>{item}
              </motion.li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  );
}

function CompanySkillMatrix({ applications }: { applications: { company: string; missing_skills: string[] }[] }) {
  const relevant = applications.filter((a) => a.missing_skills.length > 0).slice(0, 6);
  if (!relevant.length) return null;
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2.5 text-base">
          <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-brand-100 text-brand-700"><BarChart3 className="h-4 w-4" /></span>
          Skill Gap by Company
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {relevant.map((app) => (
            <div key={app.company} className="flex items-start gap-3 rounded-xl border border-slate-200 bg-white/50 p-3">
              <span className="w-24 shrink-0 truncate pt-0.5 text-xs font-medium text-ink-700">{app.company}</span>
              <div className="flex flex-1 flex-wrap gap-1.5">
                {app.missing_skills.slice(0, 6).map((s) => <Badge key={s} variant="danger" className="text-[10px]">{s}</Badge>)}
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

export function GlobalAnalysisTab() {
  const { globalAnalysis, setGlobalAnalysis, applications, profile, addToast, isLoading, setLoading, setProfileModalOpen } = useAppStore();

  const fetchAnalysis = async () => {
    try { setGlobalAnalysis(await api.getGlobalAnalysis()); } catch { /* none yet */ }
  };
  useEffect(() => { fetchAnalysis(); }, []);

  const handleRefresh = async () => {
    setLoading("global", true);
    try {
      setGlobalAnalysis(await api.refreshGlobalAnalysis());
      addToast({ type: "success", message: "Global analysis refreshed!" });
    } catch (e: any) {
      addToast({ type: "error", message: e.message });
    } finally {
      setLoading("global", false);
    }
  };

  const busy = isLoading["global"];
  const rejected = applications.filter((a) => a.status === "not_selected");
  const canRun = rejected.length > 0 && !!profile;

  const stats = [
    { label: "Total Applied", value: applications.length, icon: <Target className="h-4 w-4" />, color: "text-sky-600", bg: "bg-sky-50" },
    { label: "Rejections", value: rejected.length, icon: <AlertTriangle className="h-4 w-4" />, color: "text-rose-600", bg: "bg-rose-50" },
    { label: "Missing Skills", value: globalAnalysis?.recurring_missing_skills.length ?? "—", icon: <TrendingUp className="h-4 w-4" />, color: "text-amber-600", bg: "bg-amber-50" },
    { label: "Recommendations", value: globalAnalysis?.career_recommendations.length ?? "—", icon: <Lightbulb className="h-4 w-4" />, color: "text-emerald-600", bg: "bg-emerald-50" },
  ];

  return (
    <div className="space-y-6 p-4 py-6 sm:p-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div className="space-y-2">
          <Badge variant="purple" className="text-[10px]"><Sparkles className="h-2.5 w-2.5" /> Macro Insights</Badge>
          <h1 className="font-display text-3xl font-bold tracking-tightest text-ink-900 sm:text-4xl">
            Global Career <span className="gradient-text-brand">Analysis</span>
          </h1>
          <p className="text-sm text-ink-500">Consolidated patterns across every rejection — what to focus on before your next round.</p>
        </div>
        <Button onClick={handleRefresh} loading={busy} disabled={!canRun} className="shrink-0">
          <RefreshCw className={cn("h-4 w-4", busy && "animate-spin")} />
          {busy ? "Analyzing..." : "Run Global Analysis"}
        </Button>
      </div>

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        {stats.map((s, i) => (
          <motion.div key={s.label} initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.06 }} className="glass glass-edge glass-hover p-4">
            <div className={cn("mb-2 flex h-8 w-8 items-center justify-center rounded-lg", s.bg, s.color)}>{s.icon}</div>
            <p className={cn("font-display text-2xl font-bold tabular-nums", s.color)}>{s.value}</p>
            <p className="mt-0.5 text-xs text-ink-400">{s.label}</p>
          </motion.div>
        ))}
      </div>

      <AnimatePresence>
        {busy && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
            <Card><CardContent><AIThinkingAnimation label="Analyzing patterns across all rejections..." /></CardContent></Card>
          </motion.div>
        )}
      </AnimatePresence>

      {!globalAnalysis && !busy && (
        <div className="glass glass-edge flex flex-col items-center py-20 text-center">
          <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-slate-100"><BarChart3 className="h-8 w-8 text-ink-400" /></div>
          <h3 className="font-display text-lg font-semibold text-ink-800">No analysis yet</h3>
          <p className="mx-auto mt-1 max-w-sm text-sm text-ink-500">
            {!profile
              ? "Add your candidate profile first — use the Profile button in the header or Living Profile card in the sidebar."
              : rejected.length === 0
              ? "Mark applications as Not Selected in Tracking — patterns emerge across multiple rejections."
              : "Click 'Run Global Analysis' to generate consolidated insights."}
          </p>
          {!profile && (
            <Button onClick={() => setProfileModalOpen(true)} className="mt-5">
              <Sparkles className="h-4 w-4" /> Add profile
            </Button>
          )}
          {profile && rejected.length > 0 && <Button onClick={handleRefresh} className="mt-5"><Sparkles className="h-4 w-4" /> Generate Analysis</Button>}
        </div>
      )}

      {globalAnalysis && !busy && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-5">
          <div className="flex items-center gap-1.5 text-xs text-ink-400"><Clock className="h-3 w-3" /> Last updated {formatRelativeTime(globalAnalysis.last_updated)}</div>

          {/* Summary paragraph (PRD §10.2) */}
          {globalAnalysis.summary && (
            <Card glow className="border-brand-200">
              <CardHeader className="mb-3">
                <CardTitle className="flex items-center gap-2.5 text-base">
                  <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-brand-100 text-brand-700"><Sparkles className="h-4 w-4" /></span>
                  Summary Recommendation
                </CardTitle>
              </CardHeader>
              <CardContent><p className="text-[15px] leading-relaxed text-ink-700">{globalAnalysis.summary}</p></CardContent>
            </Card>
          )}

          <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
            {globalAnalysis.skill_radar_data.length > 0 && <RadarChartSection data={globalAnalysis.skill_radar_data} />}
            <InsightCard icon={<AlertTriangle className="h-4 w-4" />} title="Recurring Missing Skills" items={globalAnalysis.recurring_missing_skills} variant="danger" />
          </div>

          <div className="grid grid-cols-1 gap-5 lg:grid-cols-3">
            <InsightCard icon={<MessageSquare className="h-4 w-4" />} title="Common Interview Topics" items={globalAnalysis.common_interview_topics} variant="warning" />
            <InsightCard icon={<TrendingUp className="h-4 w-4" />} title="Frequent Weaknesses" items={globalAnalysis.frequent_weaknesses} variant="info" />
            <InsightCard icon={<Lightbulb className="h-4 w-4" />} title="Career Recommendations" items={globalAnalysis.career_recommendations} variant="success" />
          </div>

          <CompanySkillMatrix applications={applications.filter((a) => a.status === "not_selected")} />
        </motion.div>
      )}
    </div>
  );
}

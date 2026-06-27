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
        <CardTitle className="flex items-center gap-2">
          <Target className="w-5 h-5 text-indigo-400" />
          Skill Radar
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <RadarChart data={data}>
              <PolarGrid stroke="#334155" />
              <PolarAngleAxis
                dataKey="subject"
                tick={{ fill: "#94a3b8", fontSize: 11 }}
              />
              <PolarRadiusAxis
                angle={90}
                domain={[0, 100]}
                tick={{ fill: "#475569", fontSize: 9 }}
                tickCount={5}
              />
              <Radar
                name="Current Skills"
                dataKey="value"
                stroke="#6366f1"
                fill="#6366f1"
                fillOpacity={0.25}
                strokeWidth={2}
              />
              <RechartsTooltip
                contentStyle={{
                  backgroundColor: "#1e293b",
                  border: "1px solid #334155",
                  borderRadius: "8px",
                  color: "#f1f5f9",
                  fontSize: "12px",
                }}
                formatter={(v: number) => [`${v}%`, "Score"]}
              />
            </RadarChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  );
}

function InsightCard({
  icon, title, items, variant,
}: {
  icon: React.ReactNode;
  title: string;
  items: string[];
  variant: "danger" | "warning" | "info" | "success";
}) {
  const colorMap = {
    danger: "text-red-400 bg-red-500/10 border-red-500/20",
    warning: "text-amber-400 bg-amber-500/10 border-amber-500/20",
    info: "text-blue-400 bg-blue-500/10 border-blue-500/20",
    success: "text-emerald-400 bg-emerald-500/10 border-emerald-500/20",
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base">
          <span className={cn(
            "w-7 h-7 rounded-lg flex items-center justify-center",
            colorMap[variant].split(" ").slice(1).join(" ")
          )}>
            {icon}
          </span>
          {title}
          <Badge variant={variant} className="ml-auto">
            {items.length}
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent>
        {items.length === 0 ? (
          <p className="text-sm text-slate-500 text-center py-4">None identified yet.</p>
        ) : (
          <ul className="space-y-2">
            {items.map((item, i) => (
              <motion.li
                key={i}
                initial={{ opacity: 0, x: -8 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.06 }}
                className={cn(
                  "flex items-start gap-2 text-sm p-2.5 rounded-lg border",
                  colorMap[variant]
                )}
              >
                <span className="font-bold shrink-0 mt-0.5">{i + 1}.</span>
                {item}
              </motion.li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  );
}

function CompanySkillMatrix({ applications }: { applications: { company: string; missing_skills: string[] }[] }) {
  const relevant = applications.filter((a) => a.missing_skills.length > 0).slice(0, 5);
  if (!relevant.length) return null;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base">
          <BarChart3 className="w-4 h-4 text-indigo-400" />
          Skill Gap by Company
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {relevant.map((app) => (
            <div key={app.company} className="flex items-start gap-3">
              <span className="text-xs text-slate-400 w-24 truncate pt-1 shrink-0">{app.company}</span>
              <div className="flex flex-wrap gap-1.5 flex-1">
                {app.missing_skills.slice(0, 5).map((s) => (
                  <Badge key={s} variant="danger" className="text-[10px]">{s}</Badge>
                ))}
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

export function GlobalAnalysisTab() {
  const {
    globalAnalysis, setGlobalAnalysis, applications,
    addToast, isLoading, setLoading,
  } = useAppStore();

  const fetchAnalysis = async () => {
    try {
      const data = await api.getGlobalAnalysis();
      setGlobalAnalysis(data);
    } catch {
      // No analysis yet — that's OK
    }
  };

  useEffect(() => { fetchAnalysis(); }, []);

  const handleRefresh = async () => {
    setLoading("global", true);
    try {
      const data = await api.refreshGlobalAnalysis();
      setGlobalAnalysis(data);
      addToast({ type: "success", message: "Global analysis refreshed!" });
    } catch (e: any) {
      addToast({ type: "error", message: e.message });
    } finally {
      setLoading("global", false);
    }
  };

  const isLoading_ = isLoading["global"];
  const rejected = applications.filter((a) => a.status === "not_selected");

  return (
    <div className="p-6 space-y-6">
      {/* Title */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold gradient-text">Global Career Analysis</h1>
          <p className="text-slate-400 text-sm mt-1">
            AI identifies macro patterns across all your rejections.
          </p>
        </div>
        <Button
          onClick={handleRefresh}
          loading={isLoading_}
          disabled={rejected.length === 0}
          className="shrink-0"
        >
          <RefreshCw className={cn("w-4 h-4", isLoading_ && "animate-spin")} />
          {isLoading_ ? "Analyzing..." : "Refresh Analysis"}
        </Button>
      </div>

      {/* Summary stats */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {[
          { label: "Total Applied", value: applications.length, icon: <Target className="w-4 h-4" />, color: "text-blue-400" },
          { label: "Rejections Analyzed", value: rejected.length, icon: <AlertTriangle className="w-4 h-4" />, color: "text-red-400" },
          { label: "Missing Skills", value: globalAnalysis?.recurring_missing_skills.length ?? "—", icon: <TrendingUp className="w-4 h-4" />, color: "text-amber-400" },
          { label: "Recommendations", value: globalAnalysis?.career_recommendations.length ?? "—", icon: <Lightbulb className="w-4 h-4" />, color: "text-emerald-400" },
        ].map((s) => (
          <motion.div
            key={s.label}
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="glass-card p-4 text-center"
          >
            <div className={cn("flex justify-center mb-1", s.color)}>{s.icon}</div>
            <p className={cn("text-2xl font-black", s.color)}>{s.value}</p>
            <p className="text-xs text-slate-500 mt-0.5">{s.label}</p>
          </motion.div>
        ))}
      </div>

      {/* Loading state */}
      <AnimatePresence>
        {isLoading_ && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
          >
            <Card>
              <CardContent>
                <AIThinkingAnimation label="Analyzing patterns across all rejections..." />
              </CardContent>
            </Card>
          </motion.div>
        )}
      </AnimatePresence>

      {/* No data state */}
      {!globalAnalysis && !isLoading_ && (
        <div className="text-center py-20">
          <div className="w-16 h-16 rounded-2xl bg-slate-800 flex items-center justify-center mx-auto mb-4">
            <BarChart3 className="w-8 h-8 text-slate-600" />
          </div>
          <h3 className="text-lg font-semibold text-slate-300">No analysis yet</h3>
          <p className="text-slate-500 text-sm mt-1 max-w-sm mx-auto">
            {rejected.length === 0
              ? "Log some rejection feedback in the 'Not Selected' tab first."
              : "Click 'Refresh Analysis' to generate insights from your rejections."}
          </p>
          {rejected.length > 0 && (
            <Button onClick={handleRefresh} className="mt-4">
              <Sparkles className="w-4 h-4" />
              Generate Analysis
            </Button>
          )}
        </div>
      )}

      {/* Main analysis grid */}
      {globalAnalysis && !isLoading_ && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="space-y-6"
        >
          {/* Last updated */}
          <div className="flex items-center gap-1.5 text-xs text-slate-500">
            <Clock className="w-3 h-3" />
            Last updated {formatRelativeTime(globalAnalysis.last_updated)}
          </div>

          {/* Top row: Radar + Recurring missing skills */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {globalAnalysis.skill_radar_data.length > 0 && (
              <RadarChartSection data={globalAnalysis.skill_radar_data} />
            )}
            <InsightCard
              icon={<AlertTriangle className="w-4 h-4" />}
              title="Recurring Missing Skills"
              items={globalAnalysis.recurring_missing_skills}
              variant="danger"
            />
          </div>

          {/* Bottom row */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
            <InsightCard
              icon={<MessageSquare className="w-4 h-4" />}
              title="Common Interview Topics"
              items={globalAnalysis.common_interview_topics}
              variant="warning"
            />
            <InsightCard
              icon={<TrendingUp className="w-4 h-4" />}
              title="Frequent Weaknesses"
              items={globalAnalysis.frequent_weaknesses}
              variant="info"
            />
            <InsightCard
              icon={<Lightbulb className="w-4 h-4" />}
              title="Career Recommendations"
              items={globalAnalysis.career_recommendations}
              variant="success"
            />
          </div>

          {/* Company-skill matrix */}
          <CompanySkillMatrix
            applications={applications.filter((a) => a.status === "not_selected")}
          />
        </motion.div>
      )}
    </div>
  );
}

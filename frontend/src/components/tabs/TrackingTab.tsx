import { useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  LayoutDashboard, Building2, Briefcase, Calendar, Target,
  ChevronRight, Trash2, RefreshCw, TrendingUp,
} from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Progress } from "@/components/ui/Progress";
import { Spinner } from "@/components/ui/Spinner";
import { Tooltip } from "@/components/ui/Tooltip";
import { useAppStore } from "@/hooks/useAppStore";
import { cn, STATUS_CONFIG, formatRelativeTime, getMatchColor } from "@/lib/utils";
import * as api from "@/lib/api";
import type { Application, ApplicationStatus } from "@/types";

const STATUS_ORDER: ApplicationStatus[] = ["submitted", "interview", "selected", "not_selected"];

const STATUS_NEXT: Record<ApplicationStatus, ApplicationStatus | null> = {
  submitted: "interview",
  interview: "selected",
  selected: null,
  not_selected: null,
};

function ApplicationCard({ app }: { app: Application }) {
  const { upsertApplication, removeApplication, addToast, isLoading, setLoading, setActiveTab } = useAppStore();
  const cfg = STATUS_CONFIG[app.status];

  const handleStatusChange = async (status: ApplicationStatus) => {
    setLoading(`status-${app.id}`, true);
    try {
      const updated = await api.updateApplicationStatus(app.id, status);
      upsertApplication(updated);
      addToast({ type: "success", message: `Status updated to ${STATUS_CONFIG[status].label}` });
    } catch (e: any) {
      addToast({ type: "error", message: e.message });
    } finally {
      setLoading(`status-${app.id}`, false);
    }
  };

  const handleDelete = async () => {
    setLoading(`del-${app.id}`, true);
    try {
      await api.deleteApplication(app.id);
      removeApplication(app.id);
      addToast({ type: "info", message: "Application removed." });
    } catch (e: any) {
      addToast({ type: "error", message: e.message });
    } finally {
      setLoading(`del-${app.id}`, false);
    }
  };

  const nextStatus = STATUS_NEXT[app.status];
  const isUpdating = isLoading[`status-${app.id}`] || isLoading[`del-${app.id}`];

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, scale: 0.95 }}
      className="glass-card p-4 shadow-lg"
    >
      {/* Header */}
      <div className="flex items-start justify-between gap-3 mb-3">
        <div className="flex items-center gap-3 min-w-0">
          <div className="w-9 h-9 rounded-xl bg-slate-800 flex items-center justify-center shrink-0 text-sm font-bold text-slate-300">
            {app.company?.charAt(0) || "?"}
          </div>
          <div className="min-w-0">
            <p className="font-semibold text-slate-100 truncate">{app.company || "Unknown Company"}</p>
            <p className="text-xs text-slate-400 truncate">{app.role || "Unknown Role"}</p>
          </div>
        </div>
        <Badge
          variant={
            app.status === "selected" ? "success"
            : app.status === "interview" ? "warning"
            : app.status === "not_selected" ? "danger"
            : "info"
          }
          dot
          pulse={app.status === "submitted"}
        >
          {cfg.label}
        </Badge>
      </div>

      {/* Match bar */}
      <div className="mb-3">
        <div className="flex justify-between text-xs mb-1">
          <span className="text-slate-500">Match score</span>
          <span className={cn("font-bold", getMatchColor(app.match_percentage))}>
            {app.match_percentage.toFixed(0)}%
          </span>
        </div>
        <Progress value={app.match_percentage} colorByValue size="sm" />
      </div>

      {/* Skills summary */}
      {app.matched_skills.length > 0 && (
        <div className="flex flex-wrap gap-1 mb-3">
          {app.matched_skills.slice(0, 4).map((s) => (
            <span key={s} className="text-[10px] bg-emerald-500/10 text-emerald-400 px-1.5 py-0.5 rounded-md">{s}</span>
          ))}
          {app.matched_skills.length > 4 && (
            <span className="text-[10px] text-slate-500">+{app.matched_skills.length - 4}</span>
          )}
        </div>
      )}

      {/* Footer */}
      <div className="flex items-center justify-between pt-2 border-t border-slate-800/60">
        <span className="text-xs text-slate-500 flex items-center gap-1">
          <Calendar className="w-3 h-3" />
          {formatRelativeTime(app.submitted_at)}
        </span>

        <div className="flex items-center gap-1.5">
          {/* Log rejection */}
          {app.status === "not_selected" && (
            <Tooltip content="Analyze rejection">
              <button
                onClick={() => setActiveTab("not-selected")}
                className="p-1.5 rounded-lg text-amber-400 hover:bg-amber-500/10 transition-colors text-xs"
              >
                <TrendingUp className="w-3.5 h-3.5" />
              </button>
            </Tooltip>
          )}

          {/* Mark not selected */}
          {(app.status === "submitted" || app.status === "interview") && (
            <Tooltip content="Mark as Not Selected">
              <button
                onClick={() => handleStatusChange("not_selected")}
                disabled={isUpdating}
                className="p-1.5 rounded-lg text-red-400 hover:bg-red-500/10 transition-colors"
              >
                ✕
              </button>
            </Tooltip>
          )}

          {/* Move forward */}
          {nextStatus && (
            <Button
              size="sm"
              variant="outline"
              loading={isUpdating}
              onClick={() => handleStatusChange(nextStatus)}
              className="text-xs"
            >
              {STATUS_CONFIG[nextStatus].label}
              <ChevronRight className="w-3 h-3" />
            </Button>
          )}

          {/* Delete */}
          <Tooltip content="Delete">
            <button
              onClick={handleDelete}
              disabled={isUpdating}
              className="p-1.5 rounded-lg text-slate-600 hover:text-red-400 hover:bg-red-500/10 transition-colors"
            >
              <Trash2 className="w-3.5 h-3.5" />
            </button>
          </Tooltip>
        </div>
      </div>
    </motion.div>
  );
}

function StatusColumn({ status, apps }: { status: ApplicationStatus; apps: Application[] }) {
  const cfg = STATUS_CONFIG[status];

  return (
    <div className="flex-1 min-w-[260px]">
      {/* Column header */}
      <div className={cn(
        "flex items-center gap-2.5 px-4 py-3 rounded-xl mb-3 border",
        cfg.bg, cfg.border
      )}>
        <span className={cn("w-2 h-2 rounded-full", cfg.dot, status === "submitted" && "animate-pulse")} />
        <span className={cn("text-sm font-bold", cfg.color)}>{cfg.label}</span>
        <span className="ml-auto text-xs font-bold bg-slate-800/60 px-2 py-0.5 rounded-full text-slate-300">
          {apps.length}
        </span>
      </div>

      <div className="space-y-3">
        <AnimatePresence>
          {apps.map((app) => (
            <ApplicationCard key={app.id} app={app} />
          ))}
        </AnimatePresence>
        {apps.length === 0 && (
          <div className="text-center py-8 text-slate-600 text-sm border-2 border-dashed border-slate-800 rounded-xl">
            No applications
          </div>
        )}
      </div>
    </div>
  );
}

export function TrackingTab() {
  const { applications, setApplications, addToast, isLoading, setLoading } = useAppStore();

  const fetchApps = async () => {
    setLoading("fetch-apps", true);
    try {
      const apps = await api.getApplications();
      setApplications(apps);
    } catch {
      // silently fail — local state is enough
    } finally {
      setLoading("fetch-apps", false);
    }
  };

  useEffect(() => { fetchApps(); }, []);

  const grouped = STATUS_ORDER.reduce<Record<ApplicationStatus, Application[]>>(
    (acc, s) => {
      acc[s] = applications.filter((a) => a.status === s);
      return acc;
    },
    { submitted: [], interview: [], selected: [], not_selected: [] }
  );

  // Summary stats
  const total = applications.length;
  const successRate = total > 0
    ? ((grouped.selected.length / total) * 100).toFixed(0)
    : "0";
  const avgMatch = total > 0
    ? (applications.reduce((s, a) => s + a.match_percentage, 0) / total).toFixed(0)
    : "0";

  return (
    <div className="p-6 space-y-6">
      {/* Title */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold gradient-text">Application Tracker</h1>
          <p className="text-slate-400 text-sm mt-1">Your personal career CRM — track every application.</p>
        </div>
        <Button variant="secondary" size="sm" onClick={fetchApps} loading={isLoading["fetch-apps"]}>
          <RefreshCw className="w-3.5 h-3.5" />
          Sync
        </Button>
      </div>

      {/* Summary cards */}
      {total > 0 && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {[
            { label: "Total Applied", value: total, icon: <Briefcase className="w-4 h-4" />, color: "text-blue-400" },
            { label: "In Interview", value: grouped.interview.length, icon: <Building2 className="w-4 h-4" />, color: "text-amber-400" },
            { label: "Success Rate", value: `${successRate}%`, icon: <TrendingUp className="w-4 h-4" />, color: "text-emerald-400" },
            { label: "Avg Match", value: `${avgMatch}%`, icon: <Target className="w-4 h-4" />, color: "text-purple-400" },
          ].map((stat) => (
            <motion.div
              key={stat.label}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="glass-card p-4 text-center"
            >
              <div className={cn("flex justify-center mb-1", stat.color)}>{stat.icon}</div>
              <p className={cn("text-2xl font-black", stat.color)}>{stat.value}</p>
              <p className="text-xs text-slate-500 mt-0.5">{stat.label}</p>
            </motion.div>
          ))}
        </div>
      )}

      {/* Kanban columns */}
      {total === 0 ? (
        <div className="text-center py-20">
          <div className="w-16 h-16 rounded-2xl bg-slate-800 flex items-center justify-center mx-auto mb-4">
            <LayoutDashboard className="w-8 h-8 text-slate-600" />
          </div>
          <h3 className="text-lg font-semibold text-slate-300">No applications yet</h3>
          <p className="text-slate-500 text-sm mt-1">
            Head to the <span className="text-indigo-400">Apply</span> tab to get started.
          </p>
        </div>
      ) : (
        <div className="flex gap-4 overflow-x-auto pb-4">
          {STATUS_ORDER.map((status) => (
            <StatusColumn key={status} status={status} apps={grouped[status]} />
          ))}
        </div>
      )}
    </div>
  );
}

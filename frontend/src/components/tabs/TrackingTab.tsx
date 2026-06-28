import { useEffect, useMemo, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  LayoutDashboard, Briefcase, Building2, Target, TrendingUp,
  RefreshCw, Eye, Trash2, ExternalLink, Plus, LayoutGrid, List,
  StickyNote, Archive, Bookmark,
} from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Tooltip } from "@/components/ui/Tooltip";
import { Modal } from "@/components/ui/Modal";
import { ConfirmDialog } from "@/components/ui/ConfirmDialog";
import { useAppStore } from "@/hooks/useAppStore";
import { cn, STATUS_CONFIG, SOURCE_LABELS, formatRelativeTime, getMatchColor } from "@/lib/utils";
import * as api from "@/lib/api";
import type { Application, ApplicationStatus } from "@/types";

/** Jobright-style pipeline stages */
const PIPELINE: ApplicationStatus[] = ["saved", "submitted", "interview", "selected"];
const TERMINAL: ApplicationStatus[] = ["not_selected", "archived"];

function isFollowUpDue(followUpAt?: string): boolean {
  if (!followUpAt) return false;
  const due = new Date(followUpAt.slice(0, 10));
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  return due <= today;
}

const STAGE_ACTIONS: { id: ApplicationStatus; label: string }[] = [
  { id: "saved", label: "Saved" },
  { id: "submitted", label: "Applied" },
  { id: "interview", label: "Interviewing" },
  { id: "selected", label: "Offer" },
  { id: "not_selected", label: "Rejected" },
  { id: "archived", label: "Archive" },
];

type DialogState =
  | { kind: "select-direct"; app: Application }
  | { kind: "not-selected"; app: Application }
  | { kind: "delete"; app: Application }
  | null;

function SourceBadge({ source }: { source?: string }) {
  if (!source) return null;
  const tone =
    source === "linkedin" ? "info" : source === "greenhouse" ? "success" : source === "hiringcafe" ? "purple" : "default";
  return (
    <Badge variant={tone} className="text-[10px]">
      {SOURCE_LABELS[source] || source}
    </Badge>
  );
}

function ApplicationCard({
  app,
  onStatus,
  onViewJd,
  onDelete,
  onNotes,
  compact,
}: {
  app: Application;
  onStatus: (app: Application, status: ApplicationStatus) => void;
  onViewJd: (app: Application) => void;
  onDelete: (app: Application) => void;
  onNotes: (app: Application) => void;
  compact?: boolean;
}) {
  const cfg = STATUS_CONFIG[app.status];
  const busy = false;

  return (
    <motion.div layout initial={{ opacity: 0, scale: 0.98 }} animate={{ opacity: 1, scale: 1 }} className="glass glass-edge p-3.5">
      <div className="mb-2 flex items-start justify-between gap-2">
        <div className="min-w-0">
          <p className="truncate font-semibold text-ink-900">{app.company}</p>
          <p className="truncate text-xs text-ink-500">{app.role}</p>
        </div>
        <span className={cn("shrink-0 text-xs font-bold tabular-nums", getMatchColor(app.match_percentage))}>
          {app.match_percentage > 0 ? `${app.match_percentage.toFixed(0)}%` : "—"}
        </span>
      </div>

      <div className="mb-2.5 flex flex-wrap items-center gap-1.5">
        <SourceBadge source={app.source} />
        <span className="text-[10px] text-ink-400">{formatRelativeTime(app.updated_at)}</span>
        {app.follow_up_at && (
          <Badge variant={isFollowUpDue(app.follow_up_at) ? "warning" : "default"} className="text-[9px]">
            Follow-up {app.follow_up_at.slice(0, 10)}
          </Badge>
        )}
      </div>

      {!compact && app.notes && (
        <p className="mb-2 line-clamp-2 text-[11px] text-ink-500">{app.notes}</p>
      )}

      <div className="flex flex-wrap gap-1">
        {app.apply_url && (
          <a
            href={app.apply_url}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1 rounded-lg border border-slate-200 px-2 py-1 text-[10px] font-medium text-brand-700 hover:bg-brand-50"
          >
            <ExternalLink className="h-3 w-3" /> Apply
          </a>
        )}
        <button onClick={() => onViewJd(app)} className="rounded-lg border border-slate-200 px-2 py-1 text-[10px] text-ink-500 hover:bg-slate-50 cursor-pointer">
          <Eye className="inline h-3 w-3" /> JD
        </button>
        <button onClick={() => onNotes(app)} className="rounded-lg border border-slate-200 px-2 py-1 text-[10px] text-ink-500 hover:bg-slate-50 cursor-pointer">
          <StickyNote className="inline h-3 w-3" />
        </button>
        <button onClick={() => onDelete(app)} disabled={busy} className="rounded-lg border border-slate-200 px-2 py-1 text-[10px] text-rose-500 hover:bg-rose-50 cursor-pointer">
          <Trash2 className="inline h-3 w-3" />
        </button>
      </div>

      <div className="mt-2.5 flex flex-wrap gap-1 border-t border-slate-100 pt-2">
        {STAGE_ACTIONS.filter((s) => s.id !== app.status).slice(0, 4).map((st) => (
          <button
            key={st.id}
            onClick={() => onStatus(app, st.id)}
            className="rounded-md bg-slate-100 px-1.5 py-0.5 text-[10px] font-medium text-ink-600 hover:bg-brand-100 hover:text-brand-700 cursor-pointer"
          >
            → {st.label}
          </button>
        ))}
      </div>
    </motion.div>
  );
}

export function TrackingTab() {
  const { applications, setApplications, upsertApplication, removeApplication, addToast, isLoading, setLoading, setActiveTab } = useAppStore();

  const [view, setView] = useState<"board" | "table">("board");
  const [showArchived, setShowArchived] = useState(false);
  const [jdModal, setJdModal] = useState<Application | null>(null);
  const [notesModal, setNotesModal] = useState<Application | null>(null);
  const [detailModal, setDetailModal] = useState<Application | null>(null);
  const [notesDraft, setNotesDraft] = useState("");
  const [followUpDraft, setFollowUpDraft] = useState("");
  const [searchQuery, setSearchQuery] = useState("");
  const [filterSource, setFilterSource] = useState<string>("all");
  const [addModal, setAddModal] = useState(false);
  const [dialog, setDialog] = useState<DialogState>(null);
  const [extForm, setExtForm] = useState({ company: "", role: "", apply_url: "", job_description: "" });

  const fetchApps = async () => {
    setLoading("fetch-apps", true);
    try {
      setApplications(await api.getApplications(showArchived));
    } catch { /* local ok */ } finally {
      setLoading("fetch-apps", false);
    }
  };
  useEffect(() => { fetchApps(); }, [showArchived]);

  const setStatus = async (app: Application, status: ApplicationStatus) => {
    setLoading(`status-${app.id}`, true);
    try {
      const updated = await api.updateApplicationStatus(app.id, status);
      upsertApplication(updated);
      addToast({ type: "success", message: `${app.company} → ${STATUS_CONFIG[status].label}` });
      if (status === "not_selected") {
        addToast({ type: "info", message: "Moved to Rejected — analyze in Not Selected tab." });
      }
    } catch (e: unknown) {
      addToast({ type: "error", message: e instanceof Error ? e.message : "Update failed" });
    } finally {
      setLoading(`status-${app.id}`, false);
    }
  };

  const handleStageClick = (app: Application, stage: ApplicationStatus) => {
    if (stage === app.status) return;
    if (stage === "selected" && app.status !== "interview" && app.status !== "submitted") {
      setDialog({ kind: "select-direct", app });
    } else if (stage === "not_selected") {
      setDialog({ kind: "not-selected", app });
    } else {
      setStatus(app, stage);
    }
  };

  const handleDelete = async (app: Application) => {
    setLoading(`del-${app.id}`, true);
    try {
      await api.deleteApplication(app.id);
      removeApplication(app.id);
      addToast({ type: "info", message: "Application removed." });
    } catch (e: unknown) {
      addToast({ type: "error", message: e instanceof Error ? e.message : "Delete failed" });
    } finally {
      setLoading(`del-${app.id}`, false);
      setDialog(null);
    }
  };

  const saveNotes = async () => {
    if (!notesModal) return;
    setLoading("save-notes", true);
    try {
      const updated = await api.patchApplication(notesModal.id, {
        notes: notesDraft,
        follow_up_at: followUpDraft || undefined,
      });
      upsertApplication(updated);
      addToast({ type: "success", message: "Application updated." });
      setNotesModal(null);
    } catch (e: unknown) {
      addToast({ type: "error", message: e instanceof Error ? e.message : "Save failed" });
    } finally {
      setLoading("save-notes", false);
    }
  };

  const handleAddExternal = async () => {
    if (!extForm.company.trim() || !extForm.role.trim()) return;
    setLoading("add-external", true);
    try {
      const app = await api.trackJob({
        company: extForm.company.trim(),
        role: extForm.role.trim(),
        apply_url: extForm.apply_url.trim(),
        job_description: extForm.job_description.trim(),
        source: "manual",
        status: "submitted",
      });
      upsertApplication(app);
      addToast({ type: "success", message: "External job tracked." });
      setAddModal(false);
      setExtForm({ company: "", role: "", apply_url: "", job_description: "" });
    } catch (e: unknown) {
      addToast({ type: "error", message: e instanceof Error ? e.message : "Failed to track" });
    } finally {
      setLoading("add-external", false);
    }
  };

  const visible = useMemo(() => {
    return applications.filter((a) => {
      if (!showArchived && a.status === "archived") return false;
      if (filterSource !== "all" && a.source !== filterSource) return false;
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        const blob = `${a.company} ${a.role} ${a.source} ${a.notes || ""}`.toLowerCase();
        if (!blob.includes(q)) return false;
      }
      return true;
    });
  }, [applications, showArchived, filterSource, searchQuery]);

  const byStage = useMemo(() => {
    const map: Record<ApplicationStatus, Application[]> = {
      saved: [], submitted: [], interview: [], selected: [], not_selected: [], archived: [],
    };
    for (const app of visible) map[app.status].push(app);
    return map;
  }, [visible]);

  const total = applications.length;
  const activeCount = visible.filter((a) => PIPELINE.includes(a.status)).length;
  const interviewing = applications.filter((a) => a.status === "interview").length;
  const offers = applications.filter((a) => a.status === "selected").length;
  const successRate = total ? ((offers / total) * 100).toFixed(0) : "0";
  const followUpsDue = visible.filter((a) => isFollowUpDue(a.follow_up_at)).length;

  const stats = [
    { label: "Active pipeline", value: activeCount, icon: Briefcase, color: "text-sky-600", bg: "bg-sky-50" },
    { label: "Interviewing", value: interviewing, icon: Building2, color: "text-amber-600", bg: "bg-amber-50" },
    { label: "Follow-ups due", value: followUpsDue, icon: StickyNote, color: "text-rose-600", bg: "bg-rose-50" },
    { label: "Success rate", value: `${successRate}%`, icon: Target, color: "text-violet-600", bg: "bg-violet-50" },
  ];

  return (
    <div className="space-y-6 p-4 py-6 sm:p-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div className="space-y-2">
          <h1 className="font-display text-3xl font-bold tracking-tightest text-ink-900 sm:text-4xl">
            Application <span className="gradient-text-brand">Tracker</span>
          </h1>
          <p className="text-sm text-ink-500">
            Jobright-style full-cycle tracking — Saved → Applied → Interviewing → Offer, plus external job upload.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button variant="secondary" size="sm" onClick={() => setView(view === "board" ? "table" : "board")}>
            {view === "board" ? <List className="h-3.5 w-3.5" /> : <LayoutGrid className="h-3.5 w-3.5" />}
            {view === "board" ? "Table" : "Board"}
          </Button>
          <Button variant="secondary" size="sm" onClick={() => setShowArchived((v) => !v)}>
            <Archive className="h-3.5 w-3.5" /> {showArchived ? "Hide archived" : "Show archived"}
          </Button>
          <Button size="sm" onClick={() => setAddModal(true)}>
            <Plus className="h-3.5 w-3.5" /> Add external job
          </Button>
          <Button variant="secondary" size="sm" onClick={fetchApps} loading={isLoading["fetch-apps"]}>
            <RefreshCw className="h-3.5 w-3.5" /> Sync
          </Button>
        </div>
      </div>

      {total > 0 && (
        <>
          <div className="glass glass-edge flex flex-wrap items-center gap-3 p-4">
            <input
              className="input-field min-w-[200px] flex-1 py-2 text-sm"
              placeholder="Search company, role, notes…"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
            <select
              className="input-field w-auto py-2 text-sm"
              value={filterSource}
              onChange={(e) => setFilterSource(e.target.value)}
            >
              <option value="all">All sources</option>
              <option value="linkedin">LinkedIn</option>
              <option value="greenhouse">Greenhouse</option>
              <option value="hiringcafe">Hiring Cafe</option>
              <option value="manual">External</option>
            </select>
          </div>

          {/* Pipeline progress */}
          <div className="glass glass-edge p-4">
            <p className="section-label mb-3">Pipeline overview</p>
            <div className="flex h-2 overflow-hidden rounded-full bg-slate-100">
              {PIPELINE.map((stage) => {
                const count = byStage[stage].length;
                if (!count) return null;
                const pct = (count / Math.max(visible.length, 1)) * 100;
                const colors: Record<string, string> = {
                  saved: "bg-violet-500", submitted: "bg-sky-500", interview: "bg-amber-500", selected: "bg-emerald-500",
                };
                return <div key={stage} style={{ width: `${pct}%` }} className={cn("h-full", colors[stage])} title={`${STATUS_CONFIG[stage].label}: ${count}`} />;
              })}
            </div>
            <div className="mt-2 flex flex-wrap gap-3 text-[10px] text-ink-500">
              {PIPELINE.map((s) => (
                <span key={s}>{STATUS_CONFIG[s].label}: <strong className="text-ink-700">{byStage[s].length}</strong></span>
              ))}
            </div>
          </div>
        </>
      )}

      {total > 0 && (
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          {stats.map((stat, i) => (
            <motion.div key={stat.label} initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.05 }} className="glass glass-edge p-4">
              <div className={cn("mb-2 flex h-8 w-8 items-center justify-center rounded-lg", stat.bg, stat.color)}>
                <stat.icon className="h-4 w-4" />
              </div>
              <p className={cn("font-display text-2xl font-bold tabular-nums", stat.color)}>{stat.value}</p>
              <p className="mt-0.5 text-xs text-ink-400">{stat.label}</p>
            </motion.div>
          ))}
        </div>
      )}

      {visible.length === 0 ? (
        <div className="glass glass-edge flex flex-col items-center py-20 text-center">
          <LayoutDashboard className="mb-4 h-10 w-10 text-ink-300" />
          <h3 className="font-display text-lg font-semibold text-ink-800">No applications tracked yet</h3>
          <p className="mt-1 max-w-sm text-sm text-ink-500">
            Discover jobs on LinkedIn, Greenhouse & Hiring Cafe, or add an external posting manually.
          </p>
          <div className="mt-4 flex gap-2">
            <Button size="sm" onClick={() => setActiveTab("discover")}>Browse jobs</Button>
            <Button size="sm" variant="secondary" onClick={() => setAddModal(true)}>Add external job</Button>
          </div>
        </div>
      ) : view === "board" ? (
        <div className="space-y-6">
          <div className="grid gap-4 lg:grid-cols-4">
            {PIPELINE.map((stage) => {
              const cfg = STATUS_CONFIG[stage];
              const items = byStage[stage];
              return (
                <div key={stage} className="min-w-0">
                  <div className="mb-3 flex items-center justify-between">
                    <h3 className={cn("text-sm font-semibold", cfg.color)}>{cfg.column || cfg.label}</h3>
                    <Badge variant="default" className="text-[10px] tabular-nums">{items.length}</Badge>
                  </div>
                  <div className="space-y-3">
                    <AnimatePresence>
                      {items.map((app) => (
                        <ApplicationCard
                          key={app.id}
                          app={app}
                          onStatus={handleStageClick}
                          onViewJd={setDetailModal}
                          onDelete={(a) => setDialog({ kind: "delete", app: a })}
                          onNotes={(a) => {
                            setNotesModal(a);
                            setNotesDraft(a.notes || "");
                            setFollowUpDraft(a.follow_up_at?.slice(0, 10) || "");
                          }}
                          compact
                        />
                      ))}
                    </AnimatePresence>
                    {items.length === 0 && (
                      <div className="rounded-xl border border-dashed border-slate-200 py-8 text-center text-xs text-ink-400">
                        No jobs here
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>

          {(byStage.not_selected.length > 0 || byStage.archived.length > 0) && (
            <div className="grid gap-4 md:grid-cols-2">
              {TERMINAL.filter((s) => byStage[s].length > 0 || s === "not_selected").map((stage) => (
                <div key={stage}>
                  <h3 className={cn("mb-3 text-sm font-semibold", STATUS_CONFIG[stage].color)}>
                    {STATUS_CONFIG[stage].label} ({byStage[stage].length})
                  </h3>
                  <div className="space-y-2">
                    {byStage[stage].map((app) => (
                      <ApplicationCard
                        key={app.id}
                        app={app}
                        onStatus={handleStageClick}
                        onViewJd={setDetailModal}
                        onDelete={(a) => setDialog({ kind: "delete", app: a })}
                        onNotes={(a) => {
                          setNotesModal(a);
                          setNotesDraft(a.notes || "");
                          setFollowUpDraft(a.follow_up_at?.slice(0, 10) || "");
                        }}
                        compact
                      />
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      ) : (
        <div className="glass glass-edge overflow-hidden p-0">
          <div className="overflow-x-auto">
            <table className="w-full min-w-[980px] border-collapse text-sm">
              <thead>
                <tr className="border-b border-slate-200/80 text-left">
                  {["Company", "Role", "Source", "Match", "Stage", "Apply", "Updated", ""].map((h) => (
                    <th key={h} className="px-4 py-3 text-[11px] font-semibold uppercase tracking-wider text-ink-400">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {visible.map((app) => {
                  const cfg = STATUS_CONFIG[app.status];
                  const busy = isLoading[`status-${app.id}`];
                  return (
                    <tr key={app.id} className="border-b border-slate-100 hover:bg-white/60">
                      <td className="px-4 py-3 font-semibold text-ink-800">{app.company}</td>
                      <td className="px-4 py-3 text-ink-600">{app.role}</td>
                      <td className="px-4 py-3"><SourceBadge source={app.source} /></td>
                      <td className={cn("px-4 py-3 font-bold tabular-nums", getMatchColor(app.match_percentage))}>
                        {app.match_percentage > 0 ? `${app.match_percentage.toFixed(0)}%` : "—"}
                      </td>
                      <td className="px-4 py-3">
                        <span className={cn("inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-xs font-semibold", cfg.bg, cfg.border, cfg.color)}>
                          <span className={cn("h-1.5 w-1.5 rounded-full", cfg.dot)} />
                          {cfg.label}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        {app.apply_url ? (
                          <a href={app.apply_url} target="_blank" rel="noopener noreferrer" className="text-brand-600 hover:underline text-xs">Open</a>
                        ) : "—"}
                      </td>
                      <td className="px-4 py-3 text-xs text-ink-400">{formatRelativeTime(app.updated_at)}</td>
                      <td className="px-4 py-3">
                        <div className="flex gap-1">
                          {STAGE_ACTIONS.filter((s) => s.id !== app.status).slice(0, 3).map((st) => (
                            <button key={st.id} disabled={busy} onClick={() => handleStageClick(app, st.id)} className="rounded border border-slate-200 px-1.5 py-0.5 text-[10px] cursor-pointer hover:bg-slate-50">
                              {st.label}
                            </button>
                          ))}
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Add external job — Jobright upload feature */}
      <Modal open={addModal} onClose={() => setAddModal(false)} title="Track external job" description="Paste a job from LinkedIn, Greenhouse, Hiring Cafe, or any careers page.">
        <div className="space-y-3">
          <input className="input-field" placeholder="Company" value={extForm.company} onChange={(e) => setExtForm({ ...extForm, company: e.target.value })} />
          <input className="input-field" placeholder="Role / title" value={extForm.role} onChange={(e) => setExtForm({ ...extForm, role: e.target.value })} />
          <input className="input-field" placeholder="Application URL" value={extForm.apply_url} onChange={(e) => setExtForm({ ...extForm, apply_url: e.target.value })} />
          <textarea className="input-field resize-none" rows={4} placeholder="Job description (optional)" value={extForm.job_description} onChange={(e) => setExtForm({ ...extForm, job_description: e.target.value })} />
          <Button className="w-full" onClick={handleAddExternal} loading={isLoading["add-external"]} disabled={!extForm.company.trim() || !extForm.role.trim()}>
            <Bookmark className="h-4 w-4" /> Track application
          </Button>
        </div>
      </Modal>

      <Modal open={!!notesModal} onClose={() => setNotesModal(null)} title="Application notes" description="Follow-ups, recruiter contacts, interview prep.">
        <textarea className="input-field min-h-[100px] resize-none" value={notesDraft} onChange={(e) => setNotesDraft(e.target.value)} placeholder="Add notes…" />
        <label className="section-label mt-3 block">Follow-up date</label>
        <input type="date" className="input-field mt-1" value={followUpDraft} onChange={(e) => setFollowUpDraft(e.target.value)} />
        <div className="mt-3 flex justify-end gap-2">
          <Button variant="secondary" onClick={() => setNotesModal(null)}>Cancel</Button>
          <Button onClick={saveNotes} loading={isLoading["save-notes"]}>Save</Button>
        </div>
      </Modal>

      <Modal open={!!detailModal} onClose={() => setDetailModal(null)} title={detailModal ? `${detailModal.company} — ${detailModal.role}` : ""} size="lg">
        {detailModal && (
          <div className="space-y-4">
            <div className="flex flex-wrap gap-2">
              <SourceBadge source={detailModal.source} />
              <Badge variant="default">{STATUS_CONFIG[detailModal.status].label}</Badge>
            </div>
            {detailModal.apply_url && (
              <a href={detailModal.apply_url} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-1 text-sm text-brand-600 hover:underline">
                <ExternalLink className="h-4 w-4" /> Open application page
              </a>
            )}
            <div>
              <p className="section-label mb-2">Status timeline</p>
              <div className="space-y-2 border-l-2 border-brand-200 pl-4">
                {(detailModal.status_history?.length ? detailModal.status_history : [{ status: detailModal.status, changed_at: detailModal.submitted_at, note: "Tracked" }]).map((entry, i) => (
                  <div key={i} className="relative">
                    <span className="absolute -left-[21px] top-1 h-2.5 w-2.5 rounded-full bg-brand-500 ring-2 ring-white" />
                    <p className="text-sm font-medium text-ink-800">{STATUS_CONFIG[entry.status].label}</p>
                    <p className="text-[11px] text-ink-400">{formatRelativeTime(entry.changed_at)}{entry.note ? ` · ${entry.note}` : ""}</p>
                  </div>
                ))}
              </div>
            </div>
            <div>
              <p className="section-label mb-1">Job description</p>
              <div className="max-h-40 overflow-y-auto rounded-xl border border-slate-200 bg-white/60 p-3 text-sm text-ink-600 whitespace-pre-wrap">
                {detailModal.job_description || "No description saved."}
              </div>
            </div>
          </div>
        )}
      </Modal>

      <Modal open={!!jdModal} onClose={() => setJdModal(null)} title={jdModal ? `${jdModal.company} — ${jdModal.role}` : ""} size="lg">
        <div className="max-h-[55vh] overflow-y-auto whitespace-pre-wrap rounded-xl border border-slate-200 bg-white/60 p-4 text-sm text-ink-600">
          {jdModal?.job_description || "No description saved."}
        </div>
      </Modal>

      <ConfirmDialog open={dialog?.kind === "select-direct"} title="Mark as Offer Received?" message="This application wasn't in Interviewing yet. Mark as Offer Received anyway?" confirmLabel="Yes, mark offer" loading={dialog?.kind === "select-direct" ? isLoading[`status-${dialog.app.id}`] : false} onConfirm={() => { if (dialog?.kind === "select-direct") { setStatus(dialog.app, "selected"); setDialog(null); } }} onCancel={() => setDialog(null)} />
      <ConfirmDialog open={dialog?.kind === "not-selected"} tone="danger" title="Mark as Rejected?" message="Moves to Rejected for AI rejection analysis." confirmLabel="Yes, reject" loading={dialog?.kind === "not-selected" ? isLoading[`status-${dialog.app.id}`] : false} onConfirm={() => { if (dialog?.kind === "not-selected") { setStatus(dialog.app, "not_selected"); setDialog(null); } }} onCancel={() => setDialog(null)} />
      <ConfirmDialog open={dialog?.kind === "delete"} tone="danger" title="Delete application?" message="Permanently removes this entry and any rejection notes." confirmLabel="Delete" loading={dialog?.kind === "delete" ? isLoading[`del-${dialog.app.id}`] : false} onConfirm={() => { if (dialog?.kind === "delete") handleDelete(dialog.app); }} onCancel={() => setDialog(null)} />
    </div>
  );
}

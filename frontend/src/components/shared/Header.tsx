import { useState } from "react";
import { Brain, Sparkles, Trash2 } from "lucide-react";
import { useAppStore } from "@/hooks/useAppStore";
import { useAuthStore } from "@/hooks/useAuthStore";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { ConfirmDialog } from "@/components/ui/ConfirmDialog";
import * as api from "@/lib/api";
import { LogOut } from "lucide-react";

export function Header() {
  const profile = useAppStore((s) => s.profile);
  const applications = useAppStore((s) => s.applications);
  const resetAll = useAppStore((s) => s.resetAll);
  const addToast = useAppStore((s) => s.addToast);
  const setActiveTab = useAppStore((s) => s.setActiveTab);
  const isLoading = useAppStore((s) => s.isLoading);
  const setLoading = useAppStore((s) => s.setLoading);
  const authUser = useAuthStore((s) => s.user);
  const logout = useAuthStore((s) => s.logout);
  const liveJobsFetchedAt = useAuthStore((s) => s.liveJobsFetchedAt);

  const [confirmOpen, setConfirmOpen] = useState(false);
  const selectedCount = applications.filter((a) => a.status === "selected").length;

  const handleClearAll = async () => {
    setLoading("clear-all", true);
    try {
      await api.clearAllData();
      resetAll();
      setActiveTab("apply");
      addToast({ type: "success", message: "All data cleared. Fresh start!" });
    } catch (e: any) {
      addToast({ type: "error", message: e.message });
    } finally {
      setLoading("clear-all", false);
      setConfirmOpen(false);
    }
  };

  return (
    <header className="sticky top-0 z-40 border-b border-slate-200/70 bg-white/60 backdrop-blur-xl">
      <div className="mx-auto flex h-[72px] max-w-[1440px] items-center justify-between px-4 sm:px-8">
        {/* Brand */}
        <div className="flex items-center gap-3.5">
          <div className="relative">
            <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-gradient-to-br from-brand-500 to-teal-600 shadow-glow">
              <Brain className="h-5 w-5 text-white" />
            </div>
          </div>
          <div className="leading-none">
            <div className="flex items-center gap-2">
              <span className="font-display text-[17px] font-semibold tracking-tight text-ink-900">
                AI Career Copilot
              </span>
              <Badge variant="success" className="hidden sm:inline-flex text-[10px] py-0">
                <Sparkles className="h-2.5 w-2.5" />
                GPT-4o
              </Badge>
            </div>
            <p className="mt-1 text-xs text-ink-500">
              Intelligence that learns from every rejection
            </p>
          </div>
        </div>

        {/* Right cluster */}
        <div className="flex items-center gap-3 sm:gap-4">
          {applications.length > 0 && (
            <div className="hidden items-center gap-4 rounded-xl border border-slate-200/80 bg-white/60 px-4 py-2 md:flex">
              <Stat value={applications.length} label="tracked" tone="text-ink-800" />
              <span className="h-7 w-px bg-slate-200" />
              <Stat value={selectedCount} label="selected" tone="text-emerald-600" />
            </div>
          )}

          {authUser && (
            <div className="hidden items-center gap-2 rounded-full border border-slate-200/80 bg-white/60 py-1 pl-1 pr-3 sm:flex">
              {authUser.picture ? (
                <img
                  src={authUser.picture}
                  alt=""
                  className="h-7 w-7 rounded-full object-cover ring-2 ring-white"
                />
              ) : (
                <div className="flex h-7 w-7 items-center justify-center rounded-full bg-gradient-to-br from-brand-400 to-teal-500 text-xs font-bold text-white">
                  {authUser.name?.charAt(0).toUpperCase() || "U"}
                </div>
              )}
              <div className="min-w-0">
                <p className="max-w-[120px] truncate text-sm font-medium text-ink-700">{authUser.name}</p>
                {liveJobsFetchedAt && (
                  <p className="text-[10px] text-emerald-600">Live jobs synced</p>
                )}
              </div>
            </div>
          )}

          <Button variant="secondary" size="sm" onClick={() => { logout(); resetAll(); addToast({ type: "info", message: "Signed out." }); }}>
            <LogOut className="h-3.5 w-3.5" />
            <span className="hidden sm:inline">Sign out</span>
          </Button>

          <Button
            variant="secondary"
            size="sm"
            onClick={() => setConfirmOpen(true)}
            className="!text-rose-600 hover:!border-rose-200 hover:!bg-rose-50"
          >
            <Trash2 className="h-3.5 w-3.5" />
            <span className="hidden sm:inline">Clear All Data</span>
          </Button>
        </div>
      </div>

      <ConfirmDialog
        open={confirmOpen}
        tone="danger"
        title="Clear all data?"
        message={
          <>
            This permanently wipes your candidate profile, all applications, rejection notes, and
            insights from <span className="font-mono text-ink-700">data.json</span>. All four tabs
            will reset to their empty state. This cannot be undone.
          </>
        }
        confirmLabel="Yes, clear everything"
        cancelLabel="Cancel"
        loading={isLoading["clear-all"]}
        onConfirm={handleClearAll}
        onCancel={() => setConfirmOpen(false)}
      />
    </header>
  );
}

function Stat({ value, label, tone }: { value: number; label: string; tone: string }) {
  return (
    <span className="flex items-baseline gap-1.5 text-xs text-ink-500">
      <span className={`text-sm font-bold tabular-nums ${tone}`}>{value}</span>
      {label}
    </span>
  );
}

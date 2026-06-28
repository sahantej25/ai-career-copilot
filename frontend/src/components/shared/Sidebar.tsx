import { motion } from "framer-motion";
import {
  Compass, Send, LayoutDashboard, XCircle, BarChart3, Sparkles,
} from "lucide-react";
import { useAppStore } from "@/hooks/useAppStore";
import { cn } from "@/lib/utils";
import type { TabId } from "@/types";

const TABS: { id: TabId; label: string; icon: React.ReactNode; description: string }[] = [
  {
    id: "discover",
    label: "Discover",
    icon: <Compass className="h-[18px] w-[18px]" />,
    description: "Matched job feed",
  },
  {
    id: "apply",
    label: "Apply",
    icon: <Send className="h-[18px] w-[18px]" />,
    description: "Prepare & submit",
  },
  {
    id: "tracking",
    label: "Tracking",
    icon: <LayoutDashboard className="h-[18px] w-[18px]" />,
    description: "Application pipeline",
  },
  {
    id: "not-selected",
    label: "Not Selected",
    icon: <XCircle className="h-[18px] w-[18px]" />,
    description: "Learn from rejections",
  },
  {
    id: "global-analysis",
    label: "Global Analysis",
    icon: <BarChart3 className="h-[18px] w-[18px]" />,
    description: "Patterns & insights",
  },
];

export function Sidebar() {
  const { activeTab, setActiveTab, applications, profile, setProfileModalOpen } = useAppStore();

  const counts: Partial<Record<TabId, number>> = {
    tracking: applications.filter((a) => a.status !== "archived" && a.status !== "not_selected").length,
    "not-selected": applications.filter((a) => a.status === "not_selected").length,
  };

  return (
    <aside className="hidden w-64 shrink-0 flex-col gap-1.5 py-6 pr-3 lg:flex">
      <p className="section-label px-4 pb-2">Workspace</p>
      {TABS.map((tab) => {
        const isActive = activeTab === tab.id;
        const count = counts[tab.id];
        return (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={cn(
              "group relative flex items-center gap-3 rounded-xl px-3.5 py-3 text-left transition-all duration-200 ease-out-expo cursor-pointer",
              isActive ? "text-ink-900" : "text-ink-500 hover:text-ink-800"
            )}
          >
            {isActive && (
              <motion.div
                layoutId="sidebar-active"
                className="absolute inset-0 rounded-xl border border-slate-200/80 bg-white/80 shadow-soft"
                transition={{ type: "spring", stiffness: 380, damping: 32 }}
              >
                <span className="absolute left-0 top-1/2 h-6 -translate-y-1/2 w-[3px] rounded-r-full bg-gradient-to-b from-brand-500 to-teal-500" />
              </motion.div>
            )}
            <span
              className={cn(
                "relative z-10 flex h-9 w-9 items-center justify-center rounded-lg transition-all duration-200",
                isActive
                  ? "bg-gradient-to-br from-brand-100 to-teal-100 text-brand-700"
                  : "bg-slate-100 text-ink-400 group-hover:text-brand-600"
              )}
            >
              {tab.icon}
            </span>
            <div className="relative z-10 min-w-0 flex-1">
              <div className="flex items-center justify-between gap-2">
                <span className="truncate text-sm font-semibold">{tab.label}</span>
                {count !== undefined && count > 0 && (
                  <span
                    className={cn(
                      "rounded-md px-1.5 py-0.5 text-[10px] font-bold tabular-nums",
                      isActive ? "bg-brand-100 text-brand-700" : "bg-slate-100 text-ink-500"
                    )}
                  >
                    {count}
                  </span>
                )}
              </div>
              <p className="truncate text-xs text-ink-400">{tab.description}</p>
            </div>
          </button>
        );
      })}

      {/* Footer hint card — opens profile editor */}
      <div className="mt-auto px-1">
        <button
          type="button"
          onClick={() => setProfileModalOpen(true)}
          className="glass glass-edge glass-hover w-full rounded-2xl p-4 text-left transition-all cursor-pointer"
        >
          <div className="mb-2 flex items-center gap-2">
            <Sparkles className="h-3.5 w-3.5 text-brand-600" />
            <span className="text-xs font-semibold text-ink-800">Living Profile</span>
            {profile && (
              <span className="ml-auto rounded-md bg-emerald-100 px-1.5 py-0.5 text-[10px] font-bold text-emerald-700">
                Active
              </span>
            )}
          </div>
          <p className="text-xs leading-relaxed text-ink-500">
            {profile
              ? `${profile.name || "Candidate"} · ${profile.skills.length} skills — click to edit`
              : "Add your candidate details to unlock matching, resume tailoring, and insights."}
          </p>
        </button>
      </div>
    </aside>
  );
}

/** Mobile bottom tab bar */
export function MobileTabBar() {
  const { activeTab, setActiveTab } = useAppStore();

  const mobileTabs = [
    { id: "discover" as TabId, label: "Discover", icon: <Compass className="h-5 w-5" /> },
    { id: "apply" as TabId, label: "Apply", icon: <Send className="h-5 w-5" /> },
    { id: "tracking" as TabId, label: "Track", icon: <LayoutDashboard className="h-5 w-5" /> },
    { id: "not-selected" as TabId, label: "Rejected", icon: <XCircle className="h-5 w-5" /> },
    { id: "global-analysis" as TabId, label: "Insights", icon: <BarChart3 className="h-5 w-5" /> },
  ];

  return (
    <nav className="fixed inset-x-0 bottom-0 z-40 border-t border-slate-200/80 bg-white/80 backdrop-blur-2xl lg:hidden">
      <div className="mx-auto flex max-w-md">
        {mobileTabs.map((tab) => {
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={cn(
                "relative flex flex-1 flex-col items-center gap-1 py-3 text-[11px] font-medium transition-colors cursor-pointer",
                isActive ? "text-brand-600" : "text-ink-400"
              )}
            >
              {isActive && (
                <motion.span
                  layoutId="mobile-active"
                  className="absolute top-0 h-0.5 w-8 rounded-full bg-gradient-to-r from-brand-500 to-teal-500"
                  transition={{ type: "spring", stiffness: 380, damping: 30 }}
                />
              )}
              {tab.icon}
              {tab.label}
            </button>
          );
        })}
      </div>
    </nav>
  );
}

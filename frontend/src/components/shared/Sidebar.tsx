import { motion } from "framer-motion";
import {
  Send, LayoutDashboard, XCircle, BarChart3, ChevronRight,
} from "lucide-react";
import { useAppStore } from "@/hooks/useAppStore";
import { cn } from "@/lib/utils";
import type { TabId } from "@/types";

const TABS: { id: TabId; label: string; icon: React.ReactNode; description: string }[] = [
  {
    id: "apply",
    label: "Apply",
    icon: <Send className="w-5 h-5" />,
    description: "Prepare & submit",
  },
  {
    id: "tracking",
    label: "Tracking",
    icon: <LayoutDashboard className="w-5 h-5" />,
    description: "Application pipeline",
  },
  {
    id: "not-selected",
    label: "Not Selected",
    icon: <XCircle className="w-5 h-5" />,
    description: "Learn from rejections",
  },
  {
    id: "global-analysis",
    label: "Global Analysis",
    icon: <BarChart3 className="w-5 h-5" />,
    description: "Patterns & insights",
  },
];

export function Sidebar() {
  const { activeTab, setActiveTab, applications } = useAppStore();

  const counts: Partial<Record<TabId, number>> = {
    tracking: applications.length,
    "not-selected": applications.filter((a) => a.status === "not_selected").length,
  };

  return (
    <aside className="w-64 shrink-0 hidden lg:flex flex-col gap-1 pt-6 px-3">
      {TABS.map((tab) => {
        const isActive = activeTab === tab.id;
        const count = counts[tab.id];
        return (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={cn(
              "relative flex items-center gap-3 px-4 py-3 rounded-xl text-left transition-all duration-200 group",
              isActive
                ? "bg-gradient-to-r from-indigo-600/20 to-purple-600/20 border border-indigo-500/30 text-white"
                : "hover:bg-slate-800/50 text-slate-400 hover:text-slate-200 border border-transparent"
            )}
          >
            {isActive && (
              <motion.div
                layoutId="sidebar-active"
                className="absolute inset-0 rounded-xl bg-gradient-to-r from-indigo-600/10 to-purple-600/10"
                transition={{ type: "spring", stiffness: 300, damping: 30 }}
              />
            )}
            <span
              className={cn(
                "relative z-10 transition-colors",
                isActive ? "text-indigo-400" : "text-slate-500 group-hover:text-indigo-400"
              )}
            >
              {tab.icon}
            </span>
            <div className="relative z-10 flex-1 min-w-0">
              <div className="flex items-center justify-between">
                <span className="text-sm font-semibold truncate">{tab.label}</span>
                {count !== undefined && count > 0 && (
                  <span
                    className={cn(
                      "text-xs font-bold px-1.5 py-0.5 rounded-md",
                      isActive
                        ? "bg-indigo-500/30 text-indigo-300"
                        : "bg-slate-700 text-slate-400"
                    )}
                  >
                    {count}
                  </span>
                )}
              </div>
              <p className="text-xs text-slate-500 truncate">{tab.description}</p>
            </div>
            {isActive && (
              <ChevronRight className="w-3.5 h-3.5 text-indigo-400 relative z-10 shrink-0" />
            )}
          </button>
        );
      })}

      {/* Divider + hint */}
      <div className="mt-auto mb-6 px-4">
        <div className="h-px bg-slate-800 mb-4" />
        <p className="text-xs text-slate-600 leading-relaxed">
          Powered by GPT-4o. All data stored locally in{" "}
          <span className="font-mono text-slate-500">data.json</span>
        </p>
      </div>
    </aside>
  );
}

/** Mobile bottom tab bar */
export function MobileTabBar() {
  const { activeTab, setActiveTab } = useAppStore();

  const mobileTabs = [
    { id: "apply" as TabId, label: "Apply", icon: <Send className="w-5 h-5" /> },
    { id: "tracking" as TabId, label: "Track", icon: <LayoutDashboard className="w-5 h-5" /> },
    { id: "not-selected" as TabId, label: "Rejected", icon: <XCircle className="w-5 h-5" /> },
    { id: "global-analysis" as TabId, label: "Insights", icon: <BarChart3 className="w-5 h-5" /> },
  ];

  return (
    <nav className="lg:hidden fixed bottom-0 left-0 right-0 z-40 bg-slate-950/95 backdrop-blur-xl border-t border-slate-800/60">
      <div className="flex">
        {mobileTabs.map((tab) => {
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={cn(
                "flex-1 flex flex-col items-center gap-1 py-3 text-xs font-medium transition-colors",
                isActive ? "text-indigo-400" : "text-slate-500"
              )}
            >
              {tab.icon}
              {tab.label}
            </button>
          );
        })}
      </div>
    </nav>
  );
}

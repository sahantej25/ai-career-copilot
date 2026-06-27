import { Brain, Github, Sparkles } from "lucide-react";
import { useAppStore } from "@/hooks/useAppStore";
import { Badge } from "@/components/ui/Badge";

export function Header() {
  const profile = useAppStore((s) => s.profile);
  const applications = useAppStore((s) => s.applications);

  return (
    <header className="sticky top-0 z-40 bg-slate-950/80 backdrop-blur-xl border-b border-slate-800/60">
      <div className="max-w-[1400px] mx-auto px-6 h-16 flex items-center justify-between">
        {/* Logo */}
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center shadow-lg shadow-indigo-500/30">
            <Brain className="w-5 h-5 text-white" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-bold text-slate-100 text-lg leading-none">
                AI Career Copilot
              </span>
              <Badge variant="purple" className="text-[10px] py-0">
                <Sparkles className="w-2.5 h-2.5" />
                GPT-4o
              </Badge>
            </div>
            <p className="text-xs text-slate-500 leading-none mt-0.5">
              Your intelligent job application assistant
            </p>
          </div>
        </div>

        {/* Right side stats */}
        <div className="flex items-center gap-6">
          {profile && (
            <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 bg-slate-800/60 rounded-xl border border-slate-700/50">
              <div className="w-6 h-6 rounded-full bg-gradient-to-br from-indigo-400 to-purple-500 flex items-center justify-center text-xs font-bold text-white">
                {profile.name?.charAt(0) || "?"}
              </div>
              <span className="text-sm text-slate-300 font-medium">
                {profile.name || "Profile Loaded"}
              </span>
            </div>
          )}

          {applications.length > 0 && (
            <div className="hidden sm:flex items-center gap-4 text-xs text-slate-400">
              <span>
                <span className="font-semibold text-slate-200">
                  {applications.length}
                </span>{" "}
                applications
              </span>
              <span>
                <span className="font-semibold text-emerald-400">
                  {applications.filter((a) => a.status === "selected").length}
                </span>{" "}
                selected
              </span>
            </div>
          )}

          <a
            href="https://github.com"
            target="_blank"
            rel="noreferrer"
            className="p-2 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition-colors"
          >
            <Github className="w-4 h-4" />
          </a>
        </div>
      </div>
    </header>
  );
}

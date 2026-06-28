import { useEffect, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { useAppStore } from "@/hooks/useAppStore";
import { useAuthStore } from "@/hooks/useAuthStore";
import * as api from "@/lib/api";
import { AuthPage } from "@/components/auth/AuthPage";
import { Header } from "@/components/shared/Header";
import { Sidebar, MobileTabBar } from "@/components/shared/Sidebar";
import { ToastContainer } from "@/components/ui/Toast";
import { Spinner } from "@/components/ui/Spinner";
import { DiscoverTab } from "@/components/tabs/DiscoverTab";
import { ApplyTab } from "@/components/tabs/ApplyTab";
import { TrackingTab } from "@/components/tabs/TrackingTab";
import { NotSelectedTab } from "@/components/tabs/NotSelectedTab";
import { GlobalAnalysisTab } from "@/components/tabs/GlobalAnalysisTab";

const PAGE_VARIANTS = {
  initial: { opacity: 0, y: 16, filter: "blur(6px)" },
  animate: { opacity: 1, y: 0, filter: "blur(0px)" },
  exit: { opacity: 0, y: -12, filter: "blur(6px)" },
};

function TabContent() {
  const activeTab = useAppStore((s) => s.activeTab);
  return (
    <AnimatePresence mode="wait">
      <motion.div key={activeTab} variants={PAGE_VARIANTS} initial="initial" animate="animate" exit="exit" transition={{ duration: 0.35, ease: [0.16, 1, 0.3, 1] }} className="flex-1 overflow-y-auto">
        {activeTab === "discover" && <DiscoverTab />}
        {activeTab === "apply" && <ApplyTab />}
        {activeTab === "tracking" && <TrackingTab />}
        {activeTab === "not-selected" && <NotSelectedTab />}
        {activeTab === "global-analysis" && <GlobalAnalysisTab />}
      </motion.div>
    </AnimatePresence>
  );
}

function AmbientBackground() {
  return (
    <div className="fixed inset-0 -z-10 overflow-hidden pointer-events-none">
      <div className="absolute inset-0 bg-grid [mask-image:radial-gradient(ellipse_at_center,black,transparent_72%)]" />
      <div className="absolute -top-48 -left-28 h-[38rem] w-[38rem] rounded-full bg-brand-300/30 blur-[120px] animate-aurora-drift" />
      <div className="absolute top-1/4 -right-36 h-[34rem] w-[34rem] rounded-full bg-violet-300/25 blur-[120px] animate-aurora-drift-slow" />
      <div className="absolute -bottom-52 left-1/4 h-[32rem] w-[32rem] rounded-full bg-sky-300/22 blur-[130px] animate-aurora-drift" />
      <div className="absolute inset-0 grain-overlay opacity-[0.025]" />
    </div>
  );
}

function useSessionBootstrap() {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const token = useAuthStore((s) => s.token);
  const bootstrapSession = useAuthStore((s) => s.bootstrapSession);
  const refreshLiveJobs = useAuthStore((s) => s.refreshLiveJobs);
  const { setProfile, setApplications, setGlobalAnalysis, setProfileHistory, setReference } = useAppStore();
  const [ready, setReady] = useState(false);

  useEffect(() => {
    if (!isAuthenticated || !token) {
      setReady(false);
      return;
    }
    let cancelled = false;
    (async () => {
      try {
        api.setAuthToken(token);
        await bootstrapSession();
        const data = await api.getAllData();
        if (cancelled) return;
        if (data.current_profile_state) setProfile(data.current_profile_state);
        if (Array.isArray(data.applications)) setApplications(data.applications);
        if (data.global_analysis) setGlobalAnalysis(data.global_analysis);
        if (Array.isArray(data.profile_update_history)) setProfileHistory(data.profile_update_history);
        if (data.reference_resume_loaded) setReference(true, data.reference_resume_name || "");
        await refreshLiveJobs(false);
      } catch {
        /* session restore failed */
      } finally {
        if (!cancelled) setReady(true);
      }
    })();
    return () => { cancelled = true; };
  }, [isAuthenticated, token, bootstrapSession, refreshLiveJobs, setProfile, setApplications, setGlobalAnalysis, setProfileHistory, setReference]);

  return ready;
}

function AuthenticatedApp() {
  const ready = useSessionBootstrap();

  if (!ready) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center gap-4">
        <Spinner size="lg" />
        <p className="text-sm text-ink-500">Loading your workspace & fetching live jobs…</p>
      </div>
    );
  }

  return (
    <>
      <Header />
      <div className="mx-auto flex w-full max-w-[1440px] px-3 sm:px-5" style={{ minHeight: "calc(100vh - 72px)" }}>
        <Sidebar />
        <main className="flex-1 flex flex-col overflow-hidden pb-24 lg:pb-6">
          <TabContent />
        </main>
      </div>
      <MobileTabBar />
    </>
  );
}

export default function App() {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);

  return (
    <div className="relative min-h-screen text-ink-600">
      <AmbientBackground />
      {!isAuthenticated ? <AuthPage /> : <AuthenticatedApp />}
      <ToastContainer />
    </div>
  );
}

import { AnimatePresence, motion } from "framer-motion";
import { useAppStore } from "@/hooks/useAppStore";
import { Header } from "@/components/shared/Header";
import { Sidebar, MobileTabBar } from "@/components/shared/Sidebar";
import { ToastContainer } from "@/components/ui/Toast";
import { ApplyTab } from "@/components/tabs/ApplyTab";
import { TrackingTab } from "@/components/tabs/TrackingTab";
import { NotSelectedTab } from "@/components/tabs/NotSelectedTab";
import { GlobalAnalysisTab } from "@/components/tabs/GlobalAnalysisTab";

const PAGE_VARIANTS = {
  initial: { opacity: 0, y: 12 },
  animate: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: -12 },
};

function TabContent() {
  const activeTab = useAppStore((s) => s.activeTab);

  return (
    <AnimatePresence mode="wait">
      <motion.div
        key={activeTab}
        variants={PAGE_VARIANTS}
        initial="initial"
        animate="animate"
        exit="exit"
        transition={{ duration: 0.25, ease: "easeInOut" }}
        className="flex-1 overflow-y-auto"
      >
        {activeTab === "apply" && <ApplyTab />}
        {activeTab === "tracking" && <TrackingTab />}
        {activeTab === "not-selected" && <NotSelectedTab />}
        {activeTab === "global-analysis" && <GlobalAnalysisTab />}
      </motion.div>
    </AnimatePresence>
  );
}

export default function App() {
  return (
    <div className="min-h-screen bg-slate-950">
      {/* Ambient background gradients */}
      <div className="fixed inset-0 pointer-events-none overflow-hidden">
        <div className="absolute -top-40 -left-40 w-96 h-96 bg-indigo-600/8 rounded-full blur-3xl" />
        <div className="absolute top-1/3 -right-20 w-80 h-80 bg-purple-600/8 rounded-full blur-3xl" />
        <div className="absolute bottom-1/4 left-1/3 w-64 h-64 bg-blue-600/6 rounded-full blur-3xl" />
      </div>

      <Header />

      <div className="max-w-[1400px] mx-auto flex" style={{ minHeight: "calc(100vh - 64px)" }}>
        <Sidebar />

        <main className="flex-1 flex flex-col overflow-hidden pb-16 lg:pb-0">
          <TabContent />
        </main>
      </div>

      <MobileTabBar />
      <ToastContainer />
    </div>
  );
}

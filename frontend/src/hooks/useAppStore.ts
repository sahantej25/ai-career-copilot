import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";
import type {
  CandidateProfile, Application, MatchResult,
  GlobalAnalysis, ProfileUpdate, TabId,
} from "@/types";

interface Toast {
  id: string;
  type: "success" | "error" | "info" | "loading";
  message: string;
}

interface AppStore {
  // Navigation
  activeTab: TabId;
  setActiveTab: (tab: TabId) => void;

  // Profile
  profile: CandidateProfile | null;
  setProfile: (p: CandidateProfile | null) => void;

  // Current apply flow state
  currentMatch: MatchResult | null;
  setCurrentMatch: (m: MatchResult | null) => void;
  currentJD: string;
  setCurrentJD: (jd: string) => void;
  currentCompany: string;
  setCurrentCompany: (c: string) => void;
  currentRole: string;
  setCurrentRole: (r: string) => void;

  // Applications
  applications: Application[];
  setApplications: (apps: Application[]) => void;
  upsertApplication: (app: Application) => void;
  removeApplication: (id: string) => void;

  // Analysis
  globalAnalysis: GlobalAnalysis | null;
  setGlobalAnalysis: (g: GlobalAnalysis | null) => void;
  profileHistory: ProfileUpdate[];
  setProfileHistory: (h: ProfileUpdate[]) => void;

  // UI
  toasts: Toast[];
  addToast: (toast: Omit<Toast, "id">) => void;
  removeToast: (id: string) => void;
  isLoading: Record<string, boolean>;
  setLoading: (key: string, val: boolean) => void;
}

export const useAppStore = create<AppStore>()(
  persist(
    (set, get) => ({
      activeTab: "apply",
      setActiveTab: (tab) => set({ activeTab: tab }),

      profile: null,
      setProfile: (p) => set({ profile: p }),

      currentMatch: null,
      setCurrentMatch: (m) => set({ currentMatch: m }),
      currentJD: "",
      setCurrentJD: (jd) => set({ currentJD: jd }),
      currentCompany: "",
      setCurrentCompany: (c) => set({ currentCompany: c }),
      currentRole: "",
      setCurrentRole: (r) => set({ currentRole: r }),

      applications: [],
      setApplications: (apps) => set({ applications: apps }),
      upsertApplication: (app) =>
        set((s) => {
          const idx = s.applications.findIndex((a) => a.id === app.id);
          const updated = [...s.applications];
          if (idx >= 0) updated[idx] = app;
          else updated.unshift(app);
          return { applications: updated };
        }),
      removeApplication: (id) =>
        set((s) => ({ applications: s.applications.filter((a) => a.id !== id) })),

      globalAnalysis: null,
      setGlobalAnalysis: (g) => set({ globalAnalysis: g }),
      profileHistory: [],
      setProfileHistory: (h) => set({ profileHistory: h }),

      toasts: [],
      addToast: (toast) => {
        const id = Math.random().toString(36).slice(2);
        set((s) => ({ toasts: [...s.toasts, { ...toast, id }] }));
        if (toast.type !== "loading") {
          setTimeout(() => get().removeToast(id), 4000);
        }
      },
      removeToast: (id) =>
        set((s) => ({ toasts: s.toasts.filter((t) => t.id !== id) })),

      isLoading: {},
      setLoading: (key, val) =>
        set((s) => ({ isLoading: { ...s.isLoading, [key]: val } })),
    }),
    {
      name: "career-copilot-store",
      storage: createJSONStorage(() => sessionStorage),
      partialize: (s) => ({
        profile: s.profile,
        applications: s.applications,
        globalAnalysis: s.globalAnalysis,
        profileHistory: s.profileHistory,
        currentJD: s.currentJD,
        currentCompany: s.currentCompany,
        currentRole: s.currentRole,
        currentMatch: s.currentMatch,
      }),
    }
  )
);

import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";
import type { JobListing, JobPreferences } from "@/types";
import * as api from "@/lib/api";

export interface AuthUser {
  id: string;
  email: string;
  name: string;
}

interface AuthStore {
  token: string | null;
  user: AuthUser | null;
  isAuthenticated: boolean;
  liveJobs: JobListing[];
  liveJobsFetchedAt: string | null;
  liveJobsFromCache: boolean;
  jobPreferences: JobPreferences | null;

  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, name: string) => Promise<void>;
  logout: () => void;
  bootstrapSession: () => Promise<void>;
  refreshLiveJobs: (force?: boolean) => Promise<void>;
  setJobPreferences: (prefs: JobPreferences) => void;
}

export const useAuthStore = create<AuthStore>()(
  persist(
    (set, get) => ({
      token: null,
      user: null,
      isAuthenticated: false,
      liveJobs: [],
      liveJobsFetchedAt: null,
      liveJobsFromCache: false,
      jobPreferences: null,

      login: async (email, password) => {
        const res = await api.login(email, password);
        api.setAuthToken(res.access_token);
        set({ token: res.access_token, user: res.user, isAuthenticated: true });
        await get().bootstrapSession();
        await get().refreshLiveJobs(true);
      },

      register: async (email, password, name) => {
        const res = await api.register(email, password, name);
        api.setAuthToken(res.access_token);
        set({ token: res.access_token, user: res.user, isAuthenticated: true });
        await get().bootstrapSession();
        await get().refreshLiveJobs(true);
      },

      logout: () => {
        api.setAuthToken(null);
        set({
          token: null,
          user: null,
          isAuthenticated: false,
          liveJobs: [],
          liveJobsFetchedAt: null,
          liveJobsFromCache: false,
          jobPreferences: null,
        });
      },

      bootstrapSession: async () => {
        const session = await api.getSession();
        set({
          user: session.user,
          jobPreferences: session.data.job_preferences || null,
          liveJobsFetchedAt: session.live_jobs_fetched_at,
        });
        if (session.data.cached_live_jobs?.length) {
          set({ liveJobs: session.data.cached_live_jobs });
        }
      },

      refreshLiveJobs: async (force = false) => {
        const data = await api.fetchLiveJobs(force);
        set({
          liveJobs: data.jobs,
          liveJobsFetchedAt: data.fetched_at,
          liveJobsFromCache: data.from_cache ?? false,
          jobPreferences: data.preferences || get().jobPreferences,
        });
      },

      setJobPreferences: (prefs) => set({ jobPreferences: prefs }),
    }),
    {
      name: "career-copilot-auth",
      storage: createJSONStorage(() => localStorage),
      partialize: (s) => ({ token: s.token, user: s.user, isAuthenticated: s.isAuthenticated }),
      onRehydrateStorage: () => (state) => {
        if (state?.token) api.setAuthToken(state.token);
      },
    }
  )
);

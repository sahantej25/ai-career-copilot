import { beforeEach, describe, expect, it } from "vitest";
import { useAppStore } from "@/hooks/useAppStore";
import type { Application, CandidateProfile } from "@/types";

const sampleProfile: CandidateProfile = {
  name: "Jane Doe",
  email: "jane@example.com",
  phone: "",
  location: "SF",
  summary: "Engineer",
  skills: [{ name: "React", confidence: 90, category: "frontend" }],
  projects: [],
  experience: [],
  education: [],
  domains: [],
};

const sampleApp: Application = {
  id: "app-001",
  company: "Acme",
  role: "Frontend Engineer",
  job_description: "React role",
  match_percentage: 80,
  matched_skills: ["React"],
  missing_skills: ["GraphQL"],
  status: "submitted",
  submitted_at: "2026-01-01T00:00:00Z",
  updated_at: "2026-01-01T00:00:00Z",
};

function resetStore() {
  useAppStore.setState({
    activeTab: "apply",
    profile: null,
    currentMatch: null,
    currentJD: "",
    currentCompany: "",
    currentRole: "",
    currentSkillsRequired: [],
    referenceLoaded: false,
    referenceName: "",
    applications: [],
    globalAnalysis: null,
    profileHistory: [],
    toasts: [],
    isLoading: {},
  });
}

describe("useAppStore", () => {
  beforeEach(() => {
    resetStore();
  });

  it("sets and reads profile", () => {
    useAppStore.getState().setProfile(sampleProfile);
    expect(useAppStore.getState().profile?.name).toBe("Jane Doe");
  });

  it("upserts applications (insert then update)", () => {
    const { upsertApplication } = useAppStore.getState();
    upsertApplication(sampleApp);
    expect(useAppStore.getState().applications).toHaveLength(1);

    upsertApplication({ ...sampleApp, status: "interview" });
    expect(useAppStore.getState().applications[0].status).toBe("interview");
    expect(useAppStore.getState().applications).toHaveLength(1);
  });

  it("removes an application by id", () => {
    useAppStore.getState().upsertApplication(sampleApp);
    useAppStore.getState().removeApplication("app-001");
    expect(useAppStore.getState().applications).toHaveLength(0);
  });

  it("tracks apply-flow fields", () => {
    const store = useAppStore.getState();
    store.setCurrentJD("Build React apps");
    store.setCurrentCompany("Acme");
    store.setCurrentRole("Frontend Engineer");
    store.setCurrentSkillsRequired(["React", "TypeScript"]);
    store.setReference(true, "reference.pdf");

    const state = useAppStore.getState();
    expect(state.currentJD).toBe("Build React apps");
    expect(state.currentCompany).toBe("Acme");
    expect(state.currentRole).toBe("Frontend Engineer");
    expect(state.currentSkillsRequired).toEqual(["React", "TypeScript"]);
    expect(state.referenceLoaded).toBe(true);
    expect(state.referenceName).toBe("reference.pdf");
  });

  it("resetAll clears persisted application state", () => {
    const store = useAppStore.getState();
    store.setProfile(sampleProfile);
    store.upsertApplication(sampleApp);
    store.setCurrentJD("JD text");
    store.setReference(true, "ref.pdf");

    store.resetAll();

    const cleared = useAppStore.getState();
    expect(cleared.profile).toBeNull();
    expect(cleared.applications).toEqual([]);
    expect(cleared.currentJD).toBe("");
    expect(cleared.referenceLoaded).toBe(false);
  });

  it("manages toasts", () => {
    useAppStore.getState().addToast({ type: "success", message: "Saved" });
    expect(useAppStore.getState().toasts).toHaveLength(1);
    expect(useAppStore.getState().toasts[0].message).toBe("Saved");

    const id = useAppStore.getState().toasts[0].id;
    useAppStore.getState().removeToast(id);
    expect(useAppStore.getState().toasts).toHaveLength(0);
  });

  it("tracks loading flags per key", () => {
    useAppStore.getState().setLoading("match", true);
    expect(useAppStore.getState().isLoading.match).toBe(true);

    useAppStore.getState().setLoading("match", false);
    expect(useAppStore.getState().isLoading.match).toBe(false);
  });
});

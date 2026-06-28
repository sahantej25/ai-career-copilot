import { useEffect, useState } from "react";
import { User, Plus, X } from "lucide-react";
import { Modal } from "@/components/ui/Modal";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { useAppStore } from "@/hooks/useAppStore";
import * as api from "@/lib/api";
import type { CandidateProfile, Skill } from "@/types";

const EMPTY_PROFILE: CandidateProfile = {
  name: "",
  email: "",
  phone: "",
  location: "",
  summary: "",
  skills: [],
  projects: [],
  experience: [],
  education: [],
  domains: [],
};

function inputClass(extra = "") {
  return `w-full rounded-xl border border-slate-200 bg-white/80 px-3 py-2.5 text-sm text-ink-800 outline-none transition-colors placeholder:text-ink-400 focus:border-brand-400 focus:ring-2 focus:ring-brand-100 ${extra}`;
}

export function ProfileModal() {
  const open = useAppStore((s) => s.profileModalOpen);
  const setOpen = useAppStore((s) => s.setProfileModalOpen);
  const profile = useAppStore((s) => s.profile);
  const setProfile = useAppStore((s) => s.setProfile);
  const addToast = useAppStore((s) => s.addToast);
  const isLoading = useAppStore((s) => s.isLoading);
  const setLoading = useAppStore((s) => s.setLoading);

  const [form, setForm] = useState<CandidateProfile>(EMPTY_PROFILE);
  const [skillInput, setSkillInput] = useState("");
  const [domainInput, setDomainInput] = useState("");

  useEffect(() => {
    if (open) {
      setForm(profile ? { ...profile } : { ...EMPTY_PROFILE });
      setSkillInput("");
      setDomainInput("");
    }
  }, [open, profile]);

  const update = <K extends keyof CandidateProfile>(key: K, value: CandidateProfile[K]) => {
    setForm((prev) => ({ ...prev, [key]: value }));
  };

  const addSkill = () => {
    const name = skillInput.trim();
    if (!name) return;
    if (form.skills.some((s) => s.name.toLowerCase() === name.toLowerCase())) {
      setSkillInput("");
      return;
    }
    const skill: Skill = { name, confidence: 70, category: "general" };
    update("skills", [...form.skills, skill]);
    setSkillInput("");
  };

  const removeSkill = (name: string) => {
    update("skills", form.skills.filter((s) => s.name !== name));
  };

  const addDomain = () => {
    const d = domainInput.trim();
    if (!d || form.domains.includes(d)) {
      setDomainInput("");
      return;
    }
    update("domains", [...form.domains, d]);
    setDomainInput("");
  };

  const handleSave = async () => {
    setLoading("profile-save", true);
    try {
      const saved = await api.saveProfile(form);
      setProfile(saved);
      addToast({ type: "success", message: `Profile saved${saved.name ? `: ${saved.name}` : ""}` });
      setOpen(false);
    } catch (e: unknown) {
      addToast({ type: "error", message: e instanceof Error ? e.message : "Failed to save profile" });
    } finally {
      setLoading("profile-save", false);
    }
  };

  const handleClear = async () => {
    setLoading("profile-save", true);
    try {
      await api.clearProfile();
      setProfile(null);
      setForm({ ...EMPTY_PROFILE });
      addToast({ type: "info", message: "Profile cleared." });
      setOpen(false);
    } catch (e: unknown) {
      addToast({ type: "error", message: e instanceof Error ? e.message : "Failed to clear profile" });
    } finally {
      setLoading("profile-save", false);
    }
  };

  const busy = isLoading["profile-save"];

  return (
    <Modal
      open={open}
      onClose={() => setOpen(false)}
      size="lg"
      title={
        <span className="flex items-center gap-2">
          <User className="h-5 w-5 text-brand-600" />
          Candidate Profile
        </span>
      }
      description="Add or edit your details manually — no resume upload required. You can also parse a resume from the Apply tab."
      footer={
        <>
          {profile && (
            <Button variant="secondary" onClick={handleClear} loading={busy} className="mr-auto !text-rose-600">
              Clear profile
            </Button>
          )}
          <Button variant="secondary" onClick={() => setOpen(false)} disabled={busy}>
            Cancel
          </Button>
          <Button onClick={handleSave} loading={busy}>
            Save profile
          </Button>
        </>
      }
    >
      <div className="max-h-[60vh] space-y-4 overflow-y-auto pr-1">
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
          <label className="block space-y-1.5">
            <span className="text-xs font-medium text-ink-500">Full name</span>
            <input className={inputClass()} value={form.name} onChange={(e) => update("name", e.target.value)} placeholder="Jane Doe" />
          </label>
          <label className="block space-y-1.5">
            <span className="text-xs font-medium text-ink-500">Email</span>
            <input className={inputClass()} type="email" value={form.email} onChange={(e) => update("email", e.target.value)} placeholder="jane@example.com" />
          </label>
          <label className="block space-y-1.5">
            <span className="text-xs font-medium text-ink-500">Phone</span>
            <input className={inputClass()} value={form.phone} onChange={(e) => update("phone", e.target.value)} placeholder="+1 555 0100" />
          </label>
          <label className="block space-y-1.5">
            <span className="text-xs font-medium text-ink-500">Location</span>
            <input className={inputClass()} value={form.location} onChange={(e) => update("location", e.target.value)} placeholder="San Francisco, CA" />
          </label>
        </div>

        <label className="block space-y-1.5">
          <span className="text-xs font-medium text-ink-500">Professional summary</span>
          <textarea
            className={inputClass("min-h-[88px] resize-y")}
            value={form.summary}
            onChange={(e) => update("summary", e.target.value)}
            placeholder="Brief overview of your experience and strengths…"
          />
        </label>

        <div className="space-y-2">
          <span className="text-xs font-medium text-ink-500">Skills</span>
          <div className="flex gap-2">
            <input
              className={inputClass("flex-1")}
              value={skillInput}
              onChange={(e) => setSkillInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && (e.preventDefault(), addSkill())}
              placeholder="Add a skill (e.g. React)"
            />
            <Button type="button" variant="secondary" onClick={addSkill} disabled={!skillInput.trim()}>
              <Plus className="h-4 w-4" />
            </Button>
          </div>
          {form.skills.length > 0 && (
            <div className="flex flex-wrap gap-1.5">
              {form.skills.map((s) => (
                <Badge key={s.name} variant="info" className="gap-1 pr-1">
                  {s.name}
                  <button type="button" onClick={() => removeSkill(s.name)} className="rounded p-0.5 hover:bg-sky-100 cursor-pointer" aria-label={`Remove ${s.name}`}>
                    <X className="h-3 w-3" />
                  </button>
                </Badge>
              ))}
            </div>
          )}
        </div>

        <div className="space-y-2">
          <span className="text-xs font-medium text-ink-500">Domains / focus areas</span>
          <div className="flex gap-2">
            <input
              className={inputClass("flex-1")}
              value={domainInput}
              onChange={(e) => setDomainInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && (e.preventDefault(), addDomain())}
              placeholder="e.g. web, ai, fintech"
            />
            <Button type="button" variant="secondary" onClick={addDomain} disabled={!domainInput.trim()}>
              <Plus className="h-4 w-4" />
            </Button>
          </div>
          {form.domains.length > 0 && (
            <div className="flex flex-wrap gap-1.5">
              {form.domains.map((d) => (
                <Badge key={d} variant="purple">{d}</Badge>
              ))}
            </div>
          )}
        </div>
      </div>
    </Modal>
  );
}

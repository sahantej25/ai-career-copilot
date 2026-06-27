import { useState, useCallback } from "react";
import { useDropzone } from "react-dropzone";
import { motion, AnimatePresence } from "framer-motion";
import {
  Upload, FileText, Briefcase, Zap, Download, CheckCircle2,
  UploadCloud, X, RefreshCw, Target, AlertCircle, ChevronRight,
} from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Progress, AnimatedCounter } from "@/components/ui/Progress";
import { Spinner } from "@/components/ui/Spinner";
import { useAppStore } from "@/hooks/useAppStore";
import { cn, getMatchColor } from "@/lib/utils";
import * as api from "@/lib/api";

type Step = "profile" | "jd" | "match" | "generate" | "submit";

function StepIndicator({ step, current }: { step: Step; current: Step }) {
  const steps: Step[] = ["profile", "jd", "match", "generate", "submit"];
  const idx = steps.indexOf(step);
  const cur = steps.indexOf(current);
  const done = cur > idx;
  const active = cur === idx;

  return (
    <div className={cn("flex items-center gap-2 text-xs font-medium transition-colors",
      done ? "text-emerald-400" : active ? "text-indigo-400" : "text-slate-500")}>
      <span className={cn("w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold",
        done ? "bg-emerald-500 text-white" : active ? "bg-indigo-500 text-white" : "bg-slate-800 text-slate-500")}>
        {done ? "✓" : idx + 1}
      </span>
      <span className="hidden sm:block">
        {step === "profile" ? "Profile" : step === "jd" ? "Job Description" : step === "match" ? "Match" : step === "generate" ? "Resume" : "Submit"}
      </span>
    </div>
  );
}

function FileDropZone({ onFile, file, label, accept }: {
  onFile: (f: File) => void;
  file: File | null;
  label: string;
  accept?: string;
}) {
  const onDrop = useCallback((accepted: File[]) => {
    if (accepted[0]) onFile(accepted[0]);
  }, [onFile]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    maxFiles: 1,
    accept: {
      "application/pdf": [".pdf"],
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [".docx"],
      "text/plain": [".txt"],
    },
  });

  return (
    <div
      {...getRootProps()}
      className={cn(
        "relative border-2 border-dashed rounded-xl p-6 text-center cursor-pointer transition-all duration-200",
        isDragActive
          ? "border-indigo-500 bg-indigo-500/10"
          : file
          ? "border-emerald-500/50 bg-emerald-500/5"
          : "border-slate-700 hover:border-indigo-500/50 hover:bg-slate-800/30"
      )}
    >
      <input {...getInputProps()} />
      <AnimatePresence mode="wait">
        {file ? (
          <motion.div
            key="file"
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            className="flex items-center gap-3"
          >
            <div className="w-10 h-10 rounded-lg bg-emerald-500/20 flex items-center justify-center shrink-0">
              <FileText className="w-5 h-5 text-emerald-400" />
            </div>
            <div className="text-left flex-1 min-w-0">
              <p className="text-sm font-medium text-emerald-400 truncate">{file.name}</p>
              <p className="text-xs text-slate-500">{(file.size / 1024).toFixed(0)} KB</p>
            </div>
            <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0" />
          </motion.div>
        ) : (
          <motion.div key="empty" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
            <UploadCloud className={cn("w-8 h-8 mx-auto mb-2", isDragActive ? "text-indigo-400" : "text-slate-600")} />
            <p className="text-sm text-slate-400 font-medium">{label}</p>
            <p className="text-xs text-slate-600 mt-1">PDF, DOCX, TXT · Max 10MB</p>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

export function ApplyTab() {
  const {
    profile, setProfile, currentJD, setCurrentJD,
    currentCompany, setCurrentCompany, currentRole, setCurrentRole,
    currentMatch, setCurrentMatch, upsertApplication, setActiveTab,
    addToast, isLoading, setLoading,
  } = useAppStore();

  const [resumeFile, setResumeFile] = useState<File | null>(null);
  const [currentStep, setCurrentStep] = useState<Step>(profile ? "jd" : "profile");
  const [submitted, setSubmitted] = useState(false);

  const loading = (k: string) => isLoading[k] ?? false;

  const handleUploadProfile = async () => {
    if (!resumeFile) return;
    setLoading("upload", true);
    try {
      const parsed = await api.uploadProfile(resumeFile);
      setProfile(parsed);
      setCurrentStep("jd");
      addToast({ type: "success", message: `Profile loaded: ${parsed.name || "Candidate"}` });
    } catch (e: any) {
      addToast({ type: "error", message: e.message });
    } finally {
      setLoading("upload", false);
    }
  };

  const handleMatch = async () => {
    if (!currentJD.trim()) return;
    setLoading("match", true);
    try {
      const result = await api.matchJob(currentJD, currentCompany, currentRole);
      setCurrentMatch(result);
      setCurrentStep("match");
      addToast({ type: "success", message: "Skills extracted & matched!" });
    } catch (e: any) {
      addToast({ type: "error", message: e.message });
    } finally {
      setLoading("match", false);
    }
  };

  const handleGenerateResume = async () => {
    setLoading("generate", true);
    try {
      const blob = await api.generateResume(currentJD, currentCompany, currentRole);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `resume_${currentCompany || "tailored"}.pdf`;
      a.click();
      URL.revokeObjectURL(url);
      setCurrentStep("generate");
      addToast({ type: "success", message: "Tailored resume downloaded!" });
    } catch (e: any) {
      addToast({ type: "error", message: e.message });
    } finally {
      setLoading("generate", false);
    }
  };

  const handleSubmit = async () => {
    if (!currentMatch) return;
    setLoading("submit", true);
    try {
      const app = await api.submitApplication({
        company: currentCompany,
        role: currentRole,
        job_description: currentJD,
        match_percentage: currentMatch.match_percentage,
        matched_skills: currentMatch.matched_skills,
        missing_skills: currentMatch.missing_skills,
      });
      upsertApplication(app);
      setSubmitted(true);
      setCurrentStep("submit");
      addToast({ type: "success", message: `Application to ${currentCompany} logged!` });
    } catch (e: any) {
      addToast({ type: "error", message: e.message });
    } finally {
      setLoading("submit", false);
    }
  };

  const handleReset = () => {
    setCurrentJD(""); setCurrentCompany(""); setCurrentRole("");
    setCurrentMatch(null); setSubmitted(false);
    setCurrentStep(profile ? "jd" : "profile");
  };

  return (
    <div className="p-6 space-y-6 max-w-4xl">
      {/* Page title */}
      <div>
        <h1 className="text-2xl font-bold gradient-text">Prepare & Apply</h1>
        <p className="text-slate-400 text-sm mt-1">
          Upload your resume, match it to a job description, generate a tailored PDF, and submit.
        </p>
      </div>

      {/* Step progress */}
      <div className="flex items-center gap-3 overflow-x-auto pb-1">
        {(["profile", "jd", "match", "generate", "submit"] as Step[]).map((s, i) => (
          <div key={s} className="flex items-center gap-2 shrink-0">
            <StepIndicator step={s} current={currentStep} />
            {i < 4 && <ChevronRight className="w-3 h-3 text-slate-700 shrink-0" />}
          </div>
        ))}
      </div>

      {/* Step 1: Profile Upload */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <Upload className="w-5 h-5 text-indigo-400" />
              Step 1: Candidate Profile
            </CardTitle>
            {profile && (
              <Badge variant="success" dot>Profile loaded</Badge>
            )}
          </div>
        </CardHeader>
        <CardContent>
          {profile ? (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="space-y-4"
            >
              <div className="flex items-center gap-4 p-4 bg-emerald-500/5 border border-emerald-500/20 rounded-xl">
                <div className="w-12 h-12 rounded-full bg-gradient-to-br from-indigo-400 to-purple-500 flex items-center justify-center text-lg font-bold text-white">
                  {profile.name?.charAt(0) || "?"}
                </div>
                <div>
                  <p className="font-semibold text-slate-100">{profile.name}</p>
                  <p className="text-sm text-slate-400">{profile.email}</p>
                  <div className="flex flex-wrap gap-1.5 mt-2">
                    {profile.domains.slice(0, 4).map((d) => (
                      <Badge key={d} variant="purple">{d}</Badge>
                    ))}
                  </div>
                </div>
                <button
                  onClick={() => { setProfile(null); setResumeFile(null); setCurrentStep("profile"); }}
                  className="ml-auto text-slate-500 hover:text-slate-300 p-1"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>

              <div>
                <p className="section-label mb-2">Skills ({profile.skills.length})</p>
                <div className="flex flex-wrap gap-2">
                  {profile.skills.slice(0, 20).map((s) => (
                    <div key={s.name} className="flex items-center gap-1.5 bg-slate-800/60 border border-slate-700/50 rounded-lg px-2.5 py-1">
                      <span className="text-xs text-slate-300">{s.name}</span>
                      <span className="text-[10px] text-indigo-400 font-bold">{s.confidence.toFixed(0)}%</span>
                    </div>
                  ))}
                  {profile.skills.length > 20 && (
                    <span className="text-xs text-slate-500 py-1">+{profile.skills.length - 20} more</span>
                  )}
                </div>
              </div>
            </motion.div>
          ) : (
            <div className="space-y-4">
              <FileDropZone
                onFile={setResumeFile}
                file={resumeFile}
                label="Drop your resume here or click to browse"
              />
              <Button
                onClick={handleUploadProfile}
                disabled={!resumeFile}
                loading={loading("upload")}
                className="w-full"
              >
                <Upload className="w-4 h-4" />
                {loading("upload") ? "Parsing with AI..." : "Parse Resume"}
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Step 2: Job Description */}
      <AnimatePresence>
        {(profile || currentStep !== "profile") && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
          >
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Briefcase className="w-5 h-5 text-indigo-400" />
                  Step 2: Job Description
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="section-label block mb-1.5">Company</label>
                    <input
                      className="input-field"
                      placeholder="e.g. Google"
                      value={currentCompany}
                      onChange={(e) => setCurrentCompany(e.target.value)}
                    />
                  </div>
                  <div>
                    <label className="section-label block mb-1.5">Role</label>
                    <input
                      className="input-field"
                      placeholder="e.g. Senior Software Engineer"
                      value={currentRole}
                      onChange={(e) => setCurrentRole(e.target.value)}
                    />
                  </div>
                </div>
                <div>
                  <label className="section-label block mb-1.5">
                    Job Description
                  </label>
                  <textarea
                    className="input-field resize-none"
                    rows={8}
                    placeholder="Paste the full job description here..."
                    value={currentJD}
                    onChange={(e) => setCurrentJD(e.target.value)}
                  />
                </div>
                <Button
                  onClick={handleMatch}
                  disabled={!currentJD.trim() || !profile}
                  loading={loading("match")}
                  className="w-full"
                >
                  <Zap className="w-4 h-4" />
                  {loading("match") ? "Extracting & Matching Skills..." : "Extract Skills & Calculate Match"}
                </Button>
              </CardContent>
            </Card>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Step 3: Match Results */}
      <AnimatePresence>
        {currentMatch && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
          >
            <Card className="border-indigo-500/20">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Target className="w-5 h-5 text-indigo-400" />
                  Match Analysis
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* Big match percentage */}
                <div className="flex items-center gap-6">
                  <div className="relative w-24 h-24 shrink-0">
                    <svg className="w-24 h-24 -rotate-90" viewBox="0 0 80 80">
                      <circle cx="40" cy="40" r="34" fill="none" stroke="#1e293b" strokeWidth="8" />
                      <motion.circle
                        cx="40" cy="40" r="34" fill="none"
                        stroke={currentMatch.match_percentage >= 75 ? "#10b981" : currentMatch.match_percentage >= 50 ? "#f59e0b" : "#ef4444"}
                        strokeWidth="8"
                        strokeLinecap="round"
                        strokeDasharray={`${2 * Math.PI * 34}`}
                        initial={{ strokeDashoffset: 2 * Math.PI * 34 }}
                        animate={{ strokeDashoffset: 2 * Math.PI * 34 * (1 - currentMatch.match_percentage / 100) }}
                        transition={{ duration: 1.5, ease: "easeOut" }}
                      />
                    </svg>
                    <div className="absolute inset-0 flex items-center justify-center">
                      <AnimatedCounter
                        value={currentMatch.match_percentage}
                        suffix="%"
                        className={cn("text-xl font-black", getMatchColor(currentMatch.match_percentage))}
                      />
                    </div>
                  </div>
                  <div className="flex-1">
                    <p className="text-slate-100 font-semibold text-lg">
                      {currentMatch.match_percentage >= 75
                        ? "Strong Match!"
                        : currentMatch.match_percentage >= 50
                        ? "Moderate Match"
                        : "Low Match"}
                    </p>
                    <p className="text-sm text-slate-400 mt-1">{currentMatch.recommendation}</p>
                  </div>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  {/* Matched skills */}
                  <div>
                    <p className="section-label mb-2 flex items-center gap-1.5">
                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                      Matched ({currentMatch.matched_skills.length})
                    </p>
                    <div className="flex flex-wrap gap-1.5">
                      {currentMatch.matched_skills.map((s) => (
                        <Badge key={s} variant="success">{s}</Badge>
                      ))}
                    </div>
                  </div>

                  {/* Missing skills */}
                  <div>
                    <p className="section-label mb-2 flex items-center gap-1.5">
                      <AlertCircle className="w-3.5 h-3.5 text-red-400" />
                      Missing ({currentMatch.missing_skills.length})
                    </p>
                    <div className="flex flex-wrap gap-1.5">
                      {currentMatch.missing_skills.map((s) => (
                        <Badge key={s} variant="danger">{s}</Badge>
                      ))}
                    </div>
                  </div>
                </div>

                {/* Progress bar */}
                <div>
                  <div className="flex justify-between text-xs text-slate-500 mb-1.5">
                    <span>Match score</span>
                    <span>{currentMatch.match_percentage.toFixed(0)}%</span>
                  </div>
                  <Progress value={currentMatch.match_percentage} colorByValue size="lg" />
                </div>

                {/* Generate resume */}
                <Button
                  onClick={handleGenerateResume}
                  loading={loading("generate")}
                  className="w-full"
                >
                  <Download className="w-4 h-4" />
                  {loading("generate") ? "Generating Tailored Resume..." : "Generate & Download Tailored Resume"}
                </Button>
              </CardContent>
            </Card>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Step 4+5: Submit */}
      <AnimatePresence>
        {currentMatch && !submitted && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
          >
            <Card className="border-dashed border-amber-500/20 bg-amber-500/3">
              <CardContent className="flex items-center gap-4 py-2">
                <div className="w-10 h-10 rounded-xl bg-amber-500/15 flex items-center justify-center shrink-0">
                  <Upload className="w-5 h-5 text-amber-400" />
                </div>
                <div className="flex-1">
                  <p className="text-sm font-semibold text-slate-200">
                    Applied externally?
                  </p>
                  <p className="text-xs text-slate-500">
                    Once you submit on LinkedIn/Workday/company portal, click below to log it.
                  </p>
                </div>
                <Button
                  variant="outline"
                  onClick={handleSubmit}
                  loading={loading("submit")}
                >
                  <CheckCircle2 className="w-4 h-4" />
                  Mark as Submitted
                </Button>
              </CardContent>
            </Card>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Success state */}
      <AnimatePresence>
        {submitted && (
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            className="text-center py-8"
          >
            <motion.div
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{ type: "spring", stiffness: 300, damping: 20 }}
              className="w-16 h-16 rounded-full bg-emerald-500/20 flex items-center justify-center mx-auto mb-4"
            >
              <CheckCircle2 className="w-8 h-8 text-emerald-400" />
            </motion.div>
            <h3 className="text-xl font-bold text-slate-100">Application Logged!</h3>
            <p className="text-slate-400 text-sm mt-1 mb-6">
              {currentCompany} → {currentRole} has been added to your tracker.
            </p>
            <div className="flex items-center justify-center gap-3">
              <Button onClick={() => { setActiveTab("tracking"); }}>
                View in Tracker
              </Button>
              <Button variant="secondary" onClick={handleReset}>
                <RefreshCw className="w-4 h-4" />
                New Application
              </Button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

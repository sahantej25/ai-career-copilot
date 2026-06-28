import { useState } from "react";
import { motion } from "framer-motion";
import { Brain, Mail, Lock, User, Sparkles, ArrowRight } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { useAuthStore } from "@/hooks/useAuthStore";
import { cn } from "@/lib/utils";

type Mode = "login" | "register";

export function AuthPage() {
  const { login, register } = useAuthStore();
  const [mode, setMode] = useState<Mode>("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      if (mode === "login") {
        await login(email, password);
      } else {
        await register(email, password, name);
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Authentication failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="relative flex min-h-screen items-center justify-center p-4">
      <div className="absolute inset-0 -z-10 bg-grid [mask-image:radial-gradient(ellipse_at_center,black,transparent_70%)]" />
      <div className="absolute -top-32 left-1/4 h-96 w-96 rounded-full bg-brand-300/30 blur-[120px]" />
      <div className="absolute bottom-0 right-1/4 h-80 w-80 rounded-full bg-violet-300/25 blur-[120px]" />

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="w-full max-w-md"
      >
        <div className="mb-8 text-center">
          <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-brand-500 to-teal-600 shadow-glow">
            <Brain className="h-7 w-7 text-white" />
          </div>
          <h1 className="font-display text-2xl font-bold text-ink-900">AI Career Copilot</h1>
          <p className="mt-2 text-sm text-ink-500">
            Sign in to fetch live jobs from LinkedIn, Greenhouse & Hiring Cafe and track your pipeline professionally.
          </p>
        </div>

        <div className="glass glass-edge rounded-3xl p-8">
          <div className="mb-6 flex rounded-xl bg-slate-100/80 p-1">
            {(["login", "register"] as Mode[]).map((m) => (
              <button
                key={m}
                type="button"
                onClick={() => { setMode(m); setError(""); }}
                className={cn(
                  "flex-1 rounded-lg py-2 text-sm font-semibold capitalize transition-all cursor-pointer",
                  mode === m ? "bg-white text-ink-900 shadow-soft" : "text-ink-500 hover:text-ink-700"
                )}
              >
                {m === "login" ? "Sign in" : "Create account"}
              </button>
            ))}
          </div>

          <form onSubmit={submit} className="space-y-4">
            {mode === "register" && (
              <Field icon={<User className="h-4 w-4" />} label="Full name">
                <input className="input-field pl-10" placeholder="Jane Doe" value={name} onChange={(e) => setName(e.target.value)} />
              </Field>
            )}
            <Field icon={<Mail className="h-4 w-4" />} label="Email">
              <input className="input-field pl-10" type="email" required placeholder="you@company.com" value={email} onChange={(e) => setEmail(e.target.value)} />
            </Field>
            <Field icon={<Lock className="h-4 w-4" />} label="Password">
              <input className="input-field pl-10" type="password" required minLength={6} placeholder="••••••••" value={password} onChange={(e) => setPassword(e.target.value)} />
            </Field>

            {error && (
              <p className="rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-xs text-rose-700">{error}</p>
            )}

            <Button type="submit" className="w-full" loading={loading}>
              {mode === "login" ? "Sign in & load live jobs" : "Create account"}
              <ArrowRight className="h-4 w-4" />
            </Button>
          </form>

          <div className="mt-6 flex items-center gap-2 rounded-xl border border-brand-100 bg-brand-50/50 px-3 py-2.5 text-xs text-ink-600">
            <Sparkles className="h-4 w-4 shrink-0 text-brand-600" />
            After sign-in, jobs are fetched live from LinkedIn, Greenhouse & Hiring Cafe matched to your profile.
          </div>
        </div>
      </motion.div>
    </div>
  );
}

function Field({ icon, label, children }: { icon: React.ReactNode; label: string; children: React.ReactNode }) {
  return (
    <div>
      <label className="section-label mb-1.5 block">{label}</label>
      <div className="relative">{children}<span className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-ink-400">{icon}</span></div>
    </div>
  );
}

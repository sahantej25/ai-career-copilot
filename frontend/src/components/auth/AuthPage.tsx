import { useState } from "react";
import { motion } from "framer-motion";
import { GoogleLogin } from "@react-oauth/google";
import { Brain, Mail, Lock, User, Sparkles, ArrowRight, ShieldCheck } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { useAuthStore } from "@/hooks/useAuthStore";
import { cn } from "@/lib/utils";

type Mode = "login" | "register";

const GOOGLE_ENABLED = Boolean(import.meta.env.VITE_GOOGLE_CLIENT_ID);

export function AuthPage() {
  const { login, register, loginWithGoogle } = useAuthStore();
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

  const handleGoogleSuccess = async (credential?: string) => {
    if (!credential) {
      setError("Google sign-in did not return a credential.");
      return;
    }
    setError("");
    setLoading(true);
    try {
      await loginWithGoogle(credential);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Google sign-in failed");
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
            Sign in with Google or create your account to access live jobs and professional application tracking.
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

          {GOOGLE_ENABLED ? (
            <div className="mb-6 space-y-4">
              <div className="flex justify-center [&>div]:w-full">
                <GoogleLogin
                  onSuccess={(res) => handleGoogleSuccess(res.credential)}
                  onError={() => setError("Google sign-in was cancelled or failed.")}
                  theme="outline"
                  size="large"
                  width="360"
                  text={mode === "login" ? "signin_with" : "signup_with"}
                  shape="rectangular"
                />
              </div>
              <div className="relative">
                <div className="absolute inset-0 flex items-center">
                  <div className="w-full border-t border-slate-200" />
                </div>
                <div className="relative flex justify-center text-xs uppercase">
                  <span className="bg-white/80 px-3 text-ink-400">or continue with email</span>
                </div>
              </div>
            </div>
          ) : (
            <div className="mb-5 rounded-xl border border-amber-200 bg-amber-50/80 px-3 py-2.5 text-xs text-amber-800">
              Google sign-in: set <code className="font-mono">VITE_GOOGLE_CLIENT_ID</code> in{" "}
              <code className="font-mono">frontend/.env</code> to enable one-click Gmail login.
            </div>
          )}

          <form onSubmit={submit} className="space-y-4">
            {mode === "register" && (
              <Field icon={<User className="h-4 w-4" />} label="Full name">
                <input
                  className="input-field pl-10"
                  placeholder="Jane Doe"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                />
              </Field>
            )}
            <Field icon={<Mail className="h-4 w-4" />} label="Email">
              <input
                className="input-field pl-10"
                type="email"
                required
                placeholder="you@gmail.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </Field>
            <Field icon={<Lock className="h-4 w-4" />} label="Password">
              <input
                className="input-field pl-10"
                type="password"
                required
                minLength={6}
                placeholder="At least 6 characters"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </Field>

            {error && (
              <p className="rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-xs text-rose-700">
                {error}
              </p>
            )}

            <Button type="submit" className="w-full" loading={loading}>
              {mode === "login" ? "Sign in with email" : "Create account with email"}
              <ArrowRight className="h-4 w-4" />
            </Button>
          </form>

          <div className="mt-6 space-y-2">
            <div className="flex items-center gap-2 rounded-xl border border-brand-100 bg-brand-50/50 px-3 py-2.5 text-xs text-ink-600">
              <Sparkles className="h-4 w-4 shrink-0 text-brand-600" />
              After sign-in, jobs are fetched live from LinkedIn, Greenhouse & Hiring Cafe.
            </div>
            <div className="flex items-center gap-2 rounded-xl border border-slate-200/80 bg-white/50 px-3 py-2.5 text-xs text-ink-500">
              <ShieldCheck className="h-4 w-4 shrink-0 text-emerald-600" />
              Your data is private per account — profile, applications, and preferences are isolated.
            </div>
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
      <div className="relative">
        {children}
        <span className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-ink-400">{icon}</span>
      </div>
    </div>
  );
}

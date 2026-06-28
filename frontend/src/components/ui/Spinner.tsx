import { cn } from "@/lib/utils";
import { motion } from "framer-motion";
import { Brain } from "lucide-react";

interface SpinnerProps {
  size?: "sm" | "md" | "lg";
  className?: string;
  label?: string;
}

const sizes = { sm: "h-4 w-4", md: "h-8 w-8", lg: "h-12 w-12" };

export function Spinner({ size = "md", className, label }: SpinnerProps) {
  return (
    <div className={cn("flex flex-col items-center gap-3", className)}>
      <svg className={cn("animate-spin text-brand-400", sizes[size])} fill="none" viewBox="0 0 24 24">
        <circle className="opacity-20" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
        <path className="opacity-80" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
      </svg>
      {label && <p className="text-sm text-ink-500 animate-pulse">{label}</p>}
    </div>
  );
}

export function AIThinkingAnimation({ label = "AI is analyzing..." }: { label?: string }) {
  return (
    <div className="flex flex-col items-center gap-5 py-10">
      <div className="relative w-20 h-20">
        {/* Pulsing aura rings */}
        <motion.div
          className="absolute inset-0 rounded-full border border-brand-500/50"
          animate={{ scale: [1, 1.5, 1], opacity: [0.6, 0, 0.6] }}
          transition={{ duration: 2.4, repeat: Infinity, ease: "easeOut" }}
        />
        <motion.div
          className="absolute inset-2 rounded-full border border-teal-500/50"
          animate={{ scale: [1, 1.4, 1], opacity: [0.8, 0, 0.8] }}
          transition={{ duration: 2.4, repeat: Infinity, delay: 0.4, ease: "easeOut" }}
        />
        {/* Orbiting dot */}
        <motion.div
          className="absolute inset-0"
          animate={{ rotate: 360 }}
          transition={{ duration: 3, repeat: Infinity, ease: "linear" }}
        >
          <span className="absolute left-1/2 -top-0.5 -translate-x-1/2 w-2 h-2 rounded-full bg-sky-400 shadow-[0_0_12px_2px_rgba(56,189,248,0.7)]" />
        </motion.div>
        {/* Core */}
        <motion.div
          className="absolute inset-5 rounded-2xl bg-gradient-to-br from-brand-500 to-teal-600 flex items-center justify-center shadow-glow"
          animate={{ scale: [1, 1.08, 1] }}
          transition={{ duration: 1.8, repeat: Infinity, ease: "easeInOut" }}
        >
          <Brain className="w-5 h-5 text-white" />
        </motion.div>
      </div>
      <div className="flex gap-1.5">
        {[0, 1, 2].map((i) => (
          <motion.div
            key={i}
            className="w-2 h-2 rounded-full bg-gradient-to-br from-brand-400 to-teal-400"
            animate={{ y: [0, -9, 0], opacity: [0.4, 1, 0.4] }}
            transition={{ duration: 0.9, repeat: Infinity, delay: i * 0.18, ease: "easeInOut" }}
          />
        ))}
      </div>
      <p className="text-sm text-ink-500">{label}</p>
    </div>
  );
}

import { motion, AnimatePresence } from "framer-motion";
import { CheckCircle, XCircle, Info, X, Loader2 } from "lucide-react";
import { useAppStore } from "@/hooks/useAppStore";
import { cn } from "@/lib/utils";

const icons = {
  success: <CheckCircle className="w-4 h-4 text-emerald-500" />,
  error: <XCircle className="w-4 h-4 text-rose-500" />,
  info: <Info className="w-4 h-4 text-sky-500" />,
  loading: <Loader2 className="w-4 h-4 text-brand-500 animate-spin" />,
};

const accents = {
  success: "before:bg-emerald-500",
  error: "before:bg-rose-500",
  info: "before:bg-sky-500",
  loading: "before:bg-brand-500",
};

export function ToastContainer() {
  const { toasts, removeToast } = useAppStore();

  return (
    <div className="fixed bottom-6 right-6 z-[60] flex flex-col gap-2.5 pointer-events-none">
      <AnimatePresence>
        {toasts.map((toast) => (
          <motion.div
            key={toast.id}
            layout
            initial={{ opacity: 0, x: 40, scale: 0.92 }}
            animate={{ opacity: 1, x: 0, scale: 1 }}
            exit={{ opacity: 0, x: 40, scale: 0.92 }}
            transition={{ type: "spring", stiffness: 320, damping: 26 }}
            className={cn(
              "pointer-events-auto relative flex items-center gap-3 pl-5 pr-3 py-3.5 rounded-2xl overflow-hidden",
              "glass glass-edge shadow-glass-lg max-w-sm min-w-[300px]",
              "before:absolute before:left-0 before:top-0 before:bottom-0 before:w-1 before:rounded-r-full",
              accents[toast.type]
            )}
          >
            {icons[toast.type]}
            <span className="text-sm text-ink-700 flex-1 leading-snug">{toast.message}</span>
            <button
              onClick={() => removeToast(toast.id)}
              className="text-ink-400 hover:text-ink-700 transition-colors p-1 rounded-lg hover:bg-slate-100 cursor-pointer"
              aria-label="Dismiss notification"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          </motion.div>
        ))}
      </AnimatePresence>
    </div>
  );
}

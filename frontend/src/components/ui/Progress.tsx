import { HTMLAttributes, useEffect, useState } from "react";
import { cn, getMatchBg } from "@/lib/utils";
import { motion, useMotionValue, useTransform, animate } from "framer-motion";

interface ProgressProps extends HTMLAttributes<HTMLDivElement> {
  value: number;
  showLabel?: boolean;
  colorByValue?: boolean;
  color?: string;
  size?: "sm" | "md" | "lg";
}

const sizeMap = { sm: "h-1.5", md: "h-2.5", lg: "h-3.5" };

export function Progress({
  value,
  showLabel = false,
  colorByValue = false,
  color,
  size = "md",
  className,
  ...props
}: ProgressProps) {
  const barColor = color
    ? color
    : colorByValue
    ? getMatchBg(value)
    : "bg-gradient-to-r from-brand-500 via-teal-500 to-sky-400";

  return (
    <div className={cn("w-full", className)} {...props}>
      <div className={cn("relative w-full bg-slate-200/70 rounded-full overflow-hidden", sizeMap[size])}>
        <motion.div
          className={cn("relative h-full rounded-full", barColor)}
          initial={{ width: 0 }}
          animate={{ width: `${Math.min(100, Math.max(0, value))}%` }}
          transition={{ duration: 1.1, ease: [0.16, 1, 0.3, 1] }}
        >
          {/* moving sheen */}
          <span className="absolute inset-0 bg-gradient-to-r from-transparent via-white/30 to-transparent bg-[length:200%_100%] animate-shimmer rounded-full" />
        </motion.div>
      </div>
      {showLabel && (
        <span className="text-xs text-ink-500 mt-1 block text-right tabular-nums">
          {value.toFixed(0)}%
        </span>
      )}
    </div>
  );
}

interface AnimatedCounterProps {
  value: number;
  suffix?: string;
  className?: string;
  duration?: number;
}

export function AnimatedCounter({
  value,
  suffix = "",
  className,
  duration = 1.4,
}: AnimatedCounterProps) {
  const count = useMotionValue(0);
  const rounded = useTransform(count, (latest) => Math.round(latest).toString());
  const [display, setDisplay] = useState("0");

  useEffect(() => {
    const controls = animate(count, value, {
      duration,
      ease: [0.16, 1, 0.3, 1],
    });
    const unsub = rounded.on("change", (v) => setDisplay(v));
    return () => {
      controls.stop();
      unsub();
    };
  }, [value, duration, count, rounded]);

  return (
    <span className={cn("tabular-nums", className)}>
      {display}
      {suffix}
    </span>
  );
}

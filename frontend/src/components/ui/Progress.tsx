import { HTMLAttributes } from "react";
import { cn, getMatchBg } from "@/lib/utils";
import { motion } from "framer-motion";

interface ProgressProps extends HTMLAttributes<HTMLDivElement> {
  value: number;
  showLabel?: boolean;
  colorByValue?: boolean;
  color?: string;
  size?: "sm" | "md" | "lg";
}

const sizeMap = { sm: "h-1.5", md: "h-2.5", lg: "h-4" };

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
    : "bg-gradient-to-r from-indigo-500 to-purple-500";

  return (
    <div className={cn("w-full", className)} {...props}>
      <div
        className={cn(
          "w-full bg-slate-800/80 rounded-full overflow-hidden",
          sizeMap[size]
        )}
      >
        <motion.div
          className={cn("h-full rounded-full", barColor)}
          initial={{ width: 0 }}
          animate={{ width: `${Math.min(100, Math.max(0, value))}%` }}
          transition={{ duration: 1, ease: "easeOut" }}
        />
      </div>
      {showLabel && (
        <span className="text-xs text-slate-400 mt-1 block text-right">
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
}: AnimatedCounterProps) {
  return (
    <motion.span
      className={className}
      initial={{ opacity: 0, scale: 0.5 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ type: "spring", stiffness: 200, damping: 15 }}
    >
      <motion.span
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        key={value}
      >
        {value.toFixed(0)}
      </motion.span>
      {suffix}
    </motion.span>
  );
}

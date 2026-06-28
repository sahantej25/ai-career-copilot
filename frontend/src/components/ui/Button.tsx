import { forwardRef, ButtonHTMLAttributes } from "react";
import { cn } from "@/lib/utils";

type Variant = "primary" | "secondary" | "ghost" | "danger" | "outline";
type Size = "sm" | "md" | "lg" | "icon";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  size?: Size;
  loading?: boolean;
}

const variantStyles: Record<Variant, string> = {
  primary:
    "text-white bg-gradient-to-br from-brand-500 to-teal-600 shadow-glow hover:shadow-glow-lg hover:-translate-y-0.5",
  secondary:
    "text-ink-700 bg-white/70 border border-slate-200 hover:bg-white hover:border-slate-300 shadow-soft",
  ghost: "text-ink-600 hover:bg-slate-100 hover:text-ink-800",
  danger:
    "text-rose-600 bg-rose-50 border border-rose-200 hover:bg-rose-100 hover:border-rose-300",
  outline:
    "text-brand-700 border border-brand-300 bg-brand-50/60 hover:bg-brand-100 hover:border-brand-400",
};

const sizeStyles: Record<Size, string> = {
  sm: "px-3 py-1.5 text-xs rounded-lg gap-1.5",
  md: "px-5 py-2.5 text-sm rounded-xl gap-2",
  lg: "px-6 py-3 text-base rounded-xl gap-2.5",
  icon: "p-2.5 rounded-xl",
};

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      className,
      variant = "primary",
      size = "md",
      loading = false,
      disabled,
      children,
      ...props
    },
    ref
  ) => {
    return (
      <button
        ref={ref}
        disabled={disabled || loading}
        className={cn(
          "group/btn relative inline-flex items-center justify-center overflow-hidden font-semibold tracking-tight",
          "transition-all duration-200 ease-out-expo cursor-pointer select-none",
          "disabled:opacity-50 disabled:cursor-not-allowed disabled:translate-y-0 disabled:shadow-none",
          variantStyles[variant],
          sizeStyles[size],
          className
        )}
        {...props}
      >
        {/* Specular shine sweep on hover for the primary CTA */}
        {variant === "primary" && (
          <span className="pointer-events-none absolute inset-0 -translate-x-full bg-gradient-to-r from-transparent via-white/25 to-transparent transition-transform duration-700 ease-out group-hover/btn:translate-x-full" />
        )}
        {loading && (
          <svg className="animate-spin h-4 w-4 relative z-10" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
        )}
        <span className="relative z-10 inline-flex items-center gap-2">{children}</span>
      </button>
    );
  }
);
Button.displayName = "Button";

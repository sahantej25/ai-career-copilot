import { HTMLAttributes, forwardRef } from "react";
import { cn } from "@/lib/utils";

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  interactive?: boolean;
  glow?: boolean;
}

export const Card = forwardRef<HTMLDivElement, CardProps>(
  ({ className, interactive = false, glow = false, ...props }, ref) => (
    <div
      ref={ref}
      className={cn(
        "glass glass-edge p-5 sm:p-6",
        interactive && "glass-hover hover:-translate-y-0.5",
        glow && "shadow-glow",
        className
      )}
      {...props}
    />
  )
);
Card.displayName = "Card";

export const CardHeader = forwardRef<HTMLDivElement, HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div ref={ref} className={cn("mb-5", className)} {...props} />
  )
);
CardHeader.displayName = "CardHeader";

export const CardTitle = forwardRef<HTMLHeadingElement, HTMLAttributes<HTMLHeadingElement>>(
  ({ className, ...props }, ref) => (
    <h3
      ref={ref}
      className={cn("font-display text-lg font-semibold tracking-tight text-ink-900", className)}
      {...props}
    />
  )
);
CardTitle.displayName = "CardTitle";

export const CardContent = forwardRef<HTMLDivElement, HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div ref={ref} className={cn("", className)} {...props} />
  )
);
CardContent.displayName = "CardContent";

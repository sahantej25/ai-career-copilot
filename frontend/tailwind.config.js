/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        // Brand — fresh emerald/teal (career growth), the confident primary accent
        brand: {
          50: "#ecfdf5",
          100: "#d1fae5",
          200: "#a7f3d0",
          300: "#6ee7b7",
          400: "#34d399",
          500: "#10b981",
          600: "#059669",
          700: "#047857",
          800: "#065f46",
          900: "#064e3b",
          950: "#022c22",
        },
        teal: {
          400: "#2dd4bf",
          500: "#14b8a6",
          600: "#0d9488",
        },
        // Soft canvas neutrals
        canvas: {
          DEFAULT: "#f6f7f9",
          soft: "#fbfcfd",
          muted: "#eef1f5",
        },
        ink: {
          900: "#0b1220",
          800: "#0f172a",
          700: "#1e293b",
          600: "#334155",
          500: "#64748b",
          400: "#94a3b8",
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        display: ["Space Grotesk", "Inter", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "Fira Code", "monospace"],
      },
      letterSpacing: {
        tightest: "-0.04em",
      },
      borderRadius: {
        "4xl": "2rem",
      },
      boxShadow: {
        glass:
          "0 1px 0 0 rgba(255,255,255,0.9) inset, 0 10px 30px -12px rgba(2,6,23,0.12), 0 2px 6px -2px rgba(2,6,23,0.06)",
        "glass-lg":
          "0 1px 0 0 rgba(255,255,255,0.95) inset, 0 24px 60px -18px rgba(2,6,23,0.2), 0 8px 20px -8px rgba(2,6,23,0.1)",
        soft: "0 4px 18px -6px rgba(2,6,23,0.1)",
        glow: "0 8px 28px -8px rgba(16,185,129,0.5)",
        "glow-lg": "0 16px 44px -10px rgba(16,185,129,0.55)",
      },
      animation: {
        "pulse-slow": "pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        "spin-slow": "spin 3s linear infinite",
        "fade-in": "fadeIn 0.5s ease-out",
        "slide-up": "slideUp 0.5s cubic-bezier(0.16,1,0.3,1)",
        "aurora-drift": "auroraDrift 24s ease-in-out infinite",
        "aurora-drift-slow": "auroraDrift 36s ease-in-out infinite",
        shimmer: "shimmer 2.4s linear infinite",
        float: "float 8s ease-in-out infinite",
        "blink-dot": "blinkDot 1.4s ease-in-out infinite",
      },
      keyframes: {
        fadeIn: { "0%": { opacity: "0" }, "100%": { opacity: "1" } },
        slideUp: {
          "0%": { opacity: "0", transform: "translateY(24px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        auroraDrift: {
          "0%, 100%": { transform: "translate3d(0,0,0) scale(1)" },
          "33%": { transform: "translate3d(5%,-4%,0) scale(1.1)" },
          "66%": { transform: "translate3d(-4%,4%,0) scale(0.96)" },
        },
        shimmer: {
          "0%": { backgroundPosition: "-200% 0" },
          "100%": { backgroundPosition: "200% 0" },
        },
        float: {
          "0%, 100%": { transform: "translateY(0)" },
          "50%": { transform: "translateY(-10px)" },
        },
        blinkDot: {
          "0%, 100%": { opacity: "1", transform: "scale(1)" },
          "50%": { opacity: "0.35", transform: "scale(0.85)" },
        },
      },
      transitionTimingFunction: {
        "out-expo": "cubic-bezier(0.16, 1, 0.3, 1)",
      },
    },
  },
  plugins: [],
};

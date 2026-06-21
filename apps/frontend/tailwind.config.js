/** @type {import('tailwindcss').Config} */
// Token values mirror apps/frontend/data/style.md exactly (the Pactum design
// system). The actual CSS values live as variables in src/index.css :root so
// they stay a single source of truth; here we just expose them as utilities.
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        bg: "var(--bg)",
        surface: { DEFAULT: "var(--surface)", 2: "var(--surface-2)" },
        border: { DEFAULT: "var(--border)", strong: "var(--border-strong)" },
        "text-1": "var(--text-1)",
        "text-2": "var(--text-2)",
        "text-3": "var(--text-3)",
        accent: {
          DEFAULT: "var(--accent)",
          soft: "var(--accent-soft)",
          border: "var(--accent-border)",
        },
        success: { DEFAULT: "var(--success)", soft: "var(--success-soft)" },
        warning: { DEFAULT: "var(--warning)", soft: "var(--warning-soft)" },
        danger: { DEFAULT: "var(--danger)", soft: "var(--danger-soft)" },
        info: "var(--info)",
      },
      boxShadow: {
        sm: "var(--shadow-sm)",
        md: "var(--shadow-md)",
        tinted: "var(--shadow-tinted)",
        accent: "var(--shadow-accent)",
      },
      fontFamily: {
        sans: ["Geist", "Inter", "ui-sans-serif", "system-ui", "sans-serif"],
        mono: ["Geist Mono", "ui-monospace", "SFMono-Regular", "monospace"],
      },
      transitionTimingFunction: {
        "out-strong": "var(--ease-out-strong)",
        "in-out-strong": "var(--ease-in-out-strong)",
      },
    },
  },
  plugins: [],
};

export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        bg: "#F5F7FB",
        surface: "#FFFFFF",
        "surface-hover": "#F3F4F6",

        border: "#E5E7EB",
        "border-accent": "#CBD5E1",

        amber: "#F59E0B",
        "amber-dim": "#FEF3C7",

        danger: "#EF4444",
        "danger-dim": "#FEE2E2",

        success: "#10B981",
        "success-dim": "#D1FAE5",

        info: "#3B82F6",
        "info-dim": "#DBEAFE",

        "text-primary": "#111827",
        "text-secondary": "#4B5563",
        "text-dim": "#9CA3AF",
      },

      fontFamily: {
        display: ["Syne", "sans-serif"],
        mono: ["JetBrains Mono", "monospace"],
        sans: ["Plus Jakarta Sans", "sans-serif"],
      },
    },
  },
  plugins: [],
};
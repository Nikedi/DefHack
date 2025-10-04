/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./index.html", "./src/**/*.{ts,tsx,js,jsx}"],
  theme: {
    extend: {
      colors: {
        mil: {
          dark: "#0f140f",
          olive: "#34402b",
          olive2: "#3f5a36",
          sand: "#cbb890",
          accent: "#c59a45",
          alert: "#b03b2b",
          muted: "#879070",
        },
      },
      fontFamily: {
        mono: ["'Share Tech Mono'", "Roboto Mono", "ui-monospace", "SFMono-Regular", "monospace"],
        tactical: ["'Share Tech Mono'", "Roboto", "sans-serif"],
      },
      borderRadius: {
        sm: "6px",
        md: "8px",
      },
      boxShadow: {
        mil: "0 6px 18px rgba(0,0,0,0.6), inset 0 1px 0 rgba(255,255,255,0.02)",
      },
    },
  },
  plugins: [],
};
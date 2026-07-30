import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{ts,tsx}"],
  darkMode: ["class", '[data-theme="dark"]'],
  theme: {
    extend: {
      colors: {
        ink: "#17140F",
        paper: "#E7EAE2",
        "paper-raised": "#DEE2D8",
        brass: "#8A6526",
        "brass-dark": "#D2A34F",
        verdigris: "#375B50",
        "verdigris-dark": "#6FA091",
        rubrication: "#7C2A2A",
        hairline: "rgba(23,20,15,0.20)",
      },
      fontFamily: {
        display: ["Fraunces", "Georgia", "serif"],
        sans: ["Archivo", "system-ui", "sans-serif"],
        "display-ar": ["Amiri", "serif"],
        "sans-ar": ["Cairo", "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
};

export default config;

import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        background: "var(--background)",
        foreground: "var(--foreground)",
        "soft-blue": "#dbe4ff",
        "soft-blue-dark": "#1e293b",
        "main-bg": "#f4f7fe",
        "card-bg": "#ffffff",
        "dark-bg": "#0b1120",
        "dark-card": "#171e2c",
        accent: {
          primary: "#4318FF",
          secondary: "#6AD2FF",
        },
        neon: {
          cyan: "#00f3ff",
          blue: "#0070f3",
        },
        signal: {
          green: "#05cd99",
          red: "#ee5d50",
          yellow: "#ffb547"
        },
      },
      borderRadius: {
        '3xl': '24px',
        '4xl': '32px',
      },
      boxShadow: {
        'soft': '0px 18px 40px rgba(112, 144, 176, 0.12)',
        'soft-dark': '0px 18px 40px rgba(0, 0, 0, 0.4)',
      },
      fontFamily: {
        sans: ["var(--font-inter)"],
        mono: ["var(--font-jetbrains-mono)"],
      }
    },
  },
  plugins: [],
};
export default config;

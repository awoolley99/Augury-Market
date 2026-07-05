/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: {
          950: "#0B0E14",
          900: "#11151E",
          800: "#181D29",
          700: "#232939",
        },
        parchment: "#EDE6D6",
        signal: {
          DEFAULT: "#E8A33D",
          dim: "#B88130",
        },
        rise: "#5B8C6E",
        fall: "#B8503E",
        hush: "#8A8F9C",
      },
      fontFamily: {
        display: ["Iowan Old Style", "Georgia", "Palatino Linotype", "serif"],
        body: ["-apple-system", "BlinkMacSystemFont", "Segoe UI", "sans-serif"],
        mono: ["ui-monospace", "SFMono-Regular", "Menlo", "monospace"],
      },
    },
  },
  plugins: [],
};

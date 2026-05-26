/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        tnt: { navy: "#0f172a", accent: "#f59e0b", danger: "#dc2626" },
      },
    },
  },
  plugins: [],
};

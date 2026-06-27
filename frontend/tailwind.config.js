/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'deep-space': '#030305',
        'panel-bg': '#09090e',
        'neon-purple': '#bc13fe',
        'ok-green': '#22c55e',
        'critical-pink': '#ff007f',
        'text-bright': '#e4e4e7',
        'text-dim': '#a1a1aa',
      }
    },
  },
  plugins: [],
}
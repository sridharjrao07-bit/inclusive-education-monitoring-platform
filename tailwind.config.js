/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // India Blue — Ashoka Chakra inspired
        india: {
          50:  '#eef4ff',
          100: '#d9e5ff',
          200: '#bcd0ff',
          300: '#8eb2ff',
          400: '#5985ff',
          500: '#2b4acb',   // Primary button / active states
          600: '#1e3a8a',   // Darker accent
          700: '#1a2f6b',
          800: '#162556',
          900: '#0f1b3d',
          950: '#0a1128',
        },
        // Saffron — status highlights (warm)
        saffron: {
          50:  '#fff8ed',
          100: '#fff0d4',
          200: '#ffdda8',
          300: '#ffc370',
          400: '#ff9f37',
          500: '#f97f10',
          600: '#ea6506',
          700: '#c24b07',
          800: '#9a3b0e',
          900: '#7c320f',
        },
        // India Green — status / success
        neem: {
          50:  '#f0fdf5',
          100: '#dcfce8',
          200: '#bbf7d1',
          300: '#86efac',
          400: '#4ade80',
          500: '#138808',   // Indian flag green
          600: '#117007',
          700: '#115e0a',
          800: '#12490d',
          900: '#103d0e',
        },
      },
      fontFamily: {
        sans: ['"Inter"', '"Public Sans"', 'system-ui', '-apple-system', 'sans-serif'],
      },
      boxShadow: {
        'card': '0 1px 3px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04)',
        'card-hover': '0 4px 12px rgba(0,0,0,0.08), 0 2px 4px rgba(0,0,0,0.04)',
        'modal': '0 20px 60px rgba(0,0,0,0.15), 0 8px 20px rgba(0,0,0,0.08)',
      },
    },
  },
  plugins: [],
}

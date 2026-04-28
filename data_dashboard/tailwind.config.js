/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        // BEDROT Duochromatic System (Data Ecosystem - Green Accent)
        bedrot: {
          bg: {
            0: '#0d151d',   // Deepest - shells, status bars
            1: '#121c26',   // Tool backgrounds
            2: '#172430',   // Primary panels, cards
            3: '#1c2d3d',   // Input fields, elevated
            4: '#22374a',   // Hover states
            5: '#2a4157',   // Active/pressed
          },
          accent: {
            DEFAULT: '#00ff88',
            hover: '#33ffaa',
            pressed: '#00cc6a',
            muted: 'rgba(0, 255, 136, 0.2)',
            tint: 'rgba(0, 255, 136, 0.05)',
          },
          text: {
            primary: '#e8ecf0',
            secondary: '#a8b8c4',
            muted: '#6a7a88',
          },
          border: {
            subtle: '#243344',
            DEFAULT: '#2f4155',
            hover: '#3a5166',
          },
          semantic: {
            error: '#ff4466',
            success: '#33cc66',
            warning: '#ffaa33',
          }
        },
        // Legacy primary (kept for backwards compatibility)
        primary: {
          50: '#f0f9ff',
          100: '#e0f2fe',
          200: '#bae6fd',
          300: '#7dd3fc',
          400: '#38bdf8',
          500: '#0ea5e9',
          600: '#0284c7',
          700: '#0369a1',
          800: '#075985',
          900: '#0c4a6e',
        },
        dark: {
          bg: '#0d151d',
          card: '#172430',
          border: '#2f4155',
        }
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      }
    },
  },
  plugins: [],
}

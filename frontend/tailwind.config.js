/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        govblue: {
  50: '#eef4ff',
  100: '#d9e6ff',
  300: '#93b4f5',
  600: '#1d4ed8',
  700: '#1e40af',
  800: '#1e3a8a',
  900: '#0f2557',
  950: '#0a1a3f',
               },
        risk: {
          low: '#22c55e',
          moderate: '#eab308',
          high: '#f97316',
          critical: '#dc2626',
        },
      },
      fontFamily: {
        sans: ['Inter', 'ui-sans-serif', 'system-ui', 'Segoe UI', 'Arial', 'sans-serif'],
        mono: ['JetBrains Mono', 'ui-monospace', 'SFMono-Regular', 'Menlo', 'monospace'],
      },
      boxShadow: {
        card: '0 1px 3px rgba(15, 37, 87, 0.08), 0 1px 2px rgba(15, 37, 87, 0.04)',
        cardhover: '0 12px 28px -10px rgba(15, 37, 87, 0.22), 0 2px 6px rgba(15, 37, 87, 0.06)',
        pop: '0 10px 30px -8px rgba(15, 37, 87, 0.25)',
        inner: 'inset 0 1px 2px rgba(15, 37, 87, 0.06)',
      },
      backgroundImage: {
        'hero-grid':
          'linear-gradient(rgba(255,255,255,0.05) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.05) 1px, transparent 1px)',
      },
      transitionTimingFunction: {
        smooth: 'cubic-bezier(0.22, 1, 0.36, 1)',
      },
    },
  },
  plugins: [],
};

/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        ivory: '#FAF9F5',
        cream: '#F3F1E9',
        navy: {
          DEFAULT: '#0F1E36',
          light: '#1B3156',
          dark: '#081222',
        },
        electric: {
          DEFAULT: '#FACC15',
          hover: '#EAB308',
          soft: '#FEF9C3',
        },
      },
      fontFamily: {
        sans: ['"Plus Jakarta Sans"', 'Inter', 'system-ui', 'sans-serif'],
      },
      boxShadow: {
        card: '0 4px 20px -2px rgba(15, 30, 54, 0.06)',
        elevated: '0 12px 32px -4px rgba(15, 30, 54, 0.10)',
      },
    },
  },
  plugins: [],
};

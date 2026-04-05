/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ['./src/**/*.{js,jsx,ts,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        serif: ['Cormorant Garamond', 'Georgia', 'serif'],
        sans: ['DM Sans', 'system-ui', 'sans-serif'],
      },
      colors: {
        linen: {
          50: '#FDFCFA',
          100: '#F8F5F0',
          200: '#EDE9E3',
          300: '#DDD8D0',
          400: '#C8C2B8',
        },
        rouge: {
          300: '#D4908A',
          500: '#B85450',
          700: '#8B2E2B',
        },
        bronze: {
          300: '#D4BC9A',
          400: '#B89A78',
          500: '#8B7355',
          600: '#745E43',
          700: '#5E4C35',
        },
        ink: {
          900: '#1A1714',
          800: '#2C2925',
          700: '#3E3B37',
          600: '#524F4A',
          500: '#6B6760',
          400: '#8A8680',
          300: '#A8A49E',
          200: '#C4C0BB',
          100: '#DEDAD5',
        },
      },
      keyframes: {
        'fade-up': {
          '0%': { opacity: '0', transform: 'translateY(8px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        'slide-in': {
          '0%': { opacity: '0', transform: 'translateX(12px)' },
          '100%': { opacity: '1', transform: 'translateX(0)' },
        },
      },
      animation: {
        'fade-up': 'fade-up 0.3s ease-out forwards',
        'slide-in': 'slide-in 0.25s ease-out forwards',
      },
      typography: {
        DEFAULT: {
          css: {
            color: '#2C2925',
            fontFamily: "'DM Sans', system-ui, sans-serif",
            fontSize: '0.875rem',
            lineHeight: '1.6',
            'h1, h2, h3, h4': { fontFamily: "'DM Sans', system-ui, sans-serif", color: '#1A1714', fontWeight: '600' },
            strong: { color: '#1A1714' },
            'ul, ol': { paddingLeft: '1.25rem' },
            hr: { borderColor: '#EDE9E3' },
            a: { color: '#8B7355' },
            'p:first-child': { marginTop: '0' },
            'p:last-child': { marginBottom: '0' },
          },
        },
      },
    },
  },
  plugins: [require('@tailwindcss/typography')],
};

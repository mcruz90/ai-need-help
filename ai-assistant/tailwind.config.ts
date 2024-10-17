import type { Config } from 'tailwindcss';
import typography from '@tailwindcss/typography';



const config: Config = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    './utils/**/*.{js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      backgroundImage: {
        "gradient-radial": "radial-gradient(var(--tw-gradient-stops))",
        "gradient-conic":
          "conic-gradient(from 180deg at 50% 50%, var(--tw-gradient-stops))",
      },
      fontFamily: {
        sans: ['Manrope', 'sans-serif'],
      'manrope-bold': ['Manrope-Bold', 'sans-serif'],
      },
      colors: {
        'text': 'var(--text)',
        'background': 'var(--background)',
        'primary': 'var(--primary)',
        'secondary': 'var(--secondary)',
        'accent': 'var(--accent)',
        'button-brand-green': '#3ED598',
        'button-brand-green-dark': '#34B1AA',
        'button-brand-red': '#FF565E',
        'button-brand-red-dark': '#E04F57',
        'button-brand-yellow': '#FFC542',
        'button-brand-yellow-dark': '#E0AC42',
        'button-brand-neutral': '#96A7AF',
        'button-brand-neutral-dark': '#78848D',
        
       },
       
    },
  },
  plugins: [typography()],
};

export default config;

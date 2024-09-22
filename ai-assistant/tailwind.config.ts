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
        sans: ['Suse', 'sans-serif'],
      'suse-bold': ['Suse-Bold', 'sans-serif'],
      },
      colors: {
        'text': 'var(--text)',
        'background': 'var(--background)',
        'primary': 'var(--primary)',
        'secondary': 'var(--secondary)',
        'accent': 'var(--accent)',
        'chat-blue': '#3B8FF3',
        'chat-blue-dark': '#2A66B1',
        'chat-green': '#34B1AA',
        'chat-green-dark': '#2A8E87',
        'brand-orange': '#F29F67',
        'brand-orange-dark': '#E08A4F'
       },
       
    },
  },
  plugins: [typography()],
};

export default config;

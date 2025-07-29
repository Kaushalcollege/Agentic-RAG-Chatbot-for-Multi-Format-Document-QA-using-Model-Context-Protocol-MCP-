/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}", // This is crucial: it tells Tailwind where to find your React components
  ],
  theme: {
    extend: {},
  },
  plugins: [],
};

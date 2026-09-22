/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        app: {
          bg: "#F7FAF8",
        },
      },
    },
  },
  plugins: [],
};

/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        bndes: {
          blue: {
            DEFAULT: '#002B49',
            light: '#004A80',
            dark: '#001A2C',
          },
          green: {
            DEFAULT: '#008542',
            light: '#00A854',
            dark: '#005E2E',
          },
          gold: '#C49A45',
        },
      },
    },
  },
  plugins: [],
}

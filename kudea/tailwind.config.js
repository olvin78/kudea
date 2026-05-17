/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./templates/**/*.html",
    "./applications/**/*.py",
    "./static/**/*.js",
  ],
  theme: {
    extend: {
      colors: {
        'primary-blue': '#457B9D',
        'dark-blue': '#1D3557',
        'light-blue': '#A8DADC',
        'accent-green': '#F1FAEE',
        'soft-bg': '#f8fafc',
      },
      borderRadius: {
        '2xl': '1rem',
        '3xl': '1.5rem',
      }
    },
  },
  plugins: [],
}

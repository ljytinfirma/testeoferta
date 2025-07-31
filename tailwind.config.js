/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./templates/**/*.html",
    "./static/**/*.js",
    "./**/*.py"
  ],
  theme: {
    extend: {
      colors: {
        'encceja-blue': '#1e40af',
        'encceja-gray': '#6b7280',
        'receita-green': '#065f46',
        'pix-orange': '#fb923c'
      },
      fontFamily: {
        'caixa-bold': ['CAIXAStd-Bold', 'sans-serif'],
        'caixa-book': ['CAIXAStd-Book', 'sans-serif'],
        'caixa-semibold': ['CAIXAStd-SemiBold', 'sans-serif']
      },
      backgroundImage: {
        'gradient-encceja': 'linear-gradient(135deg, #1e40af 0%, #3b82f6 100%)',
      }
    },
  },
  plugins: [
    require('@tailwindcss/forms'),
  ],
}
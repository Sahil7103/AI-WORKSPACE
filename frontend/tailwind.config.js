export default {
  content: [
    "./index.html",
    "./src/**/*.{js,jsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: '#18181b', // Very dark map bg for main
        surface: '#27272a',    // Lighter surface for sidebars/cards
        surfaceHover: '#3f3f46',
        border: '#3f3f46',
        
        primaryText: '#f4f4f5', // Off-white text
        mutedText: '#a1a1aa',
        accent: '#ea580c', // Soft peach/orange
        accentHover: '#c2410c',
        
        buttonBg: '#27272a',
        buttonHover: '#3f3f46',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
      spacing: {
        '4.5': '1.125rem',
        '5.5': '1.375rem',
      },
      borderRadius: {
        'sm': '0.375rem',
        'base': '0.5rem',
        'md': '0.75rem',
        'lg': '1rem',
        'xl': '1.25rem',
        '2xl': '1.5rem',
        '3xl': '1.875rem',
        '4xl': '2rem', // for the large composer input
      },
    },
  },
  plugins: [],
}

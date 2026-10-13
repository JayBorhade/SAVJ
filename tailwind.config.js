/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        savj: {
          forest: '#123B28',
          moss: '#1E5F4E',
          leaf: '#3B8F63',
          grass: '#9AD29D',
          cream: '#F5F3EA',
          sand: '#E8E0C9',
          mist: '#ECF7F0',
          ember: '#EAAE5C',
          coral: '#EC8D72',
          charcoal: '#1E2A26'
        }
      },
      boxShadow: {
        card: '0 12px 30px rgba(18, 59, 40, 0.10)',
        soft: '0 10px 25px rgba(17, 57, 44, 0.08)'
      },
      fontFamily: {
        sans: ['Inter', 'ui-sans-serif', 'system-ui', 'sans-serif']
      }
    }
  },
  plugins: []
};

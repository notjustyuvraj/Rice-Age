/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: { extend: {
    colors: {
      ink: '#17251f', forest: '#234b3c', leaf: '#5c846d', sage: '#e8efe9', rice: '#f7f7f2',
      cream: '#fbfaf6', line: '#e6e9e3', muted: '#758078', amber: '#c48b36', danger: '#b94d48'
    },
    boxShadow: { soft: '0 8px 28px rgba(29, 53, 41, .06)' },
    fontFamily: { sans: ['Inter', 'ui-sans-serif', 'system-ui', 'sans-serif'] }
  } },
  plugins: [],
};

import type { Config } from 'tailwindcss'

export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        cloth: {
          bg: '#f4efe6',
          panel: '#f8f3eb',
          panelStrong: '#efe7dc',
          line: '#d8ccbc',
          ink: '#2f241c',
          muted: '#6f6256',
          accent: '#8a5a44',
          accentSoft: '#c89777',
          success: '#4c7351',
          warn: '#8b6a2d',
          danger: '#9a4d43'
        }
      },
      fontFamily: {
        sans: ['Inter', 'ui-sans-serif', 'system-ui', 'sans-serif'],
        serif: ['"Noto Serif SC"', 'Georgia', 'serif']
      },
      boxShadow: {
        fabric: '0 8px 30px rgba(63, 46, 35, 0.10), inset 0 1px 0 rgba(255,255,255,0.45)',
        panel: '0 6px 18px rgba(72, 53, 39, 0.08)',
      },
      backgroundImage: {
        weave: 'radial-gradient(circle at 1px 1px, rgba(106, 78, 59, 0.08) 1px, transparent 0), linear-gradient(135deg, rgba(255,255,255,0.25), rgba(126,100,79,0.04))',
        grain: 'repeating-linear-gradient(0deg, rgba(255,255,255,0.08), rgba(255,255,255,0.08) 1px, transparent 1px, transparent 3px), repeating-linear-gradient(90deg, rgba(91,66,50,0.03), rgba(91,66,50,0.03) 1px, transparent 1px, transparent 4px)'
      },
      backgroundSize: {
        weave: '12px 12px, auto',
      },
      borderRadius: {
        xl2: '1.25rem'
      }
    },
  },
  plugins: [],
} satisfies Config

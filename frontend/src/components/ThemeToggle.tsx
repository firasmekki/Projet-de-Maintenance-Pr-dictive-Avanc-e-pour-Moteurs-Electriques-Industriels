import { Sun, Moon } from 'lucide-react'
import { useTheme } from '../hooks/useTheme'

export default function ThemeToggle() {
  const { isDark, toggle } = useTheme()

  return (
    <button
      onClick={toggle}
      title={isDark ? 'Passer en mode clair' : 'Passer en mode sombre'}
      className="relative w-12 h-6 rounded-full transition-colors duration-300 focus:outline-none
                 bg-slate-600 dark:bg-slate-600 hover:bg-slate-500 dark:hover:bg-slate-500
                 border border-slate-500 dark:border-slate-500"
    >
      <span
        className={`absolute top-0.5 left-0.5 w-5 h-5 rounded-full
                    flex items-center justify-center transition-transform duration-300
                    bg-white shadow-sm
                    ${isDark ? 'translate-x-6' : 'translate-x-0'}`}
      >
        {isDark
          ? <Moon className="w-3 h-3 text-slate-700" />
          : <Sun  className="w-3 h-3 text-amber-500" />
        }
      </span>
    </button>
  )
}

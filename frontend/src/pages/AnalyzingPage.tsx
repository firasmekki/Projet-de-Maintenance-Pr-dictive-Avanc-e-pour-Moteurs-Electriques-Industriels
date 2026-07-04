import { useEffect, useState } from 'react'
import { Cpu, Brain, Activity, ShieldCheck, TrendingUp } from 'lucide-react'
import clsx from 'clsx'

const STEPS = [
  { icon: Activity,    label: 'Analyse et validation du dataset',            delay: 0    },
  { icon: TrendingUp,  label: 'Calcul des statistiques et tendances',        delay: 800  },
  { icon: Cpu,         label: "Détection d'anomalies par Isolation Forest",  delay: 1600 },
  { icon: ShieldCheck, label: 'Classification des défauts et scoring',        delay: 2400 },
  { icon: Brain,       label: 'Génération du rapport de diagnostic IA',      delay: 3200 },
]

export default function AnalyzingPage() {
  const [visible, setVisible] = useState<number[]>([])

  useEffect(() => {
    const timers = STEPS.map((s, i) =>
      setTimeout(() => setVisible(v => [...v, i]), s.delay)
    )
    return () => timers.forEach(clearTimeout)
  }, [])

  return (
    <div className="max-w-lg mx-auto flex flex-col items-center gap-10 py-8">
      {/* Animated indicator */}
      <div className="relative w-28 h-28">
        <div className="absolute inset-0 rounded-full border-4 border-blue-500/20 dark:border-blue-600/30 animate-pulse" />
        <div className="absolute inset-3 rounded-full border-4 border-t-blue-500 border-blue-200 dark:border-blue-900 animate-spin" />
        <div className="absolute inset-0 flex items-center justify-center">
          <Cpu className="w-10 h-10 text-blue-500 dark:text-blue-400 animate-pulse" />
        </div>
      </div>

      <div className="text-center">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Analyse en cours</h2>
        <p className="text-gray-600 dark:text-slate-400 mt-1">
          ORBIT AI exécute le pipeline de diagnostic complet…
        </p>
      </div>

      <div className="w-full flex flex-col gap-3">
        {STEPS.map(({ icon: Icon, label }, i) => (
          <div
            key={i}
            className={clsx(
              'flex items-center gap-3 p-3 rounded-xl border transition-all duration-500',
              visible.includes(i)
                ? 'bg-blue-50 dark:bg-blue-950/40 border-blue-300 dark:border-blue-700 text-blue-800 dark:text-blue-200'
                : 'bg-gray-50 dark:bg-slate-800/30 border-gray-200 dark:border-slate-700/30 text-gray-400 dark:text-slate-600',
            )}
          >
            <Icon className={clsx(
              'w-5 h-5 shrink-0',
              visible.includes(i) ? 'text-blue-500 dark:text-blue-400' : 'text-gray-300 dark:text-slate-600',
            )} />
            <span className="text-sm font-medium">{label}</span>
            {visible.includes(i) && (
              <div className="ml-auto flex gap-0.5">
                {[0, 1, 2].map(d => (
                  <span
                    key={d}
                    className="w-1.5 h-1.5 rounded-full bg-blue-500 dark:bg-blue-400 animate-bounce"
                    style={{ animationDelay: `${d * 150}ms` }}
                  />
                ))}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}

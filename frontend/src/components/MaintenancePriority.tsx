import { Wrench, Clock } from 'lucide-react'
import clsx from 'clsx'
import type { PrioritizedRecommendation } from '../types'

interface Props {
  recommendations: PrioritizedRecommendation[]
  fault:           string
}

const URGENCY_STYLES: Record<string, { badge: string; label: string; dot: string }> = {
  immediate: { badge: 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300',    label: 'Immédiat',  dot: 'bg-red-500' },
  days:      { badge: 'bg-orange-100 dark:bg-orange-900/30 text-orange-700 dark:text-orange-300', label: 'Cette semaine', dot: 'bg-orange-500' },
  weeks:     { badge: 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-300', label: 'Ce mois',     dot: 'bg-yellow-500' },
  months:    { badge: 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300',  label: 'Planifié',  dot: 'bg-green-500' },
}

const PRIORITY_COLORS = ['bg-red-600', 'bg-red-500', 'bg-orange-500', 'bg-yellow-500', 'bg-blue-500', 'bg-gray-500']

export default function MaintenancePriority({ recommendations, fault }: Props) {
  if (!recommendations || recommendations.length === 0) return null

  return (
    <div className="card flex flex-col gap-4">
      <div className="flex items-center gap-2">
        <Wrench className="w-5 h-5 text-blue-500" />
        <h3 className="font-semibold text-gray-800 dark:text-slate-200">Plan de Maintenance Priorisé</h3>
        <span className="badge bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 text-xs">
          {recommendations.length} actions
        </span>
      </div>

      <div className="flex flex-col gap-2">
        {recommendations.map((rec, i) => {
          const urgency = URGENCY_STYLES[rec.urgency] ?? URGENCY_STYLES.months
          const pColor  = PRIORITY_COLORS[Math.min(i, PRIORITY_COLORS.length - 1)]

          return (
            <div
              key={rec.priority}
              className="flex items-start gap-3 p-3 rounded-xl bg-gray-50 dark:bg-slate-800/40 border border-gray-100 dark:border-slate-700/60 hover:border-blue-300 dark:hover:border-blue-700 transition-colors"
            >
              {/* Priority badge */}
              <div className={clsx('w-7 h-7 rounded-full flex items-center justify-center shrink-0 text-xs font-bold text-white', pColor)}>
                {rec.priority}
              </div>

              {/* Content */}
              <div className="flex-1 min-w-0">
                <p className="text-sm text-gray-800 dark:text-slate-200 font-medium leading-snug">
                  {rec.action}
                </p>
              </div>

              {/* Urgency badge */}
              <span className={clsx('badge text-xs shrink-0 flex items-center gap-1', urgency.badge)}>
                <span className={clsx('w-1.5 h-1.5 rounded-full', urgency.dot)} />
                {urgency.label}
              </span>
            </div>
          )
        })}
      </div>

      <div className="flex items-center gap-1.5 pt-1 border-t border-gray-100 dark:border-slate-700">
        <Clock className="w-3.5 h-3.5 text-gray-400 dark:text-slate-500" />
        <p className="text-xs text-gray-400 dark:text-slate-500">
          Normes : ISO 10816 · IEC 60034 · IEEE 112 · IEEE 519 · ISO 1940-1
        </p>
      </div>
    </div>
  )
}

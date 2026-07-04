import clsx from 'clsx'
import type { HealthTimelinePhase } from '../types'

interface Props {
  timeline: HealthTimelinePhase[]
}

const PHASE_STYLES: Record<string, { dot: string; label: string; bg: string; border: string }> = {
  'Sain':                { dot: 'bg-green-500',  label: 'text-green-700 dark:text-green-400',  bg: 'bg-green-50 dark:bg-green-900/20',  border: 'border-green-200 dark:border-green-800' },
  'Dégradation Précoce': { dot: 'bg-yellow-500', label: 'text-yellow-700 dark:text-yellow-400', bg: 'bg-yellow-50 dark:bg-yellow-900/20', border: 'border-yellow-200 dark:border-yellow-800' },
  'Avertissement':       { dot: 'bg-orange-500', label: 'text-orange-700 dark:text-orange-400', bg: 'bg-orange-50 dark:bg-orange-900/20', border: 'border-orange-200 dark:border-orange-800' },
  'Critique':            { dot: 'bg-red-500',    label: 'text-red-700 dark:text-red-400',       bg: 'bg-red-50 dark:bg-red-900/20',      border: 'border-red-200 dark:border-red-800' },
}

const PHASE_ICONS: Record<string, string> = {
  'Sain':                '✅',
  'Dégradation Précoce': '⚠️',
  'Avertissement':       '🔶',
  'Critique':            '🚨',
}

export default function HealthTimeline({ timeline }: Props) {
  if (!timeline || timeline.length === 0) return null

  return (
    <div className="card flex flex-col gap-4">
      <div className="flex items-center gap-2">
        <span className="text-lg">📈</span>
        <h3 className="font-semibold text-gray-800 dark:text-slate-200">Chronologie de Santé Moteur</h3>
        <span className="badge bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 text-xs">
          {timeline.length} phase{timeline.length > 1 ? 's' : ''}
        </span>
      </div>

      {/* Horizontal progress bar */}
      <div className="flex h-6 rounded-full overflow-hidden gap-0.5">
        {timeline.map((phase, i) => {
          const style = PHASE_STYLES[phase.phase] ?? PHASE_STYLES['Sain']
          const width = phase.end_pct - phase.start_pct
          return (
            <div
              key={i}
              className={clsx('h-full flex items-center justify-center text-xs font-bold text-white', style.dot)}
              style={{ width: `${width}%`, minWidth: width > 5 ? undefined : '4px' }}
              title={`${phase.phase} — ${phase.start_pct}% à ${phase.end_pct}%`}
            >
              {width > 12 ? PHASE_ICONS[phase.phase] : ''}
            </div>
          )
        })}
      </div>

      {/* Timeline steps */}
      <div className="flex flex-col gap-2">
        {timeline.map((phase, i) => {
          const style = PHASE_STYLES[phase.phase] ?? PHASE_STYLES['Sain']
          const isLast = i === timeline.length - 1
          return (
            <div key={i} className="flex items-start gap-3">
              {/* Connector */}
              <div className="flex flex-col items-center">
                <div className={clsx('w-3.5 h-3.5 rounded-full border-2 border-white dark:border-slate-900 shadow', style.dot)} />
                {!isLast && <div className="w-0.5 h-6 bg-gray-200 dark:bg-slate-700 mt-0.5" />}
              </div>

              {/* Content */}
              <div className={clsx(
                'flex-1 flex items-center justify-between px-3 py-2 rounded-lg border text-sm mb-1',
                style.bg, style.border,
              )}>
                <div className="flex items-center gap-2">
                  <span>{PHASE_ICONS[phase.phase] ?? '•'}</span>
                  <span className={clsx('font-semibold', style.label)}>{phase.phase}</span>
                  <span className="text-xs text-gray-500 dark:text-slate-500">
                    ({phase.start_pct}%–{phase.end_pct}% du dataset)
                  </span>
                </div>
                <span className="text-xs font-bold text-gray-600 dark:text-slate-400 tabular-nums">
                  Score moy : <strong>{phase.avg_health}/100</strong>
                </span>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

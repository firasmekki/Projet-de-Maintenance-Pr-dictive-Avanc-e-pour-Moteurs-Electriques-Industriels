import { Brain } from 'lucide-react'
import clsx from 'clsx'
import type { XAIContribution } from '../types'
import { FAULT_FR } from '../types'

interface Props {
  contributions: XAIContribution[]
  fault:         string
  confidence:    number
}

function getBarColor(idx: number): string {
  const colors = [
    'bg-red-500',    'bg-orange-500', 'bg-yellow-500',
    'bg-blue-500',   'bg-purple-500', 'bg-cyan-500', 'bg-pink-500',
  ]
  return colors[idx % colors.length]
}

function getTextColor(idx: number): string {
  const colors = [
    'text-red-600 dark:text-red-400',    'text-orange-600 dark:text-orange-400',
    'text-yellow-600 dark:text-yellow-400', 'text-blue-600 dark:text-blue-400',
    'text-purple-600 dark:text-purple-400', 'text-cyan-600 dark:text-cyan-400',
    'text-pink-600 dark:text-pink-400',
  ]
  return colors[idx % colors.length]
}

export default function XAIPanel({ contributions, fault, confidence }: Props) {
  if (!contributions || contributions.length === 0) return null

  const faultFr = FAULT_FR[fault] ?? fault

  return (
    <div className="card flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Brain className="w-5 h-5 text-purple-500" />
          <h3 className="font-semibold text-gray-800 dark:text-slate-200">Analyse Explicable (XAI)</h3>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs text-gray-500 dark:text-slate-400">Diagnostic :</span>
          <span className="font-bold text-sm text-gray-800 dark:text-slate-200">{faultFr}</span>
          <span className="badge bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300">
            {confidence}%
          </span>
        </div>
      </div>

      <p className="text-xs text-gray-500 dark:text-slate-400">
        Facteurs ayant contribué à ce diagnostic — poids relatifs normalisés à 100%.
      </p>

      <div className="flex flex-col gap-3">
        {contributions.map((item, i) => (
          <div key={i} className="flex flex-col gap-1">
            <div className="flex items-center justify-between text-sm">
              <div className="flex items-center gap-2">
                <span className={clsx('w-2.5 h-2.5 rounded-full shrink-0', getBarColor(i))} />
                <span className="text-gray-700 dark:text-slate-300">{item.feature}</span>
              </div>
              <span className={clsx('font-bold tabular-nums', getTextColor(i))}>
                {item.contribution}%
              </span>
            </div>
            <div className="h-2 bg-gray-100 dark:bg-slate-700 rounded-full overflow-hidden">
              <div
                className={clsx('h-full rounded-full transition-all duration-700', getBarColor(i))}
                style={{ width: `${item.contribution}%`, opacity: 0.85 }}
              />
            </div>
          </div>
        ))}
      </div>

      <p className="text-xs text-gray-400 dark:text-slate-500 border-t border-gray-100 dark:border-slate-700 pt-3">
        XAI — Explainable AI · Basé sur les paramètres capteurs et les normes ISO 10816 / IEC 60034
      </p>
    </div>
  )
}

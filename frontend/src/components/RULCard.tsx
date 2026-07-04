import { Clock, AlertTriangle } from 'lucide-react'
import clsx from 'clsx'
import type { RULEstimate } from '../types'

interface Props {
  rul:        RULEstimate
  fault:      string
  riskFactors: string[]
  risk7d:     number
  risk30d:    number
}

const LABEL_STYLES: Record<string, string> = {
  red:    'text-red-700 dark:text-red-400',
  orange: 'text-orange-700 dark:text-orange-400',
  yellow: 'text-yellow-700 dark:text-yellow-400',
  green:  'text-green-700 dark:text-green-400',
}

const BG_STYLES: Record<string, string> = {
  red:    'from-red-50 to-white border-red-200 dark:from-red-950/30 dark:to-slate-800 dark:border-red-800/60',
  orange: 'from-orange-50 to-white border-orange-200 dark:from-orange-950/30 dark:to-slate-800 dark:border-orange-800/60',
  yellow: 'from-yellow-50 to-white border-yellow-200 dark:from-yellow-950/30 dark:to-slate-800 dark:border-yellow-800/60',
  green:  'from-green-50 to-white border-green-200 dark:from-green-950/30 dark:to-slate-800 dark:border-green-800/60',
}

export default function RULCard({ rul, fault, riskFactors, risk7d, risk30d }: Props) {
  const labelColor = LABEL_STYLES[rul.label] ?? LABEL_STYLES.green
  const bgStyle    = BG_STYLES[rul.label] ?? BG_STYLES.green

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      {/* RUL Card */}
      <div className={clsx('bg-gradient-to-br border rounded-xl p-5 flex flex-col gap-3', bgStyle)}>
        <div className="flex items-center gap-2">
          <Clock className={clsx('w-5 h-5', labelColor)} />
          <h3 className="font-semibold text-gray-800 dark:text-slate-200">Durée de Vie Restante (RUL)</h3>
        </div>

        <div className="flex items-end gap-2">
          <span className={clsx('text-4xl font-extrabold tabular-nums leading-none', labelColor)}>
            {rul.value}
          </span>
        </div>

        <div className="flex items-center gap-2 text-sm">
          <span className="text-gray-500 dark:text-slate-400">Confiance :</span>
          <span className={clsx('font-semibold', labelColor)}>{rul.confidence}</span>
        </div>

        {rul.label === 'red' || rul.label === 'orange' ? (
          <div className="flex items-start gap-2 bg-white/60 dark:bg-slate-800/40 rounded-lg px-3 py-2">
            <AlertTriangle className="w-4 h-4 text-red-500 shrink-0 mt-0.5" />
            <p className="text-xs text-gray-700 dark:text-slate-300">
              Sans intervention, un arrêt imprévu est probable dans ce délai.
            </p>
          </div>
        ) : null}

        <p className="text-xs text-gray-400 dark:text-slate-500">
          Basé sur : taux de dégradation actuel, score de santé {fault !== 'No Fault' ? `et défaut ${fault}` : ''}
        </p>
      </div>

      {/* Risk explanation */}
      <div className="card flex flex-col gap-3">
        <h3 className="font-semibold text-gray-800 dark:text-slate-200 flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 text-orange-500" />
          Probabilité de Défaillance
        </h3>

        <div className="flex gap-6">
          <div>
            <p className="text-xs text-gray-500 dark:text-slate-400 uppercase tracking-wide">7 jours</p>
            <p className={clsx('text-3xl font-extrabold tabular-nums', risk7d >= 70 ? 'text-red-600 dark:text-red-400' : risk7d >= 40 ? 'text-orange-600 dark:text-orange-400' : 'text-yellow-600 dark:text-yellow-400')}>
              {risk7d.toFixed(1)}%
            </p>
          </div>
          <div>
            <p className="text-xs text-gray-500 dark:text-slate-400 uppercase tracking-wide">30 jours</p>
            <p className={clsx('text-3xl font-extrabold tabular-nums', risk30d >= 70 ? 'text-red-600 dark:text-red-400' : risk30d >= 40 ? 'text-orange-600 dark:text-orange-400' : 'text-yellow-600 dark:text-yellow-400')}>
              {risk30d.toFixed(1)}%
            </p>
          </div>
        </div>

        {riskFactors.length > 0 && (
          <div>
            <p className="text-xs font-semibold text-gray-600 dark:text-slate-400 uppercase tracking-wide mb-2">
              Parce que :
            </p>
            <ul className="flex flex-col gap-1.5">
              {riskFactors.map((f, i) => (
                <li key={i} className="flex items-start gap-2 text-sm text-gray-700 dark:text-slate-300">
                  <span className="text-orange-500 shrink-0 mt-0.5">•</span>
                  {f}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  )
}

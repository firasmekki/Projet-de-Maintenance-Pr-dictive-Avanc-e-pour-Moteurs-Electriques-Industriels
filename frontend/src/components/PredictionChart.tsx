import {
  ResponsiveContainer, ComposedChart, Area, Line, XAxis, YAxis,
  CartesianGrid, Tooltip, ReferenceLine, Legend,
} from 'recharts'
import { TrendingDown, TrendingUp, Minus, AlertTriangle } from 'lucide-react'
import clsx from 'clsx'
import type { HealthPrediction } from '../types'
import { useChartTheme } from '../hooks/useTheme'

interface Props {
  prediction:    HealthPrediction
  historicData:  { index: number; value: number; timestamp?: string }[]
}

const TREND_STYLES: Record<string, { icon: React.ElementType; color: string; badge: string }> = {
  'DÉGRADATION RAPIDE': { icon: TrendingDown, color: 'text-red-600 dark:text-red-400',    badge: 'bg-red-100 dark:bg-red-900/40 text-red-700 dark:text-red-300' },
  'DÉGRADATION LENTE':  { icon: TrendingDown, color: 'text-orange-600 dark:text-orange-400', badge: 'bg-orange-100 dark:bg-orange-900/40 text-orange-700 dark:text-orange-300' },
  'STABLE':             { icon: Minus,        color: 'text-blue-600 dark:text-blue-400',   badge: 'bg-blue-100 dark:bg-blue-900/40 text-blue-700 dark:text-blue-300' },
  'AMÉLIORATION':       { icon: TrendingUp,   color: 'text-green-600 dark:text-green-400', badge: 'bg-green-100 dark:bg-green-900/40 text-green-700 dark:text-green-300' },
}

function healthColor(v: number): string {
  if (v >= 75) return '#22c55e'
  if (v >= 45) return '#f59e0b'
  return '#ef4444'
}

export default function PredictionChart({ prediction, historicData }: Props) {
  const ct = useChartTheme()

  const trendStyle = TREND_STYLES[prediction.trend_label] ?? TREND_STYLES.STABLE
  const TrendIcon  = trendStyle.icon

  // Build combined historical + prediction data
  const nHist = historicData.length
  const histPoints = historicData.slice(-50).map((d, i) => ({
    x:       i,
    actual:  Math.max(0, Math.min(100, d.value)),
    label:   d.timestamp ? d.timestamp.substring(0, 10) : `t${d.index}`,
  }))

  const predPoints = prediction.trajectory.map((v, i) => ({
    x:          nHist + i,
    predicted:  Math.max(0, Math.min(100, v)),
    label:      `+${i + 1}`,
  }))

  const allData = [
    ...histPoints,
    // Junction point
    { x: nHist - 1, actual: histPoints[histPoints.length - 1]?.actual, predicted: histPoints[histPoints.length - 1]?.actual, label: 'Maintenant' },
    ...predPoints,
  ]

  const { day_7, day_14, day_30 } = prediction.predictions

  return (
    <div className="card flex flex-col gap-4">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-2">
        <div>
          <h3 className="font-semibold text-gray-800 dark:text-slate-200 flex items-center gap-2">
            <TrendingDown className="w-5 h-5 text-purple-500" />
            Prévision Temporelle — Trajectoire de Santé
          </h3>
          <p className="text-xs text-gray-500 dark:text-slate-400 mt-0.5">{prediction.method}</p>
        </div>
        <span className={clsx('badge text-xs flex items-center gap-1', trendStyle.badge)}>
          <TrendIcon className="w-3.5 h-3.5" />
          {prediction.trend_label}
        </span>
      </div>

      {/* Prediction KPIs */}
      <div className="grid grid-cols-3 gap-3">
        {([
          ['7 jours',  day_7,  '#ef4444'],
          ['14 jours', day_14, '#f97316'],
          ['30 jours', day_30, '#f59e0b'],
        ] as const).map(([label, val, color]) => (
          <div key={label} className="flex flex-col items-center gap-1 p-3 rounded-xl bg-gray-50 dark:bg-slate-800/40 border border-gray-100 dark:border-slate-700">
            <span className="text-xs text-gray-500 dark:text-slate-400 uppercase tracking-wide">{label}</span>
            <span className="text-2xl font-bold tabular-nums" style={{ color: healthColor(val) }}>
              {val}%
            </span>
            <div className="w-full h-1.5 bg-gray-200 dark:bg-slate-700 rounded-full overflow-hidden">
              <div className="h-full rounded-full transition-all" style={{ width: `${val}%`, background: healthColor(val) }} />
            </div>
          </div>
        ))}
      </div>

      {/* Alert for critical timeline */}
      {prediction.days_to_critical && (
        <div className="flex items-start gap-2 bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-800 rounded-xl px-3 py-2">
          <AlertTriangle className="w-4 h-4 text-red-600 dark:text-red-400 shrink-0 mt-0.5" />
          <p className="text-sm text-red-700 dark:text-red-300">
            Seuil critique estimé atteint dans <strong>{prediction.days_to_critical}</strong> — intervention recommandée avant cette date.
          </p>
        </div>
      )}

      {/* Chart */}
      <ResponsiveContainer width="100%" height={200}>
        <ComposedChart data={allData} margin={{ top: 4, right: 8, left: 0, bottom: 0 }}>
          <defs>
            <linearGradient id="grad-actual" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%"  stopColor="#3b82f6" stopOpacity={0.35} />
              <stop offset="95%" stopColor="#3b82f6" stopOpacity={0.02} />
            </linearGradient>
            <linearGradient id="grad-pred" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%"  stopColor="#f97316" stopOpacity={0.25} />
              <stop offset="95%" stopColor="#f97316" stopOpacity={0.02} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke={ct.grid} />
          <XAxis dataKey="label" tick={{ fontSize: 0 }} tickLine={false} />
          <YAxis domain={[0, 100]} tick={{ fontSize: 9, fill: ct.tick }} tickLine={false} axisLine={false} width={32} />
          <Tooltip
            contentStyle={{ background: ct.tooltipBg, border: `1px solid ${ct.tooltipBorder}`, borderRadius: 8 }}
            labelStyle={{ color: ct.tooltipText, fontSize: 10 }}
            formatter={(v: number, name: string) => [`${v.toFixed(1)}%`, name === 'actual' ? 'Historique' : 'Prévision']}
          />
          <ReferenceLine y={75} stroke="#22c55e" strokeDasharray="3 2" label={{ value: 'Sain (75%)', fill: '#22c55e', fontSize: 9, position: 'insideTopRight' }} />
          <ReferenceLine y={45} stroke="#f59e0b" strokeDasharray="3 2" label={{ value: 'Alerte (45%)', fill: '#f59e0b', fontSize: 9, position: 'insideTopRight' }} />
          <ReferenceLine x={nHist - 1} stroke={ct.grid} strokeDasharray="4 2" label={{ value: 'Maintenant', fill: ct.tick, fontSize: 9, position: 'insideTopLeft' }} />
          <Area type="monotone" dataKey="actual"    stroke="#3b82f6" fill="url(#grad-actual)" strokeWidth={2} dot={false} connectNulls />
          <Area type="monotone" dataKey="predicted" stroke="#f97316" fill="url(#grad-pred)"  strokeWidth={2} dot={false} strokeDasharray="5 3" connectNulls />
          <Legend formatter={(v) => v === 'actual' ? 'Historique (mesuré)' : 'Prévision (ML)'} />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  )
}

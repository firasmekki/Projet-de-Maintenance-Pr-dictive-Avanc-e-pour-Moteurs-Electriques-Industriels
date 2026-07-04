import {
  ResponsiveContainer, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ReferenceLine,
} from 'recharts'
import type { TimeSeriesPoint } from '../types'
import { useChartTheme } from '../hooks/useTheme'
import clsx from 'clsx'

interface Props {
  title:          string
  unit:           string
  data:           TimeSeriesPoint[]
  color?:         string
  trend?:         string
  thresholdHigh?: number
}

const TREND_BADGE: Record<string, string> = {
  RISING:  'bg-red-100 text-red-700 dark:bg-red-900/60 dark:text-red-300',
  FALLING: 'bg-green-100 text-green-700 dark:bg-green-900/60 dark:text-green-300',
  STABLE:  'bg-gray-100 text-gray-600 dark:bg-slate-700 dark:text-slate-300',
}

const TREND_LABEL: Record<string, string> = {
  RISING:  '↑ HAUSSE',
  FALLING: '↓ BAISSE',
  STABLE:  '→ STABLE',
}

export default function TrendChart({ title, unit, data, color = '#3b82f6', trend, thresholdHigh }: Props) {
  const ct = useChartTheme()

  if (!data.length) {
    return (
      <div className="card flex items-center justify-center h-52 text-gray-400 dark:text-slate-500 text-sm">
        Données {title.toLowerCase()} indisponibles
      </div>
    )
  }

  // Clamp health-score chart to 0-100
  const isPercentScore = unit === '%' && title.toLowerCase().includes('santé')
  const vals   = data.map(d => isPercentScore ? Math.max(0, Math.min(100, d.value)) : d.value)
  const minVal = Math.min(...vals)
  const maxVal = Math.max(...vals)
  const avg    = vals.reduce((a, b) => a + b, 0) / vals.length
  const domain: [number, number] = isPercentScore
    ? [0, 100]
    : [Math.max(0, minVal * 0.92), maxVal * 1.08]

  const formatted = data.map((d, i) => ({
    x:     d.timestamp ? d.timestamp.substring(0, 16) : String(i),
    value: isPercentScore ? Math.max(0, Math.min(100, d.value)) : d.value,
  }))

  const gradId = `grad-${title.replace(/\s+/g, '-')}`

  return (
    <div className="card flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <h3 className="font-semibold text-gray-800 dark:text-slate-200">{title}</h3>
        {trend && (
          <span className={clsx('badge text-xs', TREND_BADGE[trend] ?? TREND_BADGE.STABLE)}>
            {TREND_LABEL[trend] ?? trend}
          </span>
        )}
      </div>
      <ResponsiveContainer width="100%" height={160}>
        <AreaChart data={formatted} margin={{ top: 4, right: 4, left: 0, bottom: 0 }}>
          <defs>
            <linearGradient id={gradId} x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%"  stopColor={color} stopOpacity={0.3} />
              <stop offset="95%" stopColor={color} stopOpacity={0.02} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke={ct.grid} />
          <XAxis dataKey="x" tick={{ fontSize: 9, fill: ct.tick }} interval="preserveStartEnd" tickLine={false} />
          <YAxis
            domain={domain}
            tick={{ fontSize: 9, fill: ct.tick }}
            tickLine={false}
            axisLine={false}
            tickFormatter={v => v.toFixed(1)}
            width={40}
          />
          <Tooltip
            contentStyle={{ background: ct.tooltipBg, border: `1px solid ${ct.tooltipBorder}`, borderRadius: 8 }}
            labelStyle={{ color: ct.tooltipText, fontSize: 11 }}
            itemStyle={{ color: color, fontSize: 12 }}
            formatter={(v: number) => [`${v.toFixed(3)} ${unit}`, title]}
          />
          {thresholdHigh !== undefined && (
            <ReferenceLine
              y={thresholdHigh}
              stroke="#ef4444"
              strokeDasharray="4 2"
              label={{ value: 'Limite', fill: '#ef4444', fontSize: 10, position: 'insideTopRight' }}
            />
          )}
          <Area
            type="monotone"
            dataKey="value"
            stroke={color}
            strokeWidth={2}
            fill={`url(#${gradId})`}
            dot={false}
            activeDot={{ r: 4, fill: color }}
          />
        </AreaChart>
      </ResponsiveContainer>
      <div className="flex gap-4 text-xs text-gray-500 dark:text-slate-400">
        <span>Min <strong className="text-gray-700 dark:text-slate-200">{minVal.toFixed(2)}</strong></span>
        <span>Max <strong className="text-gray-700 dark:text-slate-200">{maxVal.toFixed(2)}</strong></span>
        <span>Moy <strong className="text-gray-700 dark:text-slate-200">{avg.toFixed(2)}</strong></span>
        <span className="ml-auto text-gray-400 dark:text-slate-500">{unit}</span>
      </div>
    </div>
  )
}

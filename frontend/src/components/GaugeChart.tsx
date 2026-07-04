import { PieChart, Pie, Cell } from 'recharts'
import { useChartTheme } from '../hooks/useTheme'

interface Props {
  value:    number
  label:    string
  colorFn?: (v: number) => string
  unit?:    string
}

function defaultColor(v: number) {
  if (v >= 75) return '#22c55e'
  if (v >= 50) return '#f59e0b'
  return '#ef4444'
}

export default function GaugeChart({ value, label, colorFn = defaultColor, unit = '' }: Props) {
  const { gaugeBg } = useChartTheme()
  const clamped = Math.max(0, Math.min(100, value))
  const fill    = colorFn(clamped)

  const data = [
    { value: clamped,       fill },
    { value: 100 - clamped, fill: gaugeBg },
  ]

  return (
    <div className="flex flex-col items-center gap-1">
      <div className="relative w-[160px] h-[90px]">
        <PieChart width={160} height={90}>
          <Pie
            data={data}
            cx={80}
            cy={80}
            startAngle={180}
            endAngle={0}
            innerRadius={55}
            outerRadius={78}
            dataKey="value"
            stroke="none"
            paddingAngle={2}
            isAnimationActive={true}
          >
            {data.map((entry, i) => (
              <Cell key={i} fill={entry.fill} />
            ))}
          </Pie>
        </PieChart>
        <div className="absolute inset-x-0 bottom-0 flex flex-col items-center">
          <span className="text-2xl font-bold tabular-nums" style={{ color: fill }}>
            {clamped.toFixed(0)}{unit}
          </span>
        </div>
      </div>
      <span className="text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-slate-400">
        {label}
      </span>
    </div>
  )
}

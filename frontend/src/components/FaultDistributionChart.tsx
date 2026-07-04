import { useState } from 'react'
import { useChartTheme } from '../hooks/useTheme'
import { FAULT_FR } from '../types'

const COLORS = ['#ef4444', '#f59e0b', '#3b82f6', '#8b5cf6', '#06b6d4', '#10b981', '#6b7280']

interface Props {
  data: { name: string; value: number }[]
}

interface Segment {
  name: string
  label: string
  value: number
  pct: number
  start: number
  end: number
  color: string
}

const CX = 110, CY = 110, OR = 90, IR = 56, GAP = 3

function buildSegments(items: { name: string; value: number; label: string }[]): Segment[] {
  const total = items.reduce((s, d) => s + d.value, 0)
  if (total === 0) return []
  let angle = -90
  return items.map((d, i) => {
    const pct = d.value / total
    const sweep = pct * 360
    const half = items.length > 1 ? GAP / 2 : 0
    const start = angle + half
    const end = angle + sweep - half
    angle += sweep
    return { name: d.name, label: d.label, value: d.value, pct, start, end, color: COLORS[i % COLORS.length] }
  })
}

function donutPath(cx: number, cy: number, r1: number, r2: number, a1: number, a2: number): string {
  const rad = (d: number) => (d * Math.PI) / 180
  const sx1 = cx + r1 * Math.cos(rad(a1)), sy1 = cy + r1 * Math.sin(rad(a1))
  const ex1 = cx + r1 * Math.cos(rad(a2)), ey1 = cy + r1 * Math.sin(rad(a2))
  const sx2 = cx + r2 * Math.cos(rad(a2)), sy2 = cy + r2 * Math.sin(rad(a2))
  const ex2 = cx + r2 * Math.cos(rad(a1)), ey2 = cy + r2 * Math.sin(rad(a1))
  const lg = a2 - a1 > 180 ? 1 : 0
  return `M${sx1},${sy1} A${r1},${r1},0,${lg},1,${ex1},${ey1} L${sx2},${sy2} A${r2},${r2},0,${lg},0,${ex2},${ey2} Z`
}

export default function FaultDistributionChart({ data }: Props) {
  const total = data.reduce((s, d) => s + d.value, 0)
  const ct = useChartTheme()
  const translated = data.map(d => ({ ...d, label: FAULT_FR[d.name] ?? d.name }))
  const segments = buildSegments(translated)
  const [activeIdx, setActiveIdx] = useState(0)
  const active = segments[activeIdx]

  const labelColor  = ct.isDark ? '#cbd5e1' : '#475569'
  const countColor  = ct.isDark ? '#64748b' : '#94a3b8'
  const trackColor  = ct.isDark ? '#1e293b' : '#f1f5f9'
  const trackStroke = ct.isDark ? '#334155' : '#e2e8f0'

  return (
    <div className="card flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <h3 className="font-semibold text-gray-800 dark:text-slate-200">Distribution des Défauts</h3>
        <span className="text-xs text-gray-500 dark:text-slate-400">{total} mesures</span>
      </div>

      <div className="flex flex-col md:flex-row items-center gap-6">
        {/* Custom SVG Donut */}
        <div className="shrink-0 w-[220px] h-[220px]">
          <svg viewBox="0 0 220 220" className="w-full h-full overflow-visible">
            <defs>
              {segments.map((s, i) => (
                <filter key={i} id={`glow-${i}`} x="-30%" y="-30%" width="160%" height="160%">
                  <feGaussianBlur in="SourceGraphic" stdDeviation="5" result="blur" />
                  <feMerge>
                    <feMergeNode in="blur" />
                    <feMergeNode in="SourceGraphic" />
                  </feMerge>
                </filter>
              ))}
            </defs>

            {/* Track background ring */}
            <circle
              cx={CX} cy={CY}
              r={(OR + IR) / 2}
              fill="none"
              stroke={trackStroke}
              strokeWidth={OR - IR + 2}
            />
            {/* Inner fill */}
            <circle cx={CX} cy={CY} r={IR - 1} fill={trackColor} />

            {/* Segments */}
            {segments.map((s, i) => {
              const isActive = i === activeIdx
              const r1 = isActive ? OR + 6 : OR
              const r2 = isActive ? IR - 4 : IR
              return (
                <path
                  key={i}
                  d={donutPath(CX, CY, r1, r2, s.start, s.end)}
                  fill={s.color}
                  opacity={isActive ? 1 : 0.55}
                  filter={isActive ? `url(#glow-${i})` : undefined}
                  style={{ transition: 'all 0.22s cubic-bezier(.4,0,.2,1)', cursor: 'pointer' }}
                  onMouseEnter={() => setActiveIdx(i)}
                />
              )
            })}

            {/* Center text via foreignObject for proper text wrapping */}
            <foreignObject x={CX - 50} y={CY - 46} width={100} height={92}>
              <div
                style={{
                  display: 'flex', flexDirection: 'column', alignItems: 'center',
                  justifyContent: 'center', height: '100%', textAlign: 'center',
                  gap: '3px', pointerEvents: 'none',
                }}
              >
                <span style={{
                  fontSize: 9.5, fontWeight: 700, lineHeight: 1.3,
                  color: labelColor, letterSpacing: '0.01em',
                }}>
                  {active?.label}
                </span>
                <span style={{
                  fontSize: 28, fontWeight: 900, lineHeight: 1,
                  color: active?.color,
                  textShadow: active ? `0 0 20px ${active.color}60` : 'none',
                }}>
                  {active ? `${(active.pct * 100).toFixed(1)}%` : ''}
                </span>
                <span style={{ fontSize: 9, color: countColor, fontVariantNumeric: 'tabular-nums' }}>
                  {active ? `${active.value} mesures` : ''}
                </span>
              </div>
            </foreignObject>
          </svg>
        </div>

        {/* Legend table */}
        <div className="flex-1 w-full">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-200 dark:border-slate-700">
                <th className="text-left pb-2 text-xs font-semibold text-gray-500 dark:text-slate-400 uppercase tracking-wide">Défaut</th>
                <th className="text-right pb-2 text-xs font-semibold text-gray-500 dark:text-slate-400 uppercase tracking-wide">Prob.</th>
                <th className="text-right pb-2 text-xs font-semibold text-gray-500 dark:text-slate-400 uppercase tracking-wide"></th>
              </tr>
            </thead>
            <tbody>
              {segments.map((s, i) => (
                <tr
                  key={s.name}
                  className={`border-b border-gray-100 dark:border-slate-700/50 cursor-pointer transition-colors
                             ${activeIdx === i ? 'bg-gray-50 dark:bg-slate-700/40' : 'hover:bg-gray-50 dark:hover:bg-slate-700/20'}`}
                  onMouseEnter={() => setActiveIdx(i)}
                >
                  <td className="py-2.5 font-medium text-gray-700 dark:text-slate-200">{s.label}</td>
                  <td className="py-2.5 text-right font-bold tabular-nums" style={{ color: s.color }}>
                    {(s.pct * 100).toFixed(1)}%
                  </td>
                  <td className="py-2.5 text-right pl-3">
                    <span
                      className="inline-block w-3 h-3 rounded-full ring-2 ring-offset-1 dark:ring-offset-slate-800"
                      style={{ background: s.color, ringColor: s.color }}
                    />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}

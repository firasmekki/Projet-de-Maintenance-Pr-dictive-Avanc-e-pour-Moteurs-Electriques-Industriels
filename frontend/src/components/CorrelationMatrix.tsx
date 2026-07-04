import { useState } from 'react'
import type { CorrelationMatrix as CorrelationMatrixType } from '../types'

interface Props {
  data: CorrelationMatrixType
}

function corrColor(v: number): string {
  // -1 → red, 0 → neutral, +1 → blue
  const abs = Math.abs(v)
  if (v > 0) {
    const r = Math.round(255 - abs * 150)
    const g = Math.round(255 - abs * 120)
    const b = 255
    return `rgb(${r},${g},${b})`
  } else if (v < 0) {
    const r = 255
    const g = Math.round(255 - abs * 120)
    const b = Math.round(255 - abs * 150)
    return `rgb(${r},${g},${b})`
  }
  return 'rgb(249,250,251)'
}

function corrTextColor(v: number): string {
  return Math.abs(v) > 0.5 ? '#ffffff' : '#374151'
}

function strengthLabel(v: number): string {
  const a = Math.abs(v)
  if (a >= 0.9) return 'Très forte'
  if (a >= 0.7) return 'Forte'
  if (a >= 0.4) return 'Modérée'
  if (a >= 0.2) return 'Faible'
  return 'Nulle'
}

export default function CorrelationMatrix({ data }: Props) {
  const [hovered, setHovered] = useState<[number, number] | null>(null)
  const { labels, matrix } = data

  const n = labels.length

  return (
    <div className="card flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="font-semibold text-gray-800 dark:text-slate-200">Matrice de Corrélation des Capteurs</h3>
          <p className="text-xs text-gray-500 dark:text-slate-400 mt-0.5">
            Corrélation de Pearson — Bleu : corrélation positive · Rouge : corrélation négative
          </p>
        </div>
        {hovered && (
          <div className="text-right">
            <p className="text-xs text-gray-500 dark:text-slate-400">
              {labels[hovered[0]]} ↔ {labels[hovered[1]]}
            </p>
            <p className="font-bold text-gray-800 dark:text-slate-200">
              r = {matrix[hovered[0]][hovered[1]].toFixed(3)} — {strengthLabel(matrix[hovered[0]][hovered[1]])}
            </p>
          </div>
        )}
      </div>

      <div className="overflow-x-auto">
        <table className="mx-auto border-collapse">
          <thead>
            <tr>
              <th className="w-24" />
              {labels.map((l, j) => (
                <th
                  key={j}
                  className="text-xs font-semibold text-gray-600 dark:text-slate-300 pb-2 px-1 text-center"
                  style={{ minWidth: 64 }}
                >
                  <span className="block truncate max-w-[60px]" title={l}>{l}</span>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {labels.map((rowLabel, i) => (
              <tr key={i}>
                <td className="text-xs font-semibold text-gray-600 dark:text-slate-300 pr-2 text-right whitespace-nowrap">
                  {rowLabel}
                </td>
                {labels.map((_, j) => {
                  const v     = matrix[i][j]
                  const bg    = corrColor(v)
                  const tc    = corrTextColor(v)
                  const isHov = hovered?.[0] === i && hovered?.[1] === j

                  return (
                    <td
                      key={j}
                      onMouseEnter={() => setHovered([i, j])}
                      onMouseLeave={() => setHovered(null)}
                      className="p-0.5 cursor-default"
                    >
                      <div
                        style={{
                          background: bg,
                          color: tc,
                          width: 60, height: 52,
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          borderRadius: 6,
                          fontSize: 11,
                          fontWeight: i === j ? 700 : 500,
                          border: isHov ? '2px solid #1e40af' : '2px solid transparent',
                          transition: 'transform 0.1s',
                          transform: isHov ? 'scale(1.08)' : 'scale(1)',
                        }}
                      >
                        {v.toFixed(2)}
                      </div>
                    </td>
                  )
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Color scale legend */}
      <div className="flex items-center gap-3 justify-center">
        <span className="text-xs text-gray-500 dark:text-slate-400">-1</span>
        <div className="flex h-3 rounded-full overflow-hidden w-48">
          {Array.from({ length: 40 }, (_, i) => {
            const v = -1 + (i / 39) * 2
            return <div key={i} style={{ flex: 1, background: corrColor(v) }} />
          })}
        </div>
        <span className="text-xs text-gray-500 dark:text-slate-400">+1</span>
        <div className="flex gap-3 text-xs text-gray-500 dark:text-slate-400 ml-4">
          <span className="flex items-center gap-1"><span className="w-3 h-3 rounded" style={{ background: corrColor(-0.8) }} /> Inverse</span>
          <span className="flex items-center gap-1"><span className="w-3 h-3 rounded" style={{ background: corrColor(0) }} />  Nulle</span>
          <span className="flex items-center gap-1"><span className="w-3 h-3 rounded" style={{ background: corrColor(0.8) }} /> Directe</span>
        </div>
      </div>
    </div>
  )
}

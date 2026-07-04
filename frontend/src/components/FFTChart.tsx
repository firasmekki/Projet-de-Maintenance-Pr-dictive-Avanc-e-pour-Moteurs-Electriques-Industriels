import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ReferenceLine, ResponsiveContainer, Cell } from 'recharts'
import { Activity } from 'lucide-react'
import type { FFTSpectrum } from '../types'
import { useChartTheme } from '../hooks/useTheme'

interface Props {
  fft:   FFTSpectrum
  fault: string
}

const FAULT_FREQ_HINTS: Record<string, string> = {
  'Bearing Wear':   'Roulement : fréquences BPFI/BPFO (multiples hautes fréquences)',
  'Misalignment':   'Désalignement : composante 2×RPM dominante',
  'Unbalance':      'Déséquilibre : composante 1×RPM dominante',
  'Rotor Fault':    'Défaut rotor : bandes latérales autour de la fréquence fondamentale',
  'Insulation Fault': 'Défaut isolation : peu visible en vibration — test électrique requis',
  'Overload':       'Surcharge : vibrations à 2× fréquence réseau (100/120 Hz)',
}

export default function FFTChart({ fft, fault }: Props) {
  const ct = useChartTheme()

  const domFreq = fft.dominant?.frequency ?? 0
  const domMag  = fft.dominant?.magnitude ?? 0

  // Only show significant spectrum components
  const data = fft.spectrum
    .filter(s => s.magnitude > domMag * 0.05)
    .map(s => ({
      freq: s.frequency.toFixed(4),
      mag:  round2(s.magnitude),
      isDominant: Math.abs(s.frequency - domFreq) < 0.0001,
    }))

  function round2(v: number) { return Math.round(v * 10000) / 10000 }

  const hint = FAULT_FREQ_HINTS[fault]

  return (
    <div className="card flex flex-col gap-4">
      <div className="flex items-center justify-between flex-wrap gap-2">
        <div>
          <h3 className="font-semibold text-gray-800 dark:text-slate-200 flex items-center gap-2">
            <Activity className="w-5 h-5 text-cyan-500" />
            Analyse Spectrale FFT — Vibration
          </h3>
          <p className="text-xs text-gray-500 dark:text-slate-400 mt-0.5">{fft.note}</p>
        </div>
        <div className="text-right">
          <p className="text-xs text-gray-500 dark:text-slate-400">Fréquence dominante</p>
          <p className="font-bold text-cyan-600 dark:text-cyan-400 tabular-nums">
            {domFreq.toFixed(4)} <span className="text-xs font-normal">{fft.frequency_unit}</span>
          </p>
        </div>
      </div>

      {hint && (
        <div className="flex items-start gap-2 bg-cyan-50 dark:bg-cyan-900/20 border border-cyan-200 dark:border-cyan-800 rounded-xl px-3 py-2">
          <Activity className="w-4 h-4 text-cyan-600 dark:text-cyan-400 shrink-0 mt-0.5" />
          <p className="text-xs text-cyan-700 dark:text-cyan-300">{hint}</p>
        </div>
      )}

      <ResponsiveContainer width="100%" height={180}>
        <BarChart data={data} margin={{ top: 4, right: 8, left: 0, bottom: 0 }} cursor={{ fill: 'transparent' }}>
          <CartesianGrid strokeDasharray="3 3" stroke={ct.grid} vertical={false} />
          <XAxis
            dataKey="freq"
            tick={{ fontSize: 8, fill: ct.tick }}
            tickLine={false}
            label={{ value: fft.frequency_unit, position: 'insideBottomRight', fontSize: 8, fill: ct.tick, offset: -4 }}
          />
          <YAxis tick={{ fontSize: 9, fill: ct.tick }} tickLine={false} axisLine={false} width={36} />
          <Tooltip
            contentStyle={{ background: ct.tooltipBg, border: `1px solid ${ct.tooltipBorder}`, borderRadius: 8 }}
            labelStyle={{ color: ct.tooltipText, fontSize: 10 }}
            formatter={(v: number) => [`${v.toFixed(5)}`, 'Amplitude']}
            labelFormatter={(l: string) => `Fréquence : ${l}`}
          />
          <Bar dataKey="mag" radius={[2, 2, 0, 0]}>
            {data.map((entry, i) => (
              <Cell
                key={i}
                fill={entry.isDominant ? '#f97316' : '#06b6d4'}
                opacity={entry.isDominant ? 1.0 : 0.65}
              />
            ))}
          </Bar>
          {domFreq > 0 && (
            <ReferenceLine
              x={domFreq.toFixed(4)}
              stroke="#f97316"
              strokeDasharray="3 2"
              label={{ value: '▲ Dominant', fill: '#f97316', fontSize: 9, position: 'top' }}
            />
          )}
        </BarChart>
      </ResponsiveContainer>

      <div className="flex items-center gap-4 text-xs text-gray-500 dark:text-slate-400">
        <span className="flex items-center gap-1.5">
          <span className="w-3 h-3 rounded-sm bg-orange-500" /> Fréquence dominante
        </span>
        <span className="flex items-center gap-1.5">
          <span className="w-3 h-3 rounded-sm bg-cyan-500 opacity-65" /> Autres composantes
        </span>
        <span className="ml-auto">{fft.n_points} points analysés</span>
      </div>
    </div>
  )
}

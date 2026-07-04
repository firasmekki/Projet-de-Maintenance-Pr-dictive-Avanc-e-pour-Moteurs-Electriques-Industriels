import { useEffect, useState } from 'react'
import {
  HeartPulse, Zap, ShieldAlert, TrendingUp, AlertCircle,
  Download, RefreshCw, Bot, ThumbsUp, AlertTriangle, Target,
} from 'lucide-react'
import clsx from 'clsx'
import GaugeChart             from '../components/GaugeChart'
import TrendChart             from '../components/TrendChart'
import FaultDistributionChart from '../components/FaultDistributionChart'
import MultiAgentPanel        from '../components/MultiAgentPanel'
import HealthTimeline         from '../components/HealthTimeline'
import XAIPanel               from '../components/XAIPanel'
import RULCard                from '../components/RULCard'
import MaintenancePriority    from '../components/MaintenancePriority'
import CorrelationMatrix      from '../components/CorrelationMatrix'
import PredictionChart        from '../components/PredictionChart'
import FFTChart               from '../components/FFTChart'
import type { AnalyzeResponse } from '../types'
import { FAULT_FR, HEALTH_STATUS_FR, SEVERITY_FR, TREND_FR, REC_FR } from '../types'

interface Props {
  result:   AnalyzeResponse
  filename: string
  onReset:  () => void
}

// ── Colour helpers ────────────────────────────────────────────────────────

function severityBadgeClass(s: string) {
  const m: Record<string, string> = {
    CRITICAL: 'bg-red-100    text-red-700    border-red-300    dark:bg-red-900/70    dark:text-red-300    dark:border-red-700',
    HIGH:     'bg-orange-100 text-orange-700 border-orange-300 dark:bg-orange-900/70 dark:text-orange-300 dark:border-orange-700',
    MEDIUM:   'bg-yellow-100 text-yellow-700 border-yellow-300 dark:bg-yellow-900/70 dark:text-yellow-300 dark:border-yellow-700',
    LOW:      'bg-green-100  text-green-700  border-green-300  dark:bg-green-900/70  dark:text-green-300  dark:border-green-700',
  }
  return m[s] ?? m.LOW
}

function healthColor(score: number) {
  if (score >= 75) return '#22c55e'
  if (score >= 50) return '#f59e0b'
  return '#ef4444'
}

function riskColor(r: number) {
  if (r < 20) return '#22c55e'
  if (r < 45) return '#f59e0b'
  if (r < 70) return '#f97316'
  return '#ef4444'
}

// ── Animated KPI card ─────────────────────────────────────────────────────

function KpiCard({
  icon: Icon, label, value, sub, sub2, accent = 'blue', badge, delay = 0,
}: {
  icon: React.ElementType
  label: string; value: string; sub?: string; sub2?: string
  accent?: 'blue' | 'green' | 'yellow' | 'red' | 'orange' | 'purple'
  badge?: string; delay?: number
}) {
  const [show, setShow] = useState(false)
  useEffect(() => { const t = setTimeout(() => setShow(true), delay); return () => clearTimeout(t) }, [delay])

  const gradients: Record<string, string> = {
    blue:   'from-blue-50   to-white border-blue-200   dark:from-blue-900/40   dark:to-blue-950/20   dark:border-blue-800/60',
    green:  'from-green-50  to-white border-green-200  dark:from-green-900/40  dark:to-green-950/20  dark:border-green-800/60',
    yellow: 'from-yellow-50 to-white border-yellow-200 dark:from-yellow-900/40 dark:to-yellow-950/20 dark:border-yellow-800/60',
    red:    'from-red-50    to-white border-red-200    dark:from-red-900/40    dark:to-red-950/20    dark:border-red-800/60',
    orange: 'from-orange-50 to-white border-orange-200 dark:from-orange-900/40 dark:to-orange-950/20 dark:border-orange-800/60',
    purple: 'from-purple-50 to-white border-purple-200 dark:from-purple-900/40 dark:to-purple-950/20 dark:border-purple-800/60',
  }
  const iconColors: Record<string, string> = {
    blue:   'text-blue-500 dark:text-blue-400',
    green:  'text-green-500 dark:text-green-400',
    yellow: 'text-yellow-500 dark:text-yellow-400',
    red:    'text-red-500 dark:text-red-400',
    orange: 'text-orange-500 dark:text-orange-400',
    purple: 'text-purple-500 dark:text-purple-400',
  }

  return (
    <div className={clsx(
      'bg-gradient-to-br border rounded-xl p-5 transition-all duration-700 ease-out',
      gradients[accent],
      show ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4',
    )}>
      <div className="flex items-start justify-between gap-2">
        <div className="flex flex-col gap-1 min-w-0">
          <p className="text-xs font-semibold text-gray-500 dark:text-slate-400 uppercase tracking-wider">{label}</p>
          <p className="text-xl font-bold text-gray-900 dark:text-white leading-tight truncate">{value}</p>
          {sub  && <p className="text-xs text-gray-500 dark:text-slate-400 mt-0.5">{sub}</p>}
          {sub2 && <p className="text-xs font-medium text-gray-600 dark:text-slate-300">{sub2}</p>}
        </div>
        <div className="flex flex-col items-end gap-2 shrink-0">
          <Icon className={clsx('w-6 h-6', iconColors[accent])} />
          {badge && (
            <span className={clsx('badge border text-xs', severityBadgeClass(badge))}>
              {SEVERITY_FR[badge] ?? badge}
            </span>
          )}
        </div>
      </div>
    </div>
  )
}

// ── Risk progress bar ─────────────────────────────────────────────────────

function RiskBar({ label, value }: { label: string; value: number }) {
  const color = riskColor(value)
  return (
    <div className="flex flex-col gap-1.5">
      <div className="flex justify-between text-sm">
        <span className="text-gray-600 dark:text-slate-400">{label}</span>
        <span className="font-semibold tabular-nums" style={{ color }}>{value.toFixed(1)}%</span>
      </div>
      <div className="h-2.5 bg-gray-200 dark:bg-slate-700 rounded-full overflow-hidden">
        <div className="h-full rounded-full transition-all duration-700" style={{ width: `${value}%`, background: color }} />
      </div>
    </div>
  )
}

// ── Early Degradation panel ───────────────────────────────────────────────

function EarlyDegradationPanel() {
  return (
    <div className="card border-l-4 border-yellow-400 bg-yellow-50 dark:bg-yellow-900/20 dark:border-yellow-500">
      <div className="flex items-start gap-3">
        <AlertTriangle className="w-6 h-6 text-yellow-600 dark:text-yellow-400 shrink-0 mt-0.5" />
        <div>
          <h3 className="font-bold text-yellow-800 dark:text-yellow-300 text-base">Dégradation Précoce Détectée</h3>
          <p className="text-yellow-700 dark:text-yellow-400 text-sm mt-1">
            Les tendances de température et de vibration sont toutes deux en hausse, mais les seuils critiques ne sont pas encore atteints.
          </p>
          <ul className="mt-2 space-y-1">
            {['Déséquilibre Rotor', 'Usure des Roulements (débutante)', 'Dégradation lubrification'].map(c => (
              <li key={c} className="flex items-center gap-2 text-sm text-yellow-800 dark:text-yellow-300">
                <span className="w-1.5 h-1.5 rounded-full bg-yellow-500" /> {c}
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  )
}

// ── Main ──────────────────────────────────────────────────────────────────

export default function ResultsPage({ result, filename, onReset }: Props) {
  const { analysis, ai_narrative } = result
  const isEarlyDegradation = analysis.fault === 'Early Degradation'

  const faultAccent = ((): 'green' | 'yellow' | 'orange' | 'red' | 'blue' => {
    if (analysis.fault === 'No Fault') return 'green'
    if (isEarlyDegradation) return 'yellow'
    if (analysis.severity === 'CRITICAL') return 'red'
    if (analysis.severity === 'HIGH') return 'orange'
    return 'yellow'
  })()

  const healthAccent = ((): 'green' | 'yellow' | 'red' => {
    if (analysis.health_score >= 75) return 'green'
    if (analysis.health_score >= 45) return 'yellow'
    return 'red'
  })()

  const downloadFile = (type: 'pdf' | 'csv' | 'xlsx' | 'json') => {
    window.location.href = `/api/v1/export/${type}/${result.report_id}`
  }

  const mp       = analysis.motor_profile
  const corrM    = analysis.correlation_matrix
  const pred     = analysis.health_prediction
  const fftData  = analysis.fft_spectrum
  const ae       = analysis.autoencoder
  const frRec = REC_FR[analysis.fault] ?? analysis.recommendation
  const recs  = analysis.recommendations_prioritized ?? []
  const xai   = analysis.xai ?? []
  const tl    = analysis.health_timeline ?? []
  const rf    = analysis.risk_factors ?? []
  const roots = analysis.root_causes ?? []

  // Compute RUL client-side if backend didn't provide it (old cached analyses)
  const rul = (analysis.rul?.value && analysis.rul.value !== '—')
    ? analysis.rul
    : (() => {
        const h = analysis.health_score
        const r = analysis.risk?.days_7 ?? 0
        const f = analysis.fault
        if (f === 'No Fault' && h >= 75)  return { value: '6+ mois',           days: 180, confidence: 'ÉLEVÉE', label: 'green'  }
        if (r >= 80 || h < 30) {
          const d = Math.max(1, Math.round((1 - r / 100) * 14))
          return { value: `${d}–${d * 2} jours`, days: d,  confidence: 'ÉLEVÉE', label: 'red'    }
        }
        if (r >= 50 || h < 50) {
          const d = Math.max(7, Math.round(30 * (1 - r / 100) + 5))
          return { value: `${d} jours`,          days: d,  confidence: 'ÉLEVÉE', label: 'orange' }
        }
        if (r >= 20) return { value: '1–3 mois',              days: 60,  confidence: 'MOYENNE', label: 'yellow' }
        return             { value: '3–6 mois',               days: 120, confidence: 'FAIBLE',  label: 'green'  }
      })()

  // ISO zone: use backend value or compute from vibration statistics
  const isoZone = (analysis.iso_zone && analysis.iso_zone !== '—')
    ? analysis.iso_zone
    : (() => {
        const avgVib = analysis.statistics?.vibration?.mean ?? 0
        if (avgVib > 7.1) return 'Zone D'
        if (avgVib > 4.5) return 'Zone C'
        if (avgVib > 2.3) return 'Zone B'
        return 'Zone A'
      })()

  return (
    <div className="flex flex-col gap-6">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Résultats de l'Analyse</h2>
          <p className="text-gray-500 dark:text-slate-400 text-sm mt-0.5">{filename}</p>
        </div>
        <button onClick={onReset} className="btn-ghost">
          <RefreshCw className="w-4 h-4" /> Nouvelle Analyse
        </button>
      </div>

      {/* Motor Profile card */}
      {mp && Object.values(mp).some(v => v) && (
        <div className="card bg-gradient-to-r from-blue-50 to-white dark:from-blue-950/20 dark:to-slate-800 border-blue-200 dark:border-blue-800">
          <div className="flex items-center gap-2 mb-3">
            <span className="text-lg">⚙️</span>
            <h3 className="font-semibold text-gray-800 dark:text-slate-200">Profil Moteur</h3>
            {mp.manufacturer && <span className="badge bg-blue-100 dark:bg-blue-900/40 text-blue-700 dark:text-blue-300">{mp.manufacturer}</span>}
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
            {[
              ['Nom',               mp.name],
              ['Puissance',         mp.nominal_power_kw   ? `${mp.nominal_power_kw} kW`     : null],
              ['Tension nominale',  mp.nominal_voltage_v  ? `${mp.nominal_voltage_v} V`      : null],
              ['Courant nominal',   mp.nominal_current_a  ? `${mp.nominal_current_a} A`      : null],
              ['Vitesse',           mp.nominal_speed_rpm  ? `${mp.nominal_speed_rpm} tr/min` : null],
              ['Isolation',         mp.insulation_class   ? `Classe ${mp.insulation_class}`  : null],
              ['Efficacité',        mp.efficiency_class],
              ['Protection',        mp.protection_class],
            ].filter(([, v]) => v).map(([label, value]) => (
              <div key={String(label)} className="flex flex-col">
                <span className="text-xs text-gray-500 dark:text-slate-400 uppercase tracking-wide">{label}</span>
                <span className="text-sm font-semibold text-gray-800 dark:text-slate-200">{value}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Early Degradation alert */}
      {isEarlyDegradation && <EarlyDegradationPanel />}

      {/* ── KPI Cards ─────────────────────────────────────────────────── */}
      <div className="grid grid-cols-2 lg:grid-cols-3 gap-3">
        <KpiCard
          icon={HeartPulse} label="Score de Santé"
          value={`${analysis.health_score}/100`}
          sub={HEALTH_STATUS_FR[analysis.health_status] ?? analysis.health_status}
          sub2={`RUL : ${rul.value}`}
          accent={healthAccent} delay={0}
        />
        <KpiCard
          icon={Zap} label="Défaut Détecté"
          value={FAULT_FR[analysis.fault] ?? analysis.fault}
          sub={`ISO ${isoZone}`}
          badge={analysis.severity} accent={faultAccent} delay={80}
        />
        <KpiCard
          icon={ShieldAlert} label="Niveau de Confiance"
          value={`${analysis.confidence}%`}
          sub="Confiance ML + Règles" accent="blue" delay={160}
        />
        <KpiCard
          icon={AlertCircle} label="Niveau de Risque"
          value={HEALTH_STATUS_FR[analysis.risk_level] ?? analysis.risk_level}
          sub={`7j : ${analysis.risk.days_7.toFixed(1)}%  |  30j : ${analysis.risk.days_30.toFixed(1)}%`}
          badge={analysis.risk_level}
          accent={analysis.risk_level === 'LOW' ? 'green' : analysis.risk_level === 'MEDIUM' ? 'yellow' : analysis.risk_level === 'HIGH' ? 'orange' : 'red'}
          delay={240}
        />
        <KpiCard
          icon={AlertCircle} label="Anomalies"
          value={String(analysis.anomaly.count)}
          sub={`${analysis.anomaly.percentage.toFixed(1)}% des mesures`}
          accent={analysis.anomaly.count > 0 ? 'orange' : 'green'} delay={320}
        />
        <KpiCard
          icon={ThumbsUp} label="Statut Général"
          value={HEALTH_STATUS_FR[analysis.health_status] ?? analysis.health_status}
          sub={roots.length > 0 ? roots[0] : 'Évaluation globale'}
          accent={healthAccent} delay={400}
        />
      </div>

      {/* ── Health Timeline ───────────────────────────────────────────── */}
      {tl.length >= 2 && <HealthTimeline timeline={tl} />}

      {/* ── RUL + Risk Explanation ────────────────────────────────────── */}
      <RULCard rul={rul} fault={analysis.fault} riskFactors={rf} risk7d={analysis.risk.days_7} risk30d={analysis.risk.days_30} />

      {/* ── Gauges + Risk bars ────────────────────────────────────────── */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="card flex flex-col gap-4">
          <h3 className="font-semibold text-gray-800 dark:text-slate-200">Jauges Système</h3>
          <div className="flex gap-6 justify-around flex-wrap">
            <GaugeChart value={analysis.health_score}  label="Score Santé" colorFn={healthColor} unit="%" />
            <GaugeChart value={analysis.risk.days_7}   label="Risque 7j"  colorFn={riskColor}   unit="%" />
            <GaugeChart value={analysis.risk.days_30}  label="Risque 30j" colorFn={riskColor}   unit="%" />
          </div>
        </div>

        <div className="card flex flex-col gap-4">
          <h3 className="font-semibold text-gray-800 dark:text-slate-200">Probabilité de Défaillance</h3>
          <div className="flex flex-col gap-4 mt-2">
            <RiskBar label="7 jours"  value={analysis.risk.days_7}  />
            <RiskBar label="30 jours" value={analysis.risk.days_30} />
          </div>
          <div className="border-t border-gray-200 dark:border-slate-700 pt-4 mt-2">
            <h4 className="text-xs font-semibold text-gray-500 dark:text-slate-400 uppercase mb-2">Tendances Capteurs</h4>
            <div className="grid grid-cols-3 gap-2">
              {Object.entries(analysis.trends).map(([key, val]) => {
                const colors: Record<string, string> = {
                  RISING: 'text-red-600 dark:text-red-400',
                  FALLING: 'text-green-600 dark:text-green-400',
                  STABLE: 'text-gray-500 dark:text-slate-400',
                }
                const icons: Record<string, string> = { RISING: '↑', FALLING: '↓', STABLE: '→' }
                return (
                  <div key={key} className="text-center">
                    <p className="text-xs text-gray-400 dark:text-slate-500 capitalize">{key}</p>
                    <p className={clsx('text-sm font-semibold', colors[val] ?? colors.STABLE)}>
                      {icons[val] ?? '→'} {TREND_FR[val] ?? val}
                    </p>
                  </div>
                )
              })}
            </div>
          </div>
        </div>
      </div>

      {/* ── XAI Panel ─────────────────────────────────────────────────── */}
      {xai.length > 0 && (
        <XAIPanel contributions={xai} fault={analysis.fault} confidence={analysis.confidence} />
      )}

      {/* ── Trend Charts ──────────────────────────────────────────────── */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <TrendChart title="Température" unit="°C"   data={analysis.time_series.temperature} color="#ef4444" trend={analysis.trends.temperature} thresholdHigh={90} />
        <TrendChart title="Vibration"   unit="mm/s" data={analysis.time_series.vibration}   color="#f59e0b" trend={analysis.trends.vibration}   thresholdHigh={7.1} />
        <TrendChart title="Courant"     unit="A"    data={analysis.time_series.current}     color="#3b82f6" trend={analysis.trends.current} />
        <TrendChart title="Tension"     unit="V"    data={analysis.time_series.voltage}     color="#8b5cf6" trend={analysis.trends.voltage} />
        <TrendChart title="Puissance"   unit="kW"   data={analysis.time_series.power}       color="#06b6d4" trend={analysis.trends.power} />
        <TrendChart title="Score Santé" unit="%"    data={analysis.time_series.health_score} color="#22c55e" />
      </div>

      {/* ── LSTM Health Trajectory Prediction ────────────────────────── */}
      {pred && pred.trajectory.length > 0 && (
        <PredictionChart prediction={pred} historicData={analysis.time_series.health_score} />
      )}

      {/* ── FFT Spectrum ──────────────────────────────────────────────── */}
      {fftData && fftData.spectrum.length > 0 && (
        <FFTChart fft={fftData} fault={analysis.fault} />
      )}

      {/* ── AutoEncoder anomaly section ───────────────────────────────── */}
      {ae && ae.n_anomalies !== undefined && (
        <div className="card">
          <h3 className="font-semibold text-gray-800 dark:text-slate-200 mb-3 flex items-center gap-2">
            <span className="text-lg">🔬</span> Détection d'Anomalies — Double Méthode
          </h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-xl p-4">
              <p className="text-xs font-semibold text-blue-600 dark:text-blue-400 uppercase mb-2">Isolation Forest</p>
              <p className="text-2xl font-bold text-gray-800 dark:text-slate-200">{analysis.anomaly.count} <span className="text-sm font-normal text-gray-500">anomalies</span></p>
              <p className="text-sm text-gray-600 dark:text-slate-400">{analysis.anomaly.percentage.toFixed(1)}% des mesures</p>
              <p className="text-xs text-gray-400 dark:text-slate-500 mt-1">Contamination : 5% — Forêt de 100 arbres</p>
            </div>
            <div className="bg-purple-50 dark:bg-purple-900/20 border border-purple-200 dark:border-purple-800 rounded-xl p-4">
              <p className="text-xs font-semibold text-purple-600 dark:text-purple-400 uppercase mb-2">AutoEncoder (PCA linéaire)</p>
              <p className="text-2xl font-bold text-gray-800 dark:text-slate-200">{ae.n_anomalies} <span className="text-sm font-normal text-gray-500">anomalies</span></p>
              <p className="text-sm text-gray-600 dark:text-slate-400">{ae.pct_anomalies.toFixed(1)}% des mesures</p>
              <p className="text-xs text-gray-400 dark:text-slate-500 mt-1">
                Erreur reconstruction : {ae.mean_reconstruction_error.toFixed(4)}
                {ae.explained_variance ? ` · Variance expliquée : ${ae.explained_variance}%` : ''}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* ── Fault Distribution ────────────────────────────────────────── */}
      {analysis.fault_distribution.length > 0 && (
        <FaultDistributionChart data={analysis.fault_distribution} />
      )}

      {/* ── Correlation Matrix ────────────────────────────────────────── */}
      {corrM && corrM.labels.length >= 2 && (
        <CorrelationMatrix data={corrM} />
      )}

      {/* ── Multi-Agent Analysis ──────────────────────────────────────── */}
      <MultiAgentPanel reportId={result.report_id} />

      {/* ── Prioritized Maintenance ───────────────────────────────────── */}
      {recs.length > 0 && <MaintenancePriority recommendations={recs} fault={analysis.fault} />}

      {/* ── Recommendation card ───────────────────────────────────────── */}
      <div className="card border-l-4 border-blue-500">
        <h3 className="font-semibold text-gray-800 dark:text-slate-200 mb-2 flex items-center gap-2">
          <TrendingUp className="w-4 h-4 text-blue-500" /> Recommandation
        </h3>
        <p className="text-gray-700 dark:text-slate-300 text-sm leading-relaxed">{frRec}</p>
      </div>

      {/* ── AI Report ─────────────────────────────────────────────────── */}
      {ai_narrative && (
        <div className="card">
          <h3 className="font-semibold text-gray-800 dark:text-slate-200 mb-4 flex items-center gap-2">
            <Bot className="w-5 h-5 text-purple-500" /> Rapport de Diagnostic IA
          </h3>
          <div className="prose prose-sm max-w-none dark:prose-invert">
            {ai_narrative.split('\n\n').map((para, i) => {
              const trimmed = para.trim()
              if (!trimmed) return null
              const isHeader = trimmed === trimmed.toUpperCase() && trimmed.length < 50
              return isHeader
                ? <h4 key={i} className="text-purple-700 dark:text-purple-300 font-semibold text-sm uppercase tracking-wide mt-4 mb-2">{trimmed}</h4>
                : <p  key={i} className="text-gray-700 dark:text-slate-300 text-sm leading-relaxed mb-3">{trimmed}</p>
            })}
          </div>
        </div>
      )}

      {/* ── Export Panel ──────────────────────────────────────────────── */}
      <div className="card">
        <h3 className="font-semibold text-gray-800 dark:text-slate-200 mb-4 flex items-center gap-2">
          <Download className="w-5 h-5 text-green-500" /> Télécharger les Résultats
        </h3>
        <div className="flex flex-wrap gap-3">
          {([
            ['pdf',  'Télécharger PDF',   'bg-red-50    hover:bg-red-100    border-red-300    text-red-700    dark:bg-red-900/30    dark:hover:bg-red-800/50    dark:border-red-800    dark:text-red-300'],
            ['xlsx', 'Télécharger Excel', 'bg-green-50  hover:bg-green-100  border-green-300  text-green-700  dark:bg-green-900/30  dark:hover:bg-green-800/50  dark:border-green-800  dark:text-green-300'],
            ['csv',  'Télécharger CSV',   'bg-blue-50   hover:bg-blue-100   border-blue-300   text-blue-700   dark:bg-blue-900/30   dark:hover:bg-blue-800/50   dark:border-blue-800   dark:text-blue-300'],
            ['json', 'Télécharger JSON',  'bg-purple-50 hover:bg-purple-100 border-purple-300 text-purple-700 dark:bg-purple-900/30 dark:hover:bg-purple-800/50 dark:border-purple-800 dark:text-purple-300'],
          ] as const).map(([type, label, cls]) => (
            <button
              key={type}
              onClick={() => downloadFile(type)}
              className={clsx('inline-flex items-center gap-2 px-5 py-2.5 font-semibold rounded-lg transition-colors text-sm border', cls)}
            >
              <Download className="w-4 h-4" /> {label}
            </button>
          ))}
        </div>
        <p className="text-xs text-gray-400 dark:text-slate-500 mt-3">
          Rapport complet incluant : XAI · Timeline · Multi-Agent · Recommandations · Données brutes
        </p>
      </div>
    </div>
  )
}

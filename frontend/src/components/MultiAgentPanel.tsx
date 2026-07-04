import { useState, useEffect } from 'react'
import { Bot, Loader2, ChevronDown, ChevronUp, CheckCircle2, AlertTriangle, XCircle, Info } from 'lucide-react'
import clsx from 'clsx'

interface AgentFinding {
  label:  string
  value:  string
  status: 'OK' | 'WARNING' | 'CRITICAL'
  detail: string
  norm?:  string
}

interface AgentResult {
  agent_id:   string
  title:      string
  icon:       string
  domain:     string
  severity:   string
  findings:   AgentFinding[]
  conclusion: string
  confidence: number
  norm_refs:  string[]
}

interface ConsensusRow {
  agent:           string
  icon:            string
  severity:        string
  severity_fr:     string
  confidence:      number
  is_coordinator?: boolean
}

interface Synthesis {
  verdict:              string
  urgency:              string
  color:                string
  overall_severity:     string
  timeline:             string
  priority_agent:       string
  narrative:            string
  action_plan:          string[]
  n_agents_warning:     number
  n_agents_total?:      number
  consensus_fault:      string
  consensus_confidence: number
  consensus_table?:     ConsensusRow[]
  high_plus?:           number
}

interface MultiAgentResult {
  agents:    AgentResult[]
  synthesis: Synthesis
}

interface Props {
  reportId: string
}

const SEVERITY_STYLES: Record<string, string> = {
  CRITICAL: 'bg-red-100 text-red-700 border-red-300 dark:bg-red-900/40 dark:text-red-300 dark:border-red-700',
  HIGH:     'bg-orange-100 text-orange-700 border-orange-300 dark:bg-orange-900/40 dark:text-orange-300 dark:border-orange-700',
  MEDIUM:   'bg-yellow-100 text-yellow-700 border-yellow-300 dark:bg-yellow-900/40 dark:text-yellow-300 dark:border-yellow-700',
  LOW:      'bg-green-100 text-green-700 border-green-300 dark:bg-green-900/40 dark:text-green-300 dark:border-green-700',
}

const SEVERITY_FR: Record<string, string> = {
  CRITICAL: 'CRITIQUE', HIGH: 'ÉLEVÉ', MEDIUM: 'MOYEN', LOW: 'FAIBLE',
}

const STATUS_ICON = {
  OK:       <CheckCircle2 className="w-4 h-4 text-green-500 shrink-0" />,
  WARNING:  <AlertTriangle className="w-4 h-4 text-yellow-500 shrink-0" />,
  CRITICAL: <XCircle className="w-4 h-4 text-red-500 shrink-0" />,
}

const VERDICT_COLORS: Record<string, string> = {
  red:    'bg-red-50 border-red-400 dark:bg-red-950/40 dark:border-red-600',
  orange: 'bg-orange-50 border-orange-400 dark:bg-orange-950/40 dark:border-orange-600',
  yellow: 'bg-yellow-50 border-yellow-400 dark:bg-yellow-950/40 dark:border-yellow-600',
  green:  'bg-green-50 border-green-400 dark:bg-green-950/40 dark:border-green-600',
}

const VERDICT_TEXT: Record<string, string> = {
  red:    'text-red-800 dark:text-red-300',
  orange: 'text-orange-800 dark:text-orange-300',
  yellow: 'text-yellow-800 dark:text-yellow-300',
  green:  'text-green-800 dark:text-green-300',
}

function AgentCard({ agent, isOpen, onToggle }: { agent: AgentResult; isOpen: boolean; onToggle: () => void }) {
  const sevStyle = SEVERITY_STYLES[agent.severity] ?? SEVERITY_STYLES.LOW

  return (
    <div className="card p-0 overflow-hidden">
      <button
        onClick={onToggle}
        className="w-full flex items-center gap-3 px-4 py-3 text-left hover:bg-gray-50 dark:hover:bg-slate-700/30 transition-colors"
      >
        <span className="text-xl shrink-0">{agent.icon}</span>
        <div className="flex-1 min-w-0">
          <p className="font-semibold text-gray-800 dark:text-slate-200 text-sm">{agent.title}</p>
          <p className="text-xs text-gray-500 dark:text-slate-400 truncate">{agent.domain}</p>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <span className={clsx('badge border text-xs', sevStyle)}>
            {SEVERITY_FR[agent.severity] ?? agent.severity}
          </span>
          <span className="text-xs text-gray-400 dark:text-slate-500">{agent.confidence}%</span>
          {isOpen
            ? <ChevronUp className="w-4 h-4 text-gray-400" />
            : <ChevronDown className="w-4 h-4 text-gray-400" />
          }
        </div>
      </button>

      {isOpen && (
        <div className="border-t border-gray-100 dark:border-slate-700 px-4 py-3 flex flex-col gap-3">
          {/* Findings */}
          <div className="flex flex-col gap-2">
            {agent.findings.map((f, i) => (
              <div key={i} className="flex items-start gap-2">
                {STATUS_ICON[f.status] ?? STATUS_ICON.OK}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="text-xs font-semibold text-gray-700 dark:text-slate-300">{f.label}</span>
                    <span className="text-xs font-bold text-gray-900 dark:text-white">{f.value}</span>
                    {f.norm && (
                      <span className="text-[10px] px-1.5 py-0.5 rounded bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400">
                        {f.norm}
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-gray-500 dark:text-slate-400 mt-0.5">{f.detail}</p>
                </div>
              </div>
            ))}
          </div>

          {/* Conclusion */}
          <div className="bg-gray-50 dark:bg-slate-700/40 rounded-lg px-3 py-2">
            <p className="text-xs text-gray-600 dark:text-slate-300">{agent.conclusion}</p>
          </div>

          {/* Norm refs */}
          {agent.norm_refs.length > 0 && (
            <div className="flex items-center gap-1.5 flex-wrap">
              <Info className="w-3 h-3 text-blue-400" />
              {agent.norm_refs.map(n => (
                <span key={n} className="text-[10px] px-1.5 py-0.5 rounded-full bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 font-medium">
                  {n}
                </span>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default function MultiAgentPanel({ reportId }: Props) {
  const [data,    setData]    = useState<MultiAgentResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [error,   setError]   = useState<string | null>(null)
  const [open,    setOpen]    = useState<Record<string, boolean>>({})
  const [started, setStarted] = useState(false)

  const run = async () => {
    setStarted(true)
    setLoading(true)
    setError(null)
    try {
      const res  = await fetch(`/api/v1/reports/${reportId}/multi-agent`, { method: 'POST' })
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const json = await res.json()
      setData(json)
      // Open all agents by default
      const openState: Record<string, boolean> = {}
      json.agents.forEach((a: AgentResult) => { openState[a.agent_id] = true })
      setOpen(openState)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Erreur inconnue')
    } finally {
      setLoading(false)
    }
  }

  const s = data?.synthesis

  return (
    <div className="card flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <h3 className="font-semibold text-gray-800 dark:text-slate-200 flex items-center gap-2">
          <Bot className="w-5 h-5 text-purple-500" />
          Analyse Multi-Agent IA
        </h3>
        {!started && (
          <button onClick={run} className="btn-primary text-sm py-1.5 px-4">
            <Bot className="w-4 h-4" /> Lancer l'analyse
          </button>
        )}
      </div>

      {!started && (
        <p className="text-sm text-gray-600 dark:text-slate-400">
          3 agents spécialisés analysent indépendamment les dimensions électrique, vibratoire et thermique, puis un agent coordinateur fusionne leurs conclusions.
        </p>
      )}

      {loading && (
        <div className="flex items-center gap-3 py-4 justify-center">
          <Loader2 className="w-5 h-5 animate-spin text-purple-500" />
          <span className="text-sm text-gray-600 dark:text-slate-400">
            Agents en cours d'analyse…
          </span>
        </div>
      )}

      {error && (
        <div className="bg-red-50 dark:bg-red-950/40 border border-red-300 dark:border-red-700 rounded-xl p-3 text-red-700 dark:text-red-300 text-sm">
          {error}
        </div>
      )}

      {data && (
        <>
          {/* Synthesis verdict */}
          {s && (
            <div className={clsx('border-l-4 rounded-xl p-4', VERDICT_COLORS[s.color] ?? VERDICT_COLORS.green)}>
              <div className="flex items-center gap-2 mb-2">
                <span className={clsx('font-bold text-base', VERDICT_TEXT[s.color])}>
                  🎯 {s.verdict}
                </span>
                <span className={clsx('badge border text-xs', SEVERITY_STYLES[s.overall_severity] ?? SEVERITY_STYLES.LOW)}>
                  {SEVERITY_FR[s.overall_severity] ?? s.overall_severity}
                </span>
              </div>
              <p className={clsx('text-sm mb-3', VERDICT_TEXT[s.color])}>{s.narrative}</p>

              <div className="flex gap-4 text-xs text-gray-600 dark:text-slate-400 mb-3">
                <span>⏱ Délai : <strong>{s.timeline}</strong></span>
                <span>🔍 Défaut : <strong>{s.consensus_fault}</strong></span>
                <span>📊 Confiance : <strong>{s.consensus_confidence}%</strong></span>
              </div>

              {/* Consensus table */}
              {s.consensus_table && s.consensus_table.length > 0 && (
                <div>
                  <p className="text-xs font-semibold text-gray-600 dark:text-slate-400 uppercase tracking-wide mb-2">
                    Tableau de Consensus
                  </p>
                  <div className="overflow-hidden rounded-lg border border-gray-200 dark:border-slate-700">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="bg-gray-50 dark:bg-slate-800/60 text-xs">
                          <th className="px-3 py-2 text-left text-gray-500 dark:text-slate-400 font-semibold">Agent</th>
                          <th className="px-3 py-2 text-center text-gray-500 dark:text-slate-400 font-semibold">Sévérité</th>
                          <th className="px-3 py-2 text-right text-gray-500 dark:text-slate-400 font-semibold">Confiance</th>
                        </tr>
                      </thead>
                      <tbody>
                        {s.consensus_table.map((row, i) => (
                          <tr
                            key={i}
                            className={clsx(
                              'border-t border-gray-100 dark:border-slate-700/50',
                              row.is_coordinator ? 'bg-blue-50 dark:bg-blue-900/20 font-semibold' : '',
                            )}
                          >
                            <td className="px-3 py-2 text-gray-700 dark:text-slate-300">
                              {row.icon} {row.agent}
                            </td>
                            <td className="px-3 py-2 text-center">
                              <span className={clsx('badge border text-xs', SEVERITY_STYLES[row.severity] ?? SEVERITY_STYLES.LOW)}>
                                {row.severity_fr}
                              </span>
                            </td>
                            <td className="px-3 py-2 text-right text-gray-600 dark:text-slate-400 tabular-nums">
                              {Math.min(100, Math.max(0, row.confidence))}%
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                  {s.high_plus !== undefined && s.n_agents_total !== undefined && (
                    <p className="text-xs text-gray-500 dark:text-slate-400 mt-1.5">
                      {s.high_plus} sur {s.n_agents_total} agents classifient HIGH ou CRITICAL
                      {s.high_plus >= 2 ? ' — escalade vers CRITIQUE' : ''}
                    </p>
                  )}
                </div>
              )}
            </div>
          )}

          {/* Agent cards */}
          <div className="flex flex-col gap-3">
            {data.agents.map(agent => (
              <AgentCard
                key={agent.agent_id}
                agent={agent}
                isOpen={!!open[agent.agent_id]}
                onToggle={() => setOpen(o => ({ ...o, [agent.agent_id]: !o[agent.agent_id] }))}
              />
            ))}
          </div>
        </>
      )}
    </div>
  )
}

import { useState } from 'react'
import {
  CloudUpload, Loader2, CheckCircle2,
  Thermometer, Activity, Zap, Radio, Gauge, Percent, Cpu, Package, Clock,
  History, Eye, Trash2, ChevronDown, ChevronUp, AlertTriangle,
} from 'lucide-react'
import DropZone from '../components/DropZone'
import { api } from '../api/client'
import type { UploadResponse, HistoryEntry } from '../types'
import { FAULT_FR } from '../types'
import clsx from 'clsx'

interface Props {
  onUploaded:      (data: UploadResponse, file: File) => void
  history:         HistoryEntry[]
  onOpenHistory:   (entry: HistoryEntry) => void
  onDeleteHistory: (reportId: string) => void
  restoring:       boolean
}

const SUPPORTED_COLS = [
  { key: 'temperature',  label: 'Température',         icon: Thermometer, color: 'text-red-500' },
  { key: 'vibration',    label: 'Vibration',            icon: Activity,    color: 'text-orange-500' },
  { key: 'current',      label: 'Courant',              icon: Zap,         color: 'text-blue-500' },
  { key: 'voltage',      label: 'Tension',              icon: Radio,       color: 'text-purple-500' },
  { key: 'power',        label: 'Puissance',            icon: Gauge,       color: 'text-cyan-500' },
  { key: 'power_factor', label: 'Facteur de Puissance', icon: Percent,     color: 'text-green-500' },
  { key: 'thd',          label: 'THD',                  icon: Cpu,         color: 'text-yellow-500' },
  { key: 'load',         label: 'Charge',               icon: Package,     color: 'text-pink-500' },
  { key: 'timestamp',    label: 'Horodatage',           icon: Clock,       color: 'text-slate-500' },
]

function severityColor(s: string | null) {
  if (s === 'CRITICAL') return 'text-red-600 dark:text-red-400'
  if (s === 'HIGH')     return 'text-orange-600 dark:text-orange-400'
  if (s === 'MEDIUM')   return 'text-yellow-600 dark:text-yellow-400'
  return 'text-green-600 dark:text-green-400'
}

function healthDot(score: number | null) {
  if (score === null) return 'bg-gray-400'
  if (score >= 75) return 'bg-green-500'
  if (score >= 50) return 'bg-yellow-500'
  return 'bg-red-500'
}

function formatDate(iso: string) {
  const d = new Date(iso)
  const now = Date.now()
  const diff = now - d.getTime()
  const mins  = Math.floor(diff / 60000)
  const hours = Math.floor(diff / 3600000)
  const days  = Math.floor(diff / 86400000)
  if (mins  < 1)   return "À l'instant"
  if (mins  < 60)  return `Il y a ${mins} min`
  if (hours < 24)  return `Il y a ${hours}h`
  if (days  < 7)   return `Il y a ${days}j`
  return d.toLocaleDateString('fr-FR', { day: '2-digit', month: '2-digit', year: '2-digit' })
}

// ── Confirmation dialog ─────────────────────────────────────────────────────

function DeleteConfirmDialog({
  filename,
  onConfirm,
  onCancel,
}: { filename: string; onConfirm: () => void; onCancel: () => void }) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
      <div className="card w-full max-w-sm shadow-2xl">
        <div className="flex items-center gap-3 mb-3">
          <div className="w-10 h-10 rounded-xl bg-red-100 dark:bg-red-900/40 flex items-center justify-center">
            <AlertTriangle className="w-5 h-5 text-red-600 dark:text-red-400" />
          </div>
          <h3 className="font-bold text-gray-900 dark:text-white">Supprimer l'analyse</h3>
        </div>
        <p className="text-sm text-gray-600 dark:text-slate-400 mb-1">
          Êtes-vous sûr de vouloir supprimer cette analyse ?
        </p>
        <p className="text-xs font-medium text-gray-500 dark:text-slate-500 mb-5 truncate">
          {filename}
        </p>
        <div className="flex gap-3">
          <button onClick={onCancel}  className="btn-secondary flex-1 justify-center">Annuler</button>
          <button onClick={onConfirm} className="btn-danger flex-1 justify-center">Supprimer</button>
        </div>
      </div>
    </div>
  )
}

// ── Main ────────────────────────────────────────────────────────────────────

export default function UploadPage({ onUploaded, history, onOpenHistory, onDeleteHistory, restoring }: Props) {
  const [file,       setFile]       = useState<File | null>(null)
  const [loading,    setLoading]    = useState(false)
  const [error,      setError]      = useState<string | null>(null)
  const [showCols,   setShowCols]   = useState(false)
  const [deletingId, setDeletingId] = useState<string | null>(null)

  const handleUpload = async () => {
    if (!file) return
    setLoading(true)
    setError(null)
    try {
      const result = await api.uploadDataset(file)
      onUploaded(result, file)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "L'importation a échoué")
    } finally {
      setLoading(false)
    }
  }

  const confirmDelete = (entry: HistoryEntry) => setDeletingId(entry.report_id)

  const doDelete = () => {
    if (deletingId) {
      onDeleteHistory(deletingId)
      setDeletingId(null)
    }
  }

  const entryToDelete = history.find(h => h.report_id === deletingId)

  return (
    <>
      {/* Delete confirmation overlay */}
      {deletingId && entryToDelete && (
        <DeleteConfirmDialog
          filename={entryToDelete.filename}
          onConfirm={doDelete}
          onCancel={() => setDeletingId(null)}
        />
      )}

      <div className="max-w-2xl mx-auto flex flex-col gap-6">
        {/* Title */}
        <div className="text-center">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Importer un Dataset</h1>
          <p className="text-gray-600 dark:text-slate-400 mt-2">
            Importez votre dataset de capteurs moteur pour démarrer l'analyse prédictive IA
          </p>
        </div>

        {/* Drop zone */}
        <DropZone onFile={setFile} disabled={loading || restoring} />

        {/* Error */}
        {error && (
          <div className="bg-red-50 dark:bg-red-950/60 border border-red-300 dark:border-red-700 rounded-xl p-4 text-red-700 dark:text-red-300 text-sm">
            {error}
          </div>
        )}

        {/* Upload button */}
        <button
          onClick={handleUpload}
          disabled={!file || loading || restoring}
          className="btn-primary justify-center text-base py-3.5"
        >
          {loading
            ? <><Loader2 className="w-5 h-5 animate-spin" /> Importation & Validation…</>
            : <><CloudUpload className="w-5 h-5" /> Importer & Prévisualiser le Dataset</>
          }
        </button>

        {/* ── History panel ────────────────────────────────────────────── */}
        {history.length > 0 && (
          <div className="card">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <History className="w-4 h-4 text-blue-500" />
                <h3 className="font-semibold text-gray-800 dark:text-slate-200">
                  Historique des Analyses
                </h3>
                <span className="badge bg-blue-100 dark:bg-blue-900/40 text-blue-700 dark:text-blue-300 text-xs">
                  {history.length}
                </span>
              </div>
            </div>

            <div className="flex flex-col gap-2">
              {history.map(entry => (
                <div
                  key={entry.report_id}
                  className="flex items-center gap-3 p-3 rounded-xl
                             bg-gray-50 dark:bg-slate-700/40
                             border border-gray-100 dark:border-slate-700
                             hover:border-blue-300 dark:hover:border-blue-600
                             transition-colors group"
                >
                  {/* Health dot */}
                  <span className={clsx('w-2.5 h-2.5 rounded-full shrink-0', healthDot(entry.health_score))} />

                  {/* File info */}
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-800 dark:text-slate-200 truncate">
                      {entry.filename}
                    </p>
                    <div className="flex items-center gap-2 mt-0.5 flex-wrap">
                      <span className="text-xs text-gray-500 dark:text-slate-400">
                        {formatDate(entry.analyzed_at)}
                      </span>
                      {entry.fault && (
                        <span className={clsx('text-xs font-medium', severityColor(entry.severity))}>
                          {FAULT_FR[entry.fault] ?? entry.fault}
                        </span>
                      )}
                      {entry.health_score !== null && (
                        <span className="text-xs text-gray-400 dark:text-slate-500">
                          Santé : <strong className="text-gray-600 dark:text-slate-300">{entry.health_score}</strong>/100
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="flex items-center gap-1 shrink-0">
                    <button
                      onClick={() => onOpenHistory(entry)}
                      disabled={restoring}
                      title="Ouvrir l'analyse"
                      className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs font-medium
                                 bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300
                                 hover:bg-blue-100 dark:hover:bg-blue-800/50 transition-colors
                                 disabled:opacity-50"
                    >
                      {restoring
                        ? <Loader2 className="w-3.5 h-3.5 animate-spin" />
                        : <Eye className="w-3.5 h-3.5" />
                      }
                      Ouvrir
                    </button>
                    <button
                      onClick={() => confirmDelete(entry)}
                      title="Supprimer"
                      className="p-1.5 rounded-lg text-gray-400 dark:text-slate-500
                                 hover:bg-red-50 dark:hover:bg-red-900/30
                                 hover:text-red-600 dark:hover:text-red-400 transition-colors"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ── Colonnes supportées (collapsible) ────────────────────────── */}
        <div className="card">
          <button
            onClick={() => setShowCols(v => !v)}
            className="w-full flex items-center justify-between gap-2"
          >
            <div className="flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-green-500" />
              <span className="font-semibold text-gray-800 dark:text-slate-200">Colonnes Recommandées</span>
            </div>
            {showCols
              ? <ChevronUp   className="w-4 h-4 text-gray-400 dark:text-slate-500" />
              : <ChevronDown className="w-4 h-4 text-gray-400 dark:text-slate-500" />
            }
          </button>

          {showCols && (
            <div className="mt-4">
              <p className="text-sm text-gray-600 dark:text-slate-400 mb-4">
                Le système détecte automatiquement les colonnes disponibles.
                L'analyse s'adapte automatiquement aux données disponibles.
                Aucune obligation d'avoir toutes les colonnes.
              </p>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                {SUPPORTED_COLS.map(({ key, label, icon: Icon, color }) => (
                  <div
                    key={key}
                    className="flex items-center gap-2.5 px-3 py-2 rounded-lg
                               bg-gray-50 dark:bg-slate-700/50
                               border border-gray-100 dark:border-slate-700"
                  >
                    <Icon className={`w-4 h-4 ${color}`} />
                    <span className="text-sm text-gray-700 dark:text-slate-300">{label}</span>
                    <code className="ml-auto text-xs text-blue-600 dark:text-blue-400 font-mono">{key}</code>
                  </div>
                ))}
              </div>
              <p className="text-xs text-gray-500 dark:text-slate-500 mt-3">
                Au moins une colonne parmi{' '}
                <code className="text-blue-600 dark:text-blue-400">temperature</code>,{' '}
                <code className="text-blue-600 dark:text-blue-400">vibration</code> ou{' '}
                <code className="text-blue-600 dark:text-blue-400">current</code> est requise.
              </p>
            </div>
          )}
        </div>
      </div>
    </>
  )
}
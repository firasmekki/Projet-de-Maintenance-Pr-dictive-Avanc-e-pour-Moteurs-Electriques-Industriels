import { useState } from 'react'
import { FileText, Rows3, Columns3, AlertTriangle, Star, BarChart3, Trash2, Loader2 } from 'lucide-react'
import DataTable from '../components/DataTable'
import MotorProfileForm from '../components/MotorProfileForm'
import { api } from '../api/client'
import type { AnalyzeResponse, MotorProfile, UploadResponse } from '../types'
import clsx from 'clsx'

interface Props {
  upload:     UploadResponse
  onAnalyzed: (result: AnalyzeResponse) => void
  onClear:    () => void
}

function qualityColor(score: number) {
  if (score >= 90) return 'text-green-600 dark:text-green-400'
  if (score >= 70) return 'text-yellow-600 dark:text-yellow-400'
  return 'text-red-600 dark:text-red-400'
}

function MetaCard({ icon: Icon, label, value, colorClass }: {
  icon: React.ElementType; label: string; value: string; colorClass?: string
}) {
  return (
    <div className="card flex items-center gap-4">
      <div className="w-10 h-10 rounded-xl bg-gray-100 dark:bg-slate-700 flex items-center justify-center shrink-0">
        <Icon className={clsx('w-5 h-5', colorClass ?? 'text-blue-500')} />
      </div>
      <div>
        <p className="text-xs text-gray-500 dark:text-slate-400 uppercase tracking-wide">{label}</p>
        <p className={clsx('text-lg font-bold', colorClass ?? 'text-gray-900 dark:text-white')}>{value}</p>
      </div>
    </div>
  )
}

export default function PreviewPage({ upload, onAnalyzed, onClear }: Props) {
  const [loading,      setLoading]      = useState(false)
  const [error,        setError]        = useState<string | null>(null)
  const [motorProfile, setMotorProfile] = useState<MotorProfile | null>(null)

  const handleAnalyze = async () => {
    setLoading(true)
    setError(null)
    try {
      const result = await api.analyzeReport(upload.report_id, motorProfile)
      onAnalyzed(result)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "L'analyse a échoué")
    } finally {
      setLoading(false)
    }
  }

  const formatBytes = (b: number) => b < 1024 * 1024
    ? `${(b / 1024).toFixed(1)} Ko`
    : `${(b / 1024 / 1024).toFixed(2)} Mo`

  const qualityBarColor = upload.quality_score >= 90
    ? '#22c55e'
    : upload.quality_score >= 70
    ? '#f59e0b'
    : '#ef4444'

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Aperçu des Données</h2>
          <p className="text-gray-500 dark:text-slate-400 text-sm mt-0.5">
            {upload.filename} — {formatBytes(upload.file_size)}
          </p>
        </div>
        <button onClick={onClear} className="btn-ghost text-red-600 dark:text-red-400 border-red-300 dark:border-red-800 hover:border-red-400 dark:hover:border-red-500">
          <Trash2 className="w-4 h-4" /> Effacer
        </button>
      </div>

      {/* Metadata cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <MetaCard icon={Rows3}       label="Enregistrements" value={upload.row_count.toLocaleString()} />
        <MetaCard icon={Columns3}    label="Colonnes"         value={String(upload.column_count)} />
        <MetaCard
          icon={AlertTriangle}
          label="Valeurs Manquantes"
          value={String(upload.missing_values)}
          colorClass={upload.missing_values > 0 ? 'text-yellow-600 dark:text-yellow-400' : 'text-green-600 dark:text-green-400'}
        />
        <MetaCard
          icon={Star}
          label="Score Qualité"
          value={`${upload.quality_score.toFixed(1)}%`}
          colorClass={qualityColor(upload.quality_score)}
        />
      </div>

      {/* Quality bar */}
      <div className="card">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-medium text-gray-700 dark:text-slate-300">Qualité des Données</span>
          <span className={clsx('font-bold', qualityColor(upload.quality_score))}>
            {upload.quality_score.toFixed(1)}%
          </span>
        </div>
        <div className="h-2.5 bg-gray-200 dark:bg-slate-700 rounded-full overflow-hidden">
          <div
            className="h-full rounded-full transition-all duration-700"
            style={{ width: `${upload.quality_score}%`, background: qualityBarColor }}
          />
        </div>
        <div className="flex flex-wrap gap-2 mt-3">
          {upload.columns.map(col => (
            <span key={col} className="badge bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 border border-blue-200 dark:border-blue-800 text-xs">
              {col}
            </span>
          ))}
        </div>
      </div>

      {/* Motor Profile */}
      <MotorProfileForm onChange={setMotorProfile} />

      {/* Data table */}
      <div className="card">
        <h3 className="font-semibold text-gray-800 dark:text-slate-200 mb-4 flex items-center gap-2">
          <FileText className="w-4 h-4 text-blue-500" />
          Aperçu du Dataset — {upload.preview.length} sur {upload.row_count.toLocaleString()} lignes
        </h3>
        <DataTable columns={upload.columns} rows={upload.preview} pageSize={15} />
      </div>

      {error && (
        <div className="bg-red-50 dark:bg-red-950/60 border border-red-300 dark:border-red-700 rounded-xl p-4 text-red-700 dark:text-red-300 text-sm">
          {error}
        </div>
      )}

      {/* Action buttons */}
      <div className="flex gap-3">
        <button
          onClick={handleAnalyze}
          disabled={loading}
          className="btn-primary flex-1 justify-center text-base py-3.5"
        >
          {loading
            ? <><Loader2 className="w-5 h-5 animate-spin" /> Analyse IA en cours…</>
            : <><BarChart3 className="w-5 h-5" /> Analyser le Dataset</>
          }
        </button>
        <button onClick={onClear} className="btn-secondary px-6">
          <Trash2 className="w-4 h-4" /> Effacer
        </button>
      </div>
    </div>
  )
}

import { useState, useCallback } from 'react'
import { Cpu, History } from 'lucide-react'
import StepIndicator  from './components/StepIndicator'
import ThemeToggle    from './components/ThemeToggle'
import ChatWidget     from './components/ChatWidget'
import UploadPage     from './pages/UploadPage'
import PreviewPage    from './pages/PreviewPage'
import AnalyzingPage  from './pages/AnalyzingPage'
import ResultsPage    from './pages/ResultsPage'
import { useTheme }   from './hooks/useTheme'
import { api }        from './api/client'
import type { AnalyzeResponse, HistoryEntry, UploadResponse, WorkflowStep } from './types'

const HISTORY_KEY = 'orbit_analysis_history'

function loadHistory(): HistoryEntry[] {
  try { return JSON.parse(localStorage.getItem(HISTORY_KEY) ?? '[]') }
  catch { return [] }
}

function persistHistory(entries: HistoryEntry[]) {
  localStorage.setItem(HISTORY_KEY, JSON.stringify(entries.slice(0, 30)))
}

// ── App ─────────────────────────────────────────────────────────────────────

export default function App() {
  useTheme() // initialise dark/light class on <html>

  const [step,     setStep]     = useState<WorkflowStep>('upload')
  const [upload,   setUpload]   = useState<UploadResponse | null>(null)
  const [filename, setFilename] = useState('')
  const [result,   setResult]   = useState<AnalyzeResponse | null>(null)
  const [history,  setHistory]  = useState<HistoryEntry[]>(loadHistory)
  const [restoring, setRestoring] = useState(false)

  // Called when upload completes → go to preview
  const handleUploaded = (data: UploadResponse, file: File) => {
    setUpload(data)
    setFilename(file.name)
    setStep('preview')
  }

  // Called when analysis finishes → save to history + go to results
  const handleAnalyzed = useCallback((res: AnalyzeResponse, fname: string) => {
    setResult(res)
    setStep('results')

    const entry: HistoryEntry = {
      report_id:    res.report_id,
      filename:     fname,
      analyzed_at:  new Date().toISOString(),
      health_score: res.analysis.health_score ?? null,
      risk_7d:      res.analysis.risk?.days_7  ?? null,
      fault:        res.analysis.fault          ?? null,
      severity:     res.analysis.severity       ?? null,
    }

    setHistory(prev => {
      const updated = [entry, ...prev.filter(h => h.report_id !== entry.report_id)]
      persistHistory(updated)
      return updated
    })
  }, [])

  // Restore a previous analysis from history
  const handleOpenHistory = useCallback(async (entry: HistoryEntry) => {
    setRestoring(true)
    try {
      const detail = await api.getReport(entry.report_id)
      const res: AnalyzeResponse = {
        report_id:    detail.report_id,
        status:       detail.status,
        analysis:     detail.analysis,
        ai_narrative: detail.ai_narrative,
      }
      setResult(res)
      setFilename(detail.filename)
      setUpload(null)
      setStep('results')
    } catch {
      alert("Impossible de charger cette analyse. Le rapport n'existe peut-être plus sur le serveur.")
    } finally {
      setRestoring(false)
    }
  }, [])

  // Delete a history entry
  const handleDeleteHistory = useCallback((reportId: string) => {
    setHistory(prev => {
      const updated = prev.filter(h => h.report_id !== reportId)
      persistHistory(updated)
      return updated
    })
    api.deleteReport(reportId).catch(() => {/* best-effort */})
  }, [])

  const reset = () => {
    setStep('upload')
    setUpload(null)
    setResult(null)
    setFilename('')
  }

  return (
    <div className="min-h-screen flex flex-col bg-gray-50 dark:bg-slate-950 transition-colors duration-300">
      {/* ── Header ──────────────────────────────────────────────────────── */}
      <header className="border-b border-gray-200 dark:border-slate-800 bg-white/80 dark:bg-slate-900/80 backdrop-blur sticky top-0 z-20">
        <div className="max-w-6xl mx-auto px-4 py-3 flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center shrink-0">
            <Cpu className="w-4 h-4 text-white" />
          </div>
          <div>
            <h1 className="font-bold text-gray-900 dark:text-white text-sm leading-none">ORBIT AI</h1>
            <p className="text-[10px] text-gray-500 dark:text-slate-400 leading-none">Copilote Industriel</p>
          </div>

          <div className="ml-auto flex items-center gap-3">
            <span className="hidden sm:flex items-center gap-1.5 text-xs text-gray-500 dark:text-slate-500">
              <span className="w-2 h-2 rounded-full bg-green-500" />
              Connecté
            </span>

            {/* History shortcut (visible when not on upload page) */}
            {step !== 'upload' && (
              <button
                onClick={reset}
                className="flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-lg
                           bg-gray-100 dark:bg-slate-800 text-gray-600 dark:text-slate-300
                           hover:bg-gray-200 dark:hover:bg-slate-700 transition-colors"
              >
                <History className="w-3.5 h-3.5" />
                Importer
              </button>
            )}

            <ThemeToggle />
          </div>
        </div>
      </header>

      {/* ── Step indicator ───────────────────────────────────────────────── */}
      <div className="border-b border-gray-200 dark:border-slate-800 bg-white/50 dark:bg-slate-900/50">
        <div className="max-w-6xl mx-auto px-4 py-5">
          <StepIndicator current={step} />
        </div>
      </div>

      {/* ── Main content ─────────────────────────────────────────────────── */}
      <main className="flex-1 max-w-6xl mx-auto w-full px-4 py-8">
        {step === 'upload' && (
          <UploadPage
            onUploaded={handleUploaded}
            history={history}
            onOpenHistory={handleOpenHistory}
            onDeleteHistory={handleDeleteHistory}
            restoring={restoring}
          />
        )}

        {step === 'preview' && upload && (
          <PreviewPage
            upload={upload}
            onAnalyzed={(res) => handleAnalyzed(res, filename)}
            onClear={reset}
          />
        )}

        {step === 'analyzing' && <AnalyzingPage />}

        {step === 'results' && result && (
          <ResultsPage result={result} filename={filename} onReset={reset} />
        )}
      </main>

      {/* ── Footer ───────────────────────────────────────────────────────── */}
      <footer className="border-t border-gray-200 dark:border-slate-800 py-3 text-center text-xs text-gray-400 dark:text-slate-600">
        ORBIT AI Industrial Copilot — Plateforme de Maintenance Prédictive
      </footer>

      {/* ── Chatbot widget (floating, global) ───────────────────────────── */}
      <ChatWidget analysisContext={result} filename={filename} />
    </div>
  )
}
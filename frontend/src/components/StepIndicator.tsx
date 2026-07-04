import { Upload, Table, Cpu, BarChart3, CheckCircle } from 'lucide-react'
import clsx from 'clsx'
import type { WorkflowStep } from '../types'

const STEPS: { key: WorkflowStep; label: string; icon: React.ElementType }[] = [
  { key: 'upload',    label: 'Importer',   icon: Upload    },
  { key: 'preview',   label: 'Aperçu',     icon: Table     },
  { key: 'analyzing', label: 'Analyse',    icon: Cpu       },
  { key: 'results',   label: 'Résultats',  icon: BarChart3 },
]

const ORDER: WorkflowStep[] = ['upload', 'preview', 'analyzing', 'results']

export default function StepIndicator({ current }: { current: WorkflowStep }) {
  // History page: show as if on results step
  const displayStep = current === 'history' ? 'results' : current
  const currentIdx  = ORDER.indexOf(displayStep)

  return (
    <div className="flex items-center gap-0 w-full max-w-3xl mx-auto">
      {STEPS.map(({ key, label, icon: Icon }, idx) => {
        const done   = idx < currentIdx
        const active = idx === currentIdx
        const future = idx > currentIdx
        const isLast = idx === STEPS.length - 1

        return (
          <div key={key} className="flex items-center flex-1">
            <div className="flex flex-col items-center gap-1.5 min-w-[72px]">
              <div className={clsx(
                'w-10 h-10 rounded-full flex items-center justify-center transition-all duration-300',
                done   && 'bg-green-500 text-white',
                active && 'bg-blue-600 text-white ring-4 ring-blue-600/30',
                future && 'bg-gray-200 text-gray-400 dark:bg-slate-700 dark:text-slate-500',
              )}>
                {done
                  ? <CheckCircle className="w-5 h-5" />
                  : <Icon className="w-5 h-5" />
                }
              </div>
              <span className={clsx(
                'text-xs font-medium text-center leading-tight',
                done   && 'text-green-600 dark:text-green-400',
                active && 'text-blue-600 dark:text-blue-400',
                future && 'text-gray-400 dark:text-slate-500',
              )}>
                {label}
              </span>
            </div>
            {!isLast && (
              <div className={clsx(
                'flex-1 h-0.5 mx-2 mt-[-18px] transition-all duration-300',
                idx < currentIdx
                  ? 'bg-green-500'
                  : 'bg-gray-200 dark:bg-slate-700',
              )} />
            )}
          </div>
        )
      })}
    </div>
  )
}

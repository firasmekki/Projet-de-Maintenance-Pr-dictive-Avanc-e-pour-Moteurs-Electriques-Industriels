import React, { useCallback, useRef, useState } from 'react'
import { Upload, FileSpreadsheet, FileJson, FileText, X } from 'lucide-react'
import clsx from 'clsx'

interface Props {
  onFile:    (file: File) => void
  disabled?: boolean
}

const ACCEPTED = ['.csv', '.xlsx', '.xls', '.json']
const ACCEPT   = ACCEPTED.join(',')

function fileIcon(name: string) {
  const ext = name.split('.').pop()?.toLowerCase()
  if (ext === 'json') return FileJson
  if (ext === 'csv')  return FileText
  return FileSpreadsheet
}

function formatBytes(b: number) {
  if (b < 1024)        return `${b} B`
  if (b < 1024 * 1024) return `${(b / 1024).toFixed(1)} Ko`
  return `${(b / 1024 / 1024).toFixed(2)} Mo`
}

export default function DropZone({ onFile, disabled }: Props) {
  const [dragging, setDragging] = useState(false)
  const [selected, setSelected] = useState<File | null>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  const pick = useCallback((file: File) => {
    setSelected(file)
    onFile(file)
  }, [onFile])

  const onDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setDragging(false)
    const file = e.dataTransfer.files[0]
    if (file) pick(file)
  }, [pick])

  const onChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) pick(file)
  }

  const clear = () => {
    setSelected(null)
    if (inputRef.current) inputRef.current.value = ''
  }

  const Icon = selected ? fileIcon(selected.name) : Upload

  return (
    <div className="w-full">
      <div
        onDragOver={e => { e.preventDefault(); setDragging(true) }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
        onClick={() => !disabled && !selected && inputRef.current?.click()}
        className={clsx(
          'relative border-2 border-dashed rounded-2xl p-10 flex flex-col items-center justify-center gap-4',
          'transition-all duration-200 select-none',
          dragging  && 'border-blue-400 bg-blue-50 dark:bg-blue-950/30 cursor-copy',
          !dragging && !selected && 'border-gray-300 dark:border-slate-600 hover:border-blue-400 hover:bg-blue-50/50 dark:hover:bg-slate-800/50 cursor-pointer',
          selected  && 'border-green-500 bg-green-50 dark:bg-green-950/20 cursor-default',
          disabled  && 'opacity-50 cursor-not-allowed',
        )}
      >
        <input ref={inputRef} type="file" accept={ACCEPT} className="sr-only" onChange={onChange} disabled={disabled} />

        <div className={clsx(
          'w-16 h-16 rounded-2xl flex items-center justify-center',
          selected ? 'bg-green-100 dark:bg-green-900/50' : 'bg-gray-100 dark:bg-slate-700/60',
        )}>
          <Icon className={clsx('w-8 h-8', selected ? 'text-green-600 dark:text-green-400' : 'text-blue-500 dark:text-blue-400')} />
        </div>

        {selected ? (
          <div className="text-center">
            <p className="font-semibold text-green-700 dark:text-green-300 text-lg">{selected.name}</p>
            <p className="text-gray-500 dark:text-slate-400 text-sm mt-1">{formatBytes(selected.size)}</p>
          </div>
        ) : (
          <div className="text-center">
            <p className="font-semibold text-gray-700 dark:text-slate-200 text-lg">
              Glissez-déposez votre dataset ici
            </p>
            <p className="text-gray-500 dark:text-slate-400 text-sm mt-1">ou cliquez pour parcourir</p>
            <div className="flex items-center gap-2 mt-3 justify-center flex-wrap">
              {ACCEPTED.map(ext => (
                <span key={ext} className="badge bg-gray-100 dark:bg-slate-700 text-gray-600 dark:text-slate-300 uppercase">
                  {ext.replace('.', '')}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>

      {selected && (
        <button
          onClick={clear}
          className="mt-2 flex items-center gap-1 text-sm text-gray-500 dark:text-slate-400 hover:text-red-600 dark:hover:text-red-400 transition-colors"
        >
          <X className="w-4 h-4" /> Supprimer le fichier
        </button>
      )}
    </div>
  )
}

import { useState, useMemo } from 'react'
import { ChevronUp, ChevronDown, ChevronsUpDown, Search, ChevronLeft, ChevronRight } from 'lucide-react'
import clsx from 'clsx'

interface Props {
  columns:   string[]
  rows:      Record<string, unknown>[]
  pageSize?: number
}

type SortDir = 'asc' | 'desc' | null

export default function DataTable({ columns, rows, pageSize = 20 }: Props) {
  const [search,    setSearch]    = useState('')
  const [sortCol,   setSortCol]   = useState<string | null>(null)
  const [sortDir,   setSortDir]   = useState<SortDir>(null)
  const [page,      setPage]      = useState(0)
  const [colFilter, setColFilter] = useState<Record<string, string>>({})

  const filtered = useMemo(() => {
    let data = rows
    if (search.trim()) {
      const q = search.toLowerCase()
      data = data.filter(r => columns.some(c => String(r[c] ?? '').toLowerCase().includes(q)))
    }
    for (const [col, val] of Object.entries(colFilter)) {
      if (val.trim()) {
        const q = val.toLowerCase()
        data = data.filter(r => String(r[col] ?? '').toLowerCase().includes(q))
      }
    }
    return data
  }, [rows, search, colFilter, columns])

  const sorted = useMemo(() => {
    if (!sortCol || !sortDir) return filtered
    return [...filtered].sort((a, b) => {
      const va = a[sortCol], vb = b[sortCol]
      const na = Number(va), nb = Number(vb)
      const compare = !isNaN(na) && !isNaN(nb)
        ? na - nb
        : String(va ?? '').localeCompare(String(vb ?? ''))
      return sortDir === 'asc' ? compare : -compare
    })
  }, [filtered, sortCol, sortDir])

  const totalPages = Math.max(1, Math.ceil(sorted.length / pageSize))
  const paginated  = sorted.slice(page * pageSize, (page + 1) * pageSize)

  const toggleSort = (col: string) => {
    if (sortCol !== col) { setSortCol(col); setSortDir('asc'); setPage(0); return }
    if (sortDir === 'asc') { setSortDir('desc'); return }
    setSortCol(null); setSortDir(null)
  }

  const SortIcon = ({ col }: { col: string }) => {
    if (sortCol !== col) return <ChevronsUpDown className="w-3.5 h-3.5 opacity-40" />
    return sortDir === 'asc'
      ? <ChevronUp   className="w-3.5 h-3.5 text-blue-500" />
      : <ChevronDown className="w-3.5 h-3.5 text-blue-500" />
  }

  const cellValue = (val: unknown) => {
    if (val === null || val === undefined) return <span className="text-gray-300 dark:text-slate-600">—</span>
    const str = String(val)
    const num = parseFloat(str)
    if (!isNaN(num) && str.trim() !== '') return <span className="tabular-nums">{num.toFixed(3)}</span>
    return str
  }

  return (
    <div className="flex flex-col gap-3">
      {/* Global search */}
      <div className="flex items-center gap-3">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 dark:text-slate-400" />
          <input
            value={search}
            onChange={e => { setSearch(e.target.value); setPage(0) }}
            placeholder="Rechercher dans toutes les colonnes…"
            className="w-full pl-9 pr-4 py-2 text-sm rounded-lg
                       bg-gray-100 border border-gray-300 text-gray-900 placeholder-gray-400
                       focus:outline-none focus:border-blue-500
                       dark:bg-slate-700 dark:border-slate-600 dark:text-slate-100 dark:placeholder-slate-400"
          />
        </div>
        <span className="text-sm text-gray-500 dark:text-slate-400">
          {filtered.length.toLocaleString()} / {rows.length.toLocaleString()} lignes
        </span>
      </div>

      {/* Table */}
      <div className="overflow-x-auto rounded-xl border border-gray-200 dark:border-slate-700">
        <table className="min-w-full text-sm">
          <thead>
            <tr className="bg-gray-50 dark:bg-slate-900 border-b border-gray-200 dark:border-slate-700">
              {columns.map(col => (
                <th
                  key={col}
                  onClick={() => toggleSort(col)}
                  className="px-4 py-3 text-left text-xs font-semibold
                             text-gray-600 dark:text-slate-300
                             uppercase tracking-wide cursor-pointer select-none whitespace-nowrap
                             hover:text-blue-600 dark:hover:text-blue-300"
                >
                  <span className="flex items-center gap-1.5">
                    {col} <SortIcon col={col} />
                  </span>
                </th>
              ))}
            </tr>
            <tr className="bg-gray-50/60 dark:bg-slate-900/60 border-b border-gray-200/50 dark:border-slate-700/50">
              {columns.map(col => (
                <th key={col} className="px-3 py-1.5">
                  <input
                    value={colFilter[col] ?? ''}
                    onChange={e => {
                      setColFilter(prev => ({ ...prev, [col]: e.target.value }))
                      setPage(0)
                    }}
                    placeholder="Filtrer…"
                    className="w-full px-2 py-1 text-xs rounded
                               bg-white border border-gray-300 text-gray-700 placeholder-gray-400
                               focus:outline-none focus:border-blue-500
                               dark:bg-slate-800 dark:border-slate-700 dark:text-slate-200 dark:placeholder-slate-500"
                  />
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {paginated.map((row, ri) => (
              <tr
                key={ri}
                className={clsx(
                  'border-b border-gray-100 dark:border-slate-700/50 transition-colors',
                  'hover:bg-blue-50/50 dark:hover:bg-slate-700/30',
                  ri % 2 === 0
                    ? 'bg-white dark:bg-slate-800/30'
                    : 'bg-gray-50/30 dark:bg-slate-800/10',
                )}
              >
                {columns.map(col => (
                  <td key={col} className="px-4 py-2.5 text-gray-700 dark:text-slate-300 whitespace-nowrap">
                    {cellValue(row[col])}
                  </td>
                ))}
              </tr>
            ))}
            {paginated.length === 0 && (
              <tr>
                <td colSpan={columns.length} className="px-4 py-8 text-center text-gray-400 dark:text-slate-500">
                  Aucune ligne correspondante
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      <div className="flex items-center justify-between text-sm text-gray-500 dark:text-slate-400">
        <span>
          Page {page + 1} sur {totalPages} — lignes {page * pageSize + 1}–
          {Math.min((page + 1) * pageSize, sorted.length)} sur {sorted.length}
        </span>
        <div className="flex items-center gap-1">
          <button onClick={() => setPage(0)}                                      disabled={page === 0}           className="px-2 py-1 rounded hover:bg-gray-100 dark:hover:bg-slate-700 disabled:opacity-30">«</button>
          <button onClick={() => setPage(p => Math.max(0, p - 1))}               disabled={page === 0}           className="px-2 py-1 rounded hover:bg-gray-100 dark:hover:bg-slate-700 disabled:opacity-30 flex items-center gap-1">
            <ChevronLeft className="w-4 h-4" /> Préc.
          </button>
          <button onClick={() => setPage(p => Math.min(totalPages - 1, p + 1))} disabled={page >= totalPages - 1} className="px-2 py-1 rounded hover:bg-gray-100 dark:hover:bg-slate-700 disabled:opacity-30 flex items-center gap-1">
            Suiv. <ChevronRight className="w-4 h-4" />
          </button>
          <button onClick={() => setPage(totalPages - 1)}                        disabled={page >= totalPages - 1} className="px-2 py-1 rounded hover:bg-gray-100 dark:hover:bg-slate-700 disabled:opacity-30">»</button>
        </div>
      </div>
    </div>
  )
}

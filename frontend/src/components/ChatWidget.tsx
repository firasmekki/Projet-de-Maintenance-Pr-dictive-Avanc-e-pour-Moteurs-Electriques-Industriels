import { useState, useRef, useEffect, useCallback } from 'react'
import { MessageCircle, X, Send, Bot, User, Loader2, ChevronDown, Cpu } from 'lucide-react'
import clsx from 'clsx'
import type { AnalyzeResponse } from '../types'
import { FAULT_FR } from '../types'

interface Props {
  analysisContext?: AnalyzeResponse | null
  filename?:        string
}

interface Message {
  role:       'user' | 'assistant'
  content:    string
  streaming?: boolean
}

const SUGGESTED_WITH_CTX = [
  "Pourquoi ce moteur consomme-t-il plus ?",
  "Quel est le risque si je ne fais rien ?",
  "Donne-moi un plan d'action pour 30 jours",
  "Explique le défaut détecté en détail",
]

const SUGGESTED_NO_CTX = [
  "Qu'est-ce qu'un défaut de roulement ?",
  "Expliquez la norme ISO 10816",
  "Comment détecter un désalignement ?",
  "Quels capteurs surveiller en priorité ?",
]

export default function ChatWidget({ analysisContext, filename }: Props) {
  const [open,     setOpen]     = useState(false)
  const [messages, setMessages] = useState<Message[]>([])
  const [input,    setInput]    = useState('')
  const [loading,  setLoading]  = useState(false)
  const bottomRef  = useRef<HTMLDivElement>(null)
  const inputRef   = useRef<HTMLInputElement>(null)
  const abortRef   = useRef<AbortController | null>(null)

  // Auto-scroll
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // Focus input when open
  useEffect(() => {
    if (open) setTimeout(() => inputRef.current?.focus(), 150)
  }, [open])

  const sendMessage = useCallback(async (text: string) => {
    const content = text.trim()
    if (!content || loading) return

    setInput('')
    const userMsg: Message = { role: 'user', content }
    setMessages(prev => [...prev, userMsg])
    setLoading(true)

    // Placeholder assistant message
    setMessages(prev => [...prev, { role: 'assistant', content: '', streaming: true }])

    abortRef.current = new AbortController()

    try {
      const history = messages.map(m => ({ role: m.role, content: m.content }))
      history.push({ role: 'user', content })

      const res = await fetch('/api/v1/chat', {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        signal:  abortRef.current.signal,
        body: JSON.stringify({
          message:          content,
          history:          messages.map(m => ({ role: m.role, content: m.content })),
          analysis_context: analysisContext
            ? { analysis: analysisContext.analysis }
            : null,
          filename: filename ?? null,
        }),
      })

      if (!res.ok) throw new Error(`HTTP ${res.status}`)

      const reader  = res.body?.getReader()
      const decoder = new TextDecoder()
      if (!reader) throw new Error('No body')

      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() ?? ''

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue
          try {
            const data = JSON.parse(line.slice(6))
            if (data.token) {
              setMessages(prev => {
                const updated = [...prev]
                const last    = updated[updated.length - 1]
                if (last?.role === 'assistant') {
                  updated[updated.length - 1] = { ...last, content: last.content + data.token }
                }
                return updated
              })
            }
            if (data.done) {
              setMessages(prev => {
                const updated = [...prev]
                if (updated[updated.length - 1]?.role === 'assistant') {
                  updated[updated.length - 1] = { ...updated[updated.length - 1], streaming: false }
                }
                return updated
              })
            }
          } catch { /* ignore parse errors */ }
        }
      }
    } catch (err: unknown) {
      if ((err as Error).name === 'AbortError') return
      setMessages(prev => {
        const updated = [...prev]
        updated[updated.length - 1] = {
          role:      'assistant',
          content:   "Désolé, une erreur s'est produite. Vérifiez que le backend est en ligne.",
          streaming: false,
        }
        return updated
      })
    } finally {
      setLoading(false)
      setMessages(prev => {
        const updated = [...prev]
        if (updated[updated.length - 1]?.streaming) {
          updated[updated.length - 1] = { ...updated[updated.length - 1], streaming: false }
        }
        return updated
      })
    }
  }, [messages, loading, analysisContext, filename])

  const onKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage(input)
    }
  }

  const clear = () => {
    abortRef.current?.abort()
    setMessages([])
    setLoading(false)
  }

  const suggested = analysisContext ? SUGGESTED_WITH_CTX : SUGGESTED_NO_CTX

  const fault  = analysisContext?.analysis.fault
  const health = analysisContext?.analysis.health_score

  return (
    <>
      {/* ── Floating button ──────────────────────────────────────────── */}
      <button
        onClick={() => setOpen(o => !o)}
        className={clsx(
          'fixed bottom-6 right-6 z-50 w-14 h-14 rounded-full shadow-2xl',
          'flex items-center justify-center transition-all duration-300',
          'bg-blue-600 hover:bg-blue-500 text-white',
          open && 'rotate-90 scale-95',
        )}
        title="Chatbot ORBIT AI"
      >
        {open
          ? <X className="w-6 h-6" />
          : <>
              <MessageCircle className="w-6 h-6" />
              {messages.length === 0 && (
                <span className="absolute -top-1 -right-1 w-4 h-4 rounded-full bg-green-400 text-[9px] font-bold flex items-center justify-center text-green-900">
                  IA
                </span>
              )}
            </>
        }
      </button>

      {/* ── Chat panel ───────────────────────────────────────────────── */}
      <div className={clsx(
        'fixed bottom-24 right-6 z-50 flex flex-col',
        'w-[360px] max-h-[600px] rounded-2xl shadow-2xl overflow-hidden',
        'bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-700',
        'transition-all duration-300 origin-bottom-right',
        open ? 'opacity-100 scale-100 pointer-events-auto' : 'opacity-0 scale-95 pointer-events-none',
      )}>

        {/* Header */}
        <div className="flex items-center gap-3 px-4 py-3 bg-blue-600 text-white shrink-0">
          <div className="w-8 h-8 rounded-full bg-blue-500 flex items-center justify-center">
            <Cpu className="w-4 h-4" />
          </div>
          <div className="flex-1 min-w-0">
            <p className="font-bold text-sm leading-none">ORBIT AI</p>
            <p className="text-[11px] text-blue-200 leading-none mt-0.5">Expert Maintenance Industrielle</p>
          </div>
          <button onClick={clear} title="Effacer la conversation" className="text-blue-200 hover:text-white transition-colors">
            <ChevronDown className="w-4 h-4" />
          </button>
        </div>

        {/* Context badge */}
        {analysisContext && (
          <div className="flex items-center gap-2 px-4 py-2 bg-green-50 dark:bg-green-900/20 border-b border-green-200 dark:border-green-800 shrink-0">
            <span className="w-2 h-2 rounded-full bg-green-500" />
            <span className="text-xs text-green-700 dark:text-green-300 font-medium">
              Contexte actif — {filename ?? 'Dataset'}
              {fault && ` · ${FAULT_FR[fault] ?? fault}`}
              {health != null && ` · Santé ${health}/100`}
            </span>
          </div>
        )}

        {/* Messages */}
        <div className="flex-1 overflow-y-auto px-4 py-4 flex flex-col gap-3 min-h-0">
          {messages.length === 0 && (
            <div className="flex flex-col items-center gap-4 py-4">
              <div className="w-14 h-14 rounded-full bg-blue-100 dark:bg-blue-900/40 flex items-center justify-center">
                <Bot className="w-7 h-7 text-blue-600 dark:text-blue-400" />
              </div>
              <p className="text-sm text-gray-600 dark:text-slate-400 text-center leading-relaxed">
                Posez vos questions sur les moteurs industriels, les défauts, les risques ou la maintenance.
              </p>
              <div className="flex flex-col gap-2 w-full">
                {suggested.map(q => (
                  <button
                    key={q}
                    onClick={() => sendMessage(q)}
                    className="text-left text-xs px-3 py-2 rounded-lg
                               bg-gray-50 dark:bg-slate-800 border border-gray-200 dark:border-slate-700
                               text-gray-700 dark:text-slate-300
                               hover:border-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/20
                               transition-colors"
                  >
                    {q}
                  </button>
                ))}
              </div>
            </div>
          )}

          {messages.map((msg, i) => (
            <div key={i} className={clsx('flex gap-2', msg.role === 'user' ? 'justify-end' : 'justify-start')}>
              {msg.role === 'assistant' && (
                <div className="w-6 h-6 rounded-full bg-blue-600 flex items-center justify-center shrink-0 mt-0.5">
                  <Bot className="w-3.5 h-3.5 text-white" />
                </div>
              )}
              <div className={clsx(
                'max-w-[82%] rounded-2xl px-3.5 py-2.5 text-sm leading-relaxed',
                msg.role === 'user'
                  ? 'bg-blue-600 text-white rounded-br-sm'
                  : 'bg-gray-100 dark:bg-slate-800 text-gray-800 dark:text-slate-200 rounded-bl-sm',
              )}>
                {msg.content
                  ? msg.content.split('\n').map((line, li) => {
                      const bold = line.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
                      return (
                        <p
                          key={li}
                          dangerouslySetInnerHTML={{ __html: bold }}
                          className={li > 0 ? 'mt-1' : ''}
                        />
                      )
                    })
                  : msg.streaming && (
                      <span className="flex gap-1">
                        {[0, 1, 2].map(d => (
                          <span
                            key={d}
                            className="w-1.5 h-1.5 rounded-full bg-blue-400 animate-bounce"
                            style={{ animationDelay: `${d * 150}ms` }}
                          />
                        ))}
                      </span>
                    )
                }
                {msg.streaming && msg.content && (
                  <span className="inline-block w-0.5 h-3.5 bg-blue-500 ml-0.5 animate-pulse align-middle" />
                )}
              </div>
              {msg.role === 'user' && (
                <div className="w-6 h-6 rounded-full bg-gray-200 dark:bg-slate-700 flex items-center justify-center shrink-0 mt-0.5">
                  <User className="w-3.5 h-3.5 text-gray-600 dark:text-slate-400" />
                </div>
              )}
            </div>
          ))}
          <div ref={bottomRef} />
        </div>

        {/* Input */}
        <div className="px-3 py-3 border-t border-gray-200 dark:border-slate-700 bg-white dark:bg-slate-900 shrink-0">
          <div className="flex items-center gap-2 bg-gray-50 dark:bg-slate-800 rounded-xl px-3 py-2 border border-gray-200 dark:border-slate-700 focus-within:border-blue-500">
            <input
              ref={inputRef}
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={onKeyDown}
              placeholder="Posez votre question…"
              disabled={loading}
              className="flex-1 bg-transparent text-sm text-gray-800 dark:text-slate-200 placeholder-gray-400 dark:placeholder-slate-500 outline-none"
            />
            <button
              onClick={() => sendMessage(input)}
              disabled={!input.trim() || loading}
              className="w-7 h-7 rounded-lg bg-blue-600 hover:bg-blue-500 disabled:opacity-40 flex items-center justify-center transition-colors"
            >
              {loading
                ? <Loader2 className="w-3.5 h-3.5 text-white animate-spin" />
                : <Send    className="w-3.5 h-3.5 text-white" />
              }
            </button>
          </div>
          <p className="text-[10px] text-gray-400 dark:text-slate-600 text-center mt-1.5">
            ORBIT AI · Expert Maintenance Industrielle
          </p>
        </div>
      </div>
    </>
  )
}

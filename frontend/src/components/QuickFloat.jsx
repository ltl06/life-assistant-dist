import { useState, useEffect, useRef } from 'react'
import { api } from '../utils/api'
import { Zap, X, CheckCircle } from 'lucide-react'

export default function QuickFloat() {
  const [open, setOpen] = useState(false)
  const [input, setInput] = useState('')
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const inputRef = useRef(null)

  useEffect(() => {
    const handler = (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault()
        setOpen(true)
        setTimeout(() => inputRef.current?.focus(), 50)
      }
      if (e.key === 'Escape') setOpen(false)
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [])

  async function handleSubmit(e) {
    e.preventDefault()
    if (!input.trim()) return
    setLoading(true)
    setResult(null)
    try {
      const res = await api.quick.add(input)
      setResult(res)
      if (res.success) {
        setTimeout(() => { setOpen(false); setInput(''); setResult(null) }, 2000)
      }
    } catch {} finally { setLoading(false) }
  }

  const EXAMPLES = [
    '记账 35 午餐',
    '走了 8000 步',
    '体重 65',
    '睡了 7.5 小时',
  ]

  if (!open) {
    return (
      <button
        onClick={() => { setOpen(true); setTimeout(() => inputRef.current?.focus(), 50) }}
        className="fixed bottom-6 right-6 w-14 h-14 rounded-full bg-brand-500 hover:bg-brand-600 text-white shadow-lg
          flex items-center justify-center z-40 transition-all hover:scale-105 active:scale-95"
        title="快捷记录 (Ctrl+K)"
      >
        <Zap size={22} />
      </button>
    )
  }

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center pt-24 px-4">
      <div className="absolute inset-0 bg-black/30 backdrop-blur-sm" onClick={() => setOpen(false)} />
      <div className="relative w-full max-w-lg bg-white rounded-2xl shadow-2xl overflow-hidden">
        <form onSubmit={handleSubmit} className="flex items-center gap-3 p-4 border-b">
          <Zap size={20} className="text-brand-500 shrink-0" />
          <input
            ref={inputRef}
            className="flex-1 text-lg outline-none placeholder-gray-400"
            placeholder="记账、步数、体重、睡眠..."
            value={input}
            onChange={e => setInput(e.target.value)}
            autoFocus
          />
          {loading ? (
            <div className="w-5 h-5 border-2 border-brand-500 border-t-transparent rounded-full animate-spin" />
          ) : (
            <button type="submit" className="text-brand-500 font-medium text-sm">发送</button>
          )}
        </form>

        {result && (
          <div className={`px-4 py-3 text-sm flex items-center gap-2 ${result.success ? 'bg-green-50 text-green-700' : 'bg-amber-50 text-amber-700'}`}>
            <CheckCircle size={16} />
            {result.message}
          </div>
        )}

        {!result && (
          <div className="p-4">
            <p className="text-xs text-gray-400 mb-3">试试这些：</p>
            <div className="flex flex-wrap gap-2">
              {EXAMPLES.map((ex) => (
                <button key={ex} type="button"
                  onClick={() => { setInput(ex); inputRef.current?.focus() }}
                  className="px-3 py-1.5 bg-gray-100 hover:bg-brand-50 text-gray-600 hover:text-brand-600 rounded-lg text-sm transition-colors">
                  {ex}
                </button>
              ))}
            </div>
            <p className="text-xs text-gray-400 mt-3">
              支持：记账、步数、体重、睡眠 — 按 Enter 发送
            </p>
          </div>
        )}

        <button onClick={() => setOpen(false)} className="absolute top-3 right-3 text-gray-400 hover:text-gray-600">
          <X size={18} />
        </button>
      </div>
    </div>
  )
}

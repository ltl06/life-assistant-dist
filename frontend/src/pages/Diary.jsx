import { useEffect, useState } from 'react'
import { api } from '../utils/api'
import { BookOpen, Plus, ChevronLeft, Trash2, Edit2, Search, Calendar } from 'lucide-react'

const MOOD_OPTIONS = ['😊', '😃', '😐', '😔', '😡', '🤔', '😴', '🥰']
const MOOD_LABELS = {
  '😊': '开心', '😃': '愉悦', '😐': '平静', '😔': '低落', '😡': '烦躁',
  '🤔': '思考中', '😴': '疲惫', '🥰': '满足',
}

function formatDate(d) {
  return new Date(d).toLocaleDateString('zh-CN', { weekday: 'long', month: 'long', day: 'numeric' })
}

export default function Diary() {
  const [entries, setEntries] = useState([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [editing, setEditing] = useState(null)
  const [form, setForm] = useState({ title: '', content: '', mood: '', tags: '' })
  const [search, setSearch] = useState('')
  const [stats, setStats] = useState(null)
  const [expanded, setExpanded] = useState(null)

  useEffect(() => { loadData() }, [])

  async function loadData() {
    try {
      const [entries, stats] = await Promise.all([
        api.diary.list({ limit: 90 }),
        api.diary.stats(90),
      ])
      setEntries(entries)
      setStats(stats)
    } catch {} finally { setLoading(false) }
  }

  async function handleSubmit(e) {
    e.preventDefault()
    try {
      if (editing) {
        await api.diary.update(editing.id, form)
      } else {
        await api.diary.create(form)
      }
      setShowForm(false)
      setEditing(null)
      setForm({ title: '', content: '', mood: '', tags: '' })
      loadData()
    } catch {}
  }

  async function handleDelete(id) {
    if (!confirm('确定删除这篇日记？')) return
    await api.diary.delete(id)
    setEntries(entries.filter(e => e.id !== id))
  }

  function openEdit(entry) {
    setEditing(entry)
    setForm({ title: entry.title || '', content: entry.content, mood: entry.mood || '', tags: entry.tags || '' })
    setShowForm(true)
  }

  const filtered = entries.filter(e =>
    !search || (e.content || '').includes(search) || (e.title || '').includes(search)
  )

  const grouped = {}
  filtered.forEach(e => {
    const key = (e.date || '').slice(0, 7)
    if (!grouped[key]) grouped[key] = []
    grouped[key].push(e)
  })

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <BookOpen className="w-7 h-7 text-indigo-500" /> 日记本
          </h1>
          <p className="text-gray-500 mt-1">记录生活，留住回忆</p>
        </div>
        <button onClick={() => { setShowForm(true); setEditing(null); setForm({ title: '', content: '', mood: '', tags: '' }) }}
          className="btn-primary flex items-center gap-2">
          <Plus size={18} /> 写日记
        </button>
      </div>

      {stats && (
        <div className="grid grid-cols-3 gap-4">
          <div className="card text-center">
            <div className="text-2xl font-bold text-indigo-500">{stats.total_count}</div>
            <div className="stat-label">篇日记</div>
          </div>
          <div className="card text-center">
            <div className="text-2xl font-bold text-amber-500">{stats.streak_days}</div>
            <div className="stat-label">连续记录天数</div>
          </div>
          <div className="card text-center">
            <div className="text-xl font-bold">
              {Object.entries(stats.moods || {}).sort((a, b) => b[1] - a[1])[0]
                ? `${Object.entries(stats.moods || {}).sort((a, b) => b[1] - a[1])[0][0]} 最多`
                : '--'}
            </div>
            <div className="stat-label">常见心情</div>
          </div>
        </div>
      )}

      <div className="relative">
        <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
        <input className="input-field pl-10" placeholder="搜索日记内容..." value={search}
          onChange={e => setSearch(e.target.value)} />
      </div>

      {showForm && (
        <div className="card border-brand-200">
          <h3 className="font-semibold mb-4">{editing ? '编辑日记' : '写日记'}</h3>
          <form onSubmit={handleSubmit} className="space-y-4">
            <input className="input-field" placeholder="标题（可选）" value={form.title}
              onChange={e => setForm({ ...form, title: e.target.value })} />
            <textarea className="input-field" rows={8} placeholder="今天发生了什么？你的感受如何？..."
              value={form.content} onChange={e => setForm({ ...form, content: e.target.value })} required />
            <div className="flex flex-wrap gap-2 items-center">
              <span className="text-sm text-gray-500">心情：</span>
              {MOOD_OPTIONS.map(m => (
                <button key={m} type="button" onClick={() => setForm({ ...form, mood: m })}
                  className={`text-2xl p-2 rounded-xl transition-all ${form.mood === m ? 'bg-brand-50 scale-110' : 'hover:bg-gray-50'}`}
                  title={MOOD_LABELS[m]}>{m}</button>
              ))}
            </div>
            <input className="input-field" placeholder="标签，用逗号分隔，如：工作,心情,日常"
              value={form.tags} onChange={e => setForm({ ...form, tags: e.target.value })} />
            <div className="flex gap-3">
              <button type="submit" className="btn-primary">{editing ? '保存修改' : '发布日记'}</button>
              <button type="button" onClick={() => setShowForm(false)} className="btn-secondary">取消</button>
            </div>
          </form>
        </div>
      )}

      {loading ? <div className="space-y-3">{[1,2,3].map(i => <div key={i} className="h-24 bg-gray-100 rounded-2xl animate-pulse" />)}</div>
        : Object.keys(grouped).length === 0 ? (
          <div className="text-center py-16 text-gray-400">
            <BookOpen size={40} className="mx-auto mb-3 opacity-40" />
            <p>还没有日记，提起笔开始记录吧</p>
          </div>
        ) : Object.entries(grouped).map(([month, monthEntries]) => (
          <div key={month}>
            <div className="text-sm font-semibold text-gray-400 mb-2 flex items-center gap-2">
              <Calendar size={14} /> {month}
            </div>
            <div className="space-y-3">
              {monthEntries.map(entry => (
                <div key={entry.id} className="card">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-sm text-gray-400">{entry.date?.slice(0, 10)}</span>
                        {entry.mood && <span className="text-xl">{entry.mood}</span>}
                        {entry.tags && entry.tags.split(',').map(t => (
                          <span key={t} className="text-xs px-2 py-0.5 bg-indigo-50 text-indigo-600 rounded-full">{t.trim()}</span>
                        ))}
                      </div>
                      {entry.title && <h3 className="font-semibold text-gray-900 mb-1">{entry.title}</h3>}
                      <p className={`text-sm text-gray-600 ${expanded === entry.id ? '' : 'line-clamp-3'}`}>
                        {entry.content}
                      </p>
                      {(entry.content?.length || 0) > 150 && (
                        <button onClick={() => setExpanded(expanded === entry.id ? null : entry.id)}
                          className="text-xs text-brand-500 mt-1 hover:underline">
                          {expanded === entry.id ? '收起' : '展开'}
                        </button>
                      )}
                    </div>
                    <div className="flex gap-2 ml-4 shrink-0">
                      <button onClick={() => openEdit(entry)} className="p-1 text-gray-400 hover:text-brand-500">
                        <Edit2 size={14} />
                      </button>
                      <button onClick={() => handleDelete(entry.id)} className="p-1 text-gray-400 hover:text-red-500">
                        <Trash2 size={14} />
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))
      }
    </div>
  )
}

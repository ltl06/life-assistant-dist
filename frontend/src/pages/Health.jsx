import { useEffect, useState } from 'react'
import { api } from '../utils/api'
import { Heart, Plus, Activity, Moon, Footprints, Smile } from 'lucide-react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'

const MOOD_OPTIONS = ['😊', '😃', '😐', '😔', '😡']
const MOOD_LABELS = { '😊': '很开心', '😃': '开心', '😐': '一般', '😔': '有点低落', '😡': '生气' }

export default function Health() {
  const [records, setRecords] = useState([])
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState({ weight: '', steps: '', sleep_hours: '', mood: '', notes: '' })

  useEffect(() => { loadData() }, [])
  async function loadData() {
    try {
      const [recs, st] = await Promise.all([api.health.list({ limit: 30 }), api.health.stats(30)])
      setRecords(recs); setStats(st)
    } catch {} finally { setLoading(false) }
  }

  async function handleSubmit(e) {
    e.preventDefault()
    try {
      await api.health.create({
        weight: form.weight ? parseFloat(form.weight) : null,
        steps: form.steps ? parseInt(form.steps) : 0,
        sleep_hours: form.sleep_hours ? parseFloat(form.sleep_hours) : null,
        mood: form.mood || null,
        notes: form.notes || null,
      })
      setShowForm(false)
      setForm({ weight: '', steps: '', sleep_hours: '', mood: '', notes: '' })
      loadData()
    } catch {}
  }

  const chartData = [...records].reverse().slice(-14).map((r) => ({
    date: r.date?.slice(5) || '',
    weight: r.weight,
    sleep: r.sleep_hours,
    steps: r.steps,
  }))

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Heart className="w-7 h-7 text-rose-500" /> 健康追踪
          </h1>
          <p className="text-gray-500 mt-1">记录身体数据，养成健康习惯</p>
        </div>
        <button onClick={() => setShowForm(!showForm)} className="btn-primary flex items-center gap-2">
          <Plus size={18} /> 记录今日
        </button>
      </div>

      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="stat-card text-center">
            <div className="text-3xl font-bold text-rose-500">{stats.total_records}</div>
            <div className="stat-label">记录次数</div>
          </div>
          <div className="stat-card text-center">
            <div className="text-3xl font-bold text-indigo-500">{stats.avg_weight ?? '--'}<span className="text-sm font-normal">kg</span></div>
            <div className="stat-label">平均体重</div>
          </div>
          <div className="stat-card text-center">
            <div className="text-3xl font-bold text-violet-500">{stats.avg_sleep ?? '--'}<span className="text-sm font-normal">h</span></div>
            <div className="stat-label">平均睡眠</div>
          </div>
          <div className="stat-card text-center">
            <div className="text-3xl font-bold text-emerald-500">{stats.avg_steps?.toLocaleString() ?? '--'}</div>
            <div className="stat-label">平均步数</div>
          </div>
        </div>
      )}

      {chartData.length > 1 && (
        <div className="card">
          <h2 className="text-lg font-semibold mb-4">体重趋势（最近14天）</h2>
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="date" fontSize={12} />
              <YAxis fontSize={12} domain={['auto', 'auto']} />
              <Tooltip />
              <Line type="monotone" dataKey="weight" stroke="#0ea5e9" strokeWidth={2} dot={{ r: 4 }} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      {showForm && (
        <div className="card border-brand-200">
          <h2 className="text-lg font-semibold mb-4">记录今日健康数据</h2>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-medium text-gray-600 flex items-center gap-1"><Activity size={14} /> 体重 (kg)</label>
                <input className="input-field mt-1" type="number" step="0.1" placeholder="如 65.5" value={form.weight} onChange={(e) => setForm({ ...form, weight: e.target.value })} />
              </div>
              <div>
                <label className="text-sm font-medium text-gray-600 flex items-center gap-1"><Footprints size={14} /> 步数</label>
                <input className="input-field mt-1" type="number" placeholder="如 8000" value={form.steps} onChange={(e) => setForm({ ...form, steps: e.target.value })} />
              </div>
              <div>
                <label className="text-sm font-medium text-gray-600 flex items-center gap-1"><Moon size={14} /> 睡眠时长 (h)</label>
                <input className="input-field mt-1" type="number" step="0.5" placeholder="如 7.5" value={form.sleep_hours} onChange={(e) => setForm({ ...form, sleep_hours: e.target.value })} />
              </div>
              <div>
                <label className="text-sm font-medium text-gray-600 flex items-center gap-1"><Smile size={14} /> 今日心情</label>
                <div className="flex gap-2 mt-2">
                  {MOOD_OPTIONS.map((m) => (
                    <button key={m} type="button" onClick={() => setForm({ ...form, mood: m })} className={`text-2xl p-2 rounded-xl transition-all ${form.mood === m ? 'bg-brand-50 scale-110' : 'hover:bg-gray-50'}`}>{m}</button>
                  ))}
                </div>
              </div>
            </div>
            <div>
              <label className="text-sm font-medium text-gray-600">备注</label>
              <textarea className="input-field mt-1" rows={2} placeholder="今天的感受、特殊情况..." value={form.notes} onChange={(e) => setForm({ ...form, notes: e.target.value })} />
            </div>
            <div className="flex gap-3">
              <button type="submit" className="btn-primary">保存记录</button>
              <button type="button" onClick={() => setShowForm(false)} className="btn-secondary">取消</button>
            </div>
          </form>
        </div>
      )}

      <div className="space-y-3">
        <h2 className="text-lg font-semibold">历史记录</h2>
        {loading ? <div className="space-y-2">{[1,2,3].map(i => <div key={i} className="h-16 bg-gray-100 rounded-xl animate-pulse" />)}</div>
          : records.length === 0 ? <div className="text-center py-12 text-gray-400"><Heart size={32} className="mx-auto mb-2 opacity-50" /><p>还没有健康记录，开始记录吧！</p></div>
          : records.map((r) => (
            <div key={r.id} className="card flex items-center gap-4">
              <div className="text-center">
                <div className="text-xs text-gray-400">{r.date?.slice(5, 10)?.replace('-', '/') || ''}</div>
              </div>
              <div className="flex-1 grid grid-cols-4 gap-4 text-sm">
                {r.weight && <div><span className="text-gray-400">体重</span><div className="font-semibold">{r.weight}kg</div></div>}
                {r.steps > 0 && <div><span className="text-gray-400">步数</span><div className="font-semibold">{r.steps.toLocaleString()}</div></div>}
                {r.sleep_hours && <div><span className="text-gray-400">睡眠</span><div className="font-semibold">{r.sleep_hours}h</div></div>}
                {r.mood && <div><span className="text-gray-400">心情</span><div className="text-2xl">{r.mood}</div></div>}
              </div>
              {r.notes && <div className="text-xs text-gray-400 max-w-xs truncate">{r.notes}</div>}
            </div>
          ))
        }
      </div>
    </div>
  )
}

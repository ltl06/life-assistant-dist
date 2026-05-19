import { useEffect, useState } from 'react'
import { api } from '../utils/api'
import { TrendingUp, Plus, ArrowUpCircle, ArrowDownCircle } from 'lucide-react'
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from 'recharts'

const COLORS = ['#10b981', '#f59e0b', '#ef4444', '#3b82f6', '#8b5cf6', '#ec4899', '#14b8a6', '#f97316']
const EXPENSE_CATEGORIES = ['餐饮', '交通', '购物', '居住', '医疗', '教育', '娱乐', '通讯', '服装', '其他']
const INCOME_CATEGORIES = ['工资', '奖金', '投资收益', '兼职', '其他收入']

export default function Finance() {
  const [records, setRecords] = useState([])
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [type, setType] = useState('expense')
  const [form, setForm] = useState({ amount: '', category: '', description: '', date: '' })

  useEffect(() => { loadData() }, [])
  async function loadData() {
    try {
      const [recs, st] = await Promise.all([api.finance.list({ limit: 50 }), api.finance.stats(30)])
      setRecords(recs); setStats(st)
    } catch {} finally { setLoading(false) }
  }

  async function handleSubmit(e) {
    e.preventDefault()
    if (!form.amount || !form.category) return
    try {
      await api.finance.create({
        type,
        amount: parseFloat(form.amount),
        category: form.category,
        description: form.description || null,
        date: form.date || undefined,
      })
      setShowForm(false)
      setForm({ amount: '', category: '', description: '', date: '' })
      loadData()
    } catch {}
  }

  const categories = type === 'expense' ? EXPENSE_CATEGORIES : INCOME_CATEGORIES
  const pieData = records.filter(r => r.type === 'expense').reduce((acc, r) => {
    const existing = acc.find(c => c.name === r.category)
    if (existing) existing.value += r.amount
    else acc.push({ name: r.category, value: r.amount })
    return acc
  }, []).slice(0, 5)

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <TrendingUp className="w-7 h-7 text-emerald-500" /> 财务管家
          </h1>
          <p className="text-gray-500 mt-1">轻松记账，掌握每一分钱</p>
        </div>
        <button onClick={() => setShowForm(!showForm)} className="btn-primary flex items-center gap-2">
          <Plus size={18} /> 记一笔
        </button>
      </div>

      {stats && (
        <div className="grid grid-cols-3 gap-4">
          <div className="card text-center border-green-100 bg-green-50">
            <ArrowUpCircle className="w-8 h-8 text-green-500 mx-auto mb-2" />
            <div className="text-2xl font-bold text-green-600">+¥{stats.total_income?.toLocaleString()}</div>
            <div className="stat-label">本月收入</div>
          </div>
          <div className="card text-center border-red-100 bg-red-50">
            <ArrowDownCircle className="w-8 h-8 text-red-500 mx-auto mb-2" />
            <div className="text-2xl font-bold text-red-600">-¥{stats.total_expense?.toLocaleString()}</div>
            <div className="stat-label">本月支出</div>
          </div>
          <div className="card text-center border-blue-100 bg-blue-50">
            <TrendingUp className="w-8 h-8 text-blue-500 mx-auto mb-2" />
            <div className={`text-2xl font-bold ${stats.balance >= 0 ? 'text-blue-600' : 'text-red-600'}`}>
              {stats.balance >= 0 ? '+' : ''}¥{stats.balance?.toLocaleString()}
            </div>
            <div className="stat-label">本月结余</div>
          </div>
        </div>
      )}

      {pieData.length > 0 && (
        <div className="grid md:grid-cols-2 gap-4">
          <div className="card">
            <h2 className="text-lg font-semibold mb-4">支出分布</h2>
            <ResponsiveContainer width="100%" height={200}>
              <PieChart>
                <Pie data={pieData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={80} label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`} labelLine={false} fontSize={12}>
                  {pieData.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                </Pie>
                <Tooltip formatter={(v) => `¥${v.toLocaleString()}`} />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="card">
            <h2 className="text-lg font-semibold mb-4">各类支出</h2>
            <div className="space-y-2">
              {pieData.map((item, i) => (
                <div key={item.name} className="flex items-center gap-3">
                  <div className="w-3 h-3 rounded-full" style={{ backgroundColor: COLORS[i % COLORS.length] }} />
                  <span className="text-sm flex-1">{item.name}</span>
                  <span className="text-sm font-medium">¥{item.value.toLocaleString()}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {showForm && (
        <div className="card border-brand-200">
          <h2 className="text-lg font-semibold mb-4">记一笔</h2>
          <div className="flex gap-2 mb-4">
            <button onClick={() => { setType('expense'); setForm({ ...form, category: '' }) }} className={`flex-1 py-2 rounded-xl font-medium transition-all ${type === 'expense' ? 'bg-red-500 text-white' : 'bg-gray-100'}`}>支出</button>
            <button onClick={() => { setType('income'); setForm({ ...form, category: '' }) }} className={`flex-1 py-2 rounded-xl font-medium transition-all ${type === 'income' ? 'bg-green-500 text-white' : 'bg-gray-100'}`}>收入</button>
          </div>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-medium text-gray-600">金额 (元)</label>
                <input className="input-field mt-1" type="number" step="0.01" placeholder="0.00" value={form.amount} onChange={(e) => setForm({ ...form, amount: e.target.value })} required />
              </div>
              <div>
                <label className="text-sm font-medium text-gray-600">分类</label>
                <select className="input-field mt-1" value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })} required>
                  <option value="">选择分类</option>
                  {categories.map(c => <option key={c} value={c}>{c}</option>)}
                </select>
              </div>
            </div>
            <div>
              <label className="text-sm font-medium text-gray-600">备注</label>
              <input className="input-field mt-1" placeholder="如：午餐外卖" value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} />
            </div>
            <div className="flex gap-3">
              <button type="submit" className={`btn-primary ${type === 'income' ? '!bg-green-500 hover:!bg-green-600' : type === 'expense' ? '!bg-red-500 hover:!bg-red-600' : ''}`}>保存</button>
              <button type="button" onClick={() => setShowForm(false)} className="btn-secondary">取消</button>
            </div>
          </form>
        </div>
      )}

      <div className="space-y-3">
        <h2 className="text-lg font-semibold">收支记录</h2>
        {loading ? <div className="space-y-2">{[1,2,3].map(i => <div key={i} className="h-14 bg-gray-100 rounded-xl animate-pulse" />)}</div>
          : records.length === 0 ? <div className="text-center py-12 text-gray-400"><TrendingUp size={32} className="mx-auto mb-2 opacity-50" /><p>还没有记录，开始记账吧！</p></div>
          : records.map((r) => (
            <div key={r.id} className="card flex items-center gap-4">
              <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${r.type === 'income' ? 'bg-green-100' : 'bg-red-100'}`}>
                {r.type === 'income' ? <ArrowUpCircle className="w-5 h-5 text-green-600" /> : <ArrowDownCircle className="w-5 h-5 text-red-600" />}
              </div>
              <div className="flex-1">
                <div className="font-medium text-sm">{r.category}</div>
                {r.description && <div className="text-xs text-gray-400">{r.description}</div>}
              </div>
              <div className="text-right">
                <div className={`font-bold ${r.type === 'income' ? 'text-green-600' : 'text-red-600'}`}>
                  {r.type === 'income' ? '+' : '-'}¥{r.amount.toLocaleString()}
                </div>
                <div className="text-xs text-gray-400">{r.date?.slice(0, 10)}</div>
              </div>
            </div>
          ))
        }
      </div>
    </div>
  )
}

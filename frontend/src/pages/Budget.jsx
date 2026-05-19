import { useEffect, useState } from 'react'
import { api } from '../utils/api'
import { Wallet, Plus, ChevronLeft, ChevronRight, AlertTriangle, CheckCircle } from 'lucide-react'

const CATEGORIES = ["餐饮", "交通", "购物", "居住", "医疗", "教育", "娱乐", "通讯", "服装", "其他"]
const COLORS = ['#10b981', '#f59e0b', '#ef4444', '#3b82f6', '#8b5cf6', '#ec4899', '#14b8a6', '#f97316', '#06b6d4', '#84cc16']

function getCurrentYearMonth() {
  const d = new Date()
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`
}

export default function Budget() {
  const [yearMonth, setYearMonth] = useState(getCurrentYearMonth())
  const [summary, setSummary] = useState(null)
  const [loading, setLoading] = useState(true)
  const [showBudgetForm, setShowBudgetForm] = useState(false)
  const [budgetForm, setBudgetForm] = useState({ category: '', budget_amount: '' })
  const [budgets, setBudgets] = useState([])

  useEffect(() => { loadData() }, [yearMonth])

  async function loadData() {
    setLoading(true)
    try {
      const [summary, budgetList] = await Promise.all([
        api.budget.summary(yearMonth),
        api.budget.list(yearMonth),
      ])
      setSummary(summary)
      setBudgets(budgetList)
    } catch {} finally { setLoading(false) }
  }

  async function handleSetBudget(e) {
    e.preventDefault()
    if (!budgetForm.category || !budgetForm.budget_amount) return
    try {
      await api.budget.create({
        year_month: yearMonth,
        category: budgetForm.category,
        budget_amount: parseFloat(budgetForm.budget_amount),
      })
      setShowBudgetForm(false)
      setBudgetForm({ category: '', budget_amount: '' })
      loadData()
    } catch {}
  }

  async function handleDeleteBudget(id) {
    await api.budget.delete(id)
    setBudgets(budgets.filter(b => b.id !== id))
    loadData()
  }

  function prevMonth() {
    const [y, m] = yearMonth.split('-').map(Number)
    if (m === 1) setYearMonth(`${y - 1}-12`)
    else setYearMonth(`${y}-${String(m - 1).padStart(2, '0')}`)
  }

  function nextMonth() {
    const [y, m] = yearMonth.split('-').map(Number)
    if (m === 12) setYearMonth(`${y + 1}-01`)
    else setYearMonth(`${y}-${String(m + 1).padStart(2, '0')}`)
  }

  const ym = yearMonth.split('-')
  const monthLabel = `${ym[0]}年${parseInt(ym[1])}月`

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Wallet className="w-7 h-7 text-emerald-500" /> 预算计划
          </h1>
          <p className="text-gray-500 mt-1">设定预算，控制消费</p>
        </div>
        <button onClick={() => setShowBudgetForm(true)} className="btn-primary flex items-center gap-2">
          <Plus size={18} /> 设置预算
        </button>
      </div>

      <div className="flex items-center gap-4 justify-center">
        <button onClick={prevMonth} className="p-2 rounded-xl hover:bg-gray-100"><ChevronLeft size={20} /></button>
        <span className="text-xl font-bold min-w-[120px] text-center">{monthLabel}</span>
        <button onClick={nextMonth} className="p-2 rounded-xl hover:bg-gray-100"><ChevronRight size={20} /></button>
      </div>

      {loading ? <div className="space-y-3">{[1,2,3].map(i => <div key={i} className="h-20 bg-gray-100 rounded-2xl animate-pulse" />)}</div>
        : summary ? (
          <>
            <div className="card">
              <div className="flex items-center justify-between mb-3">
                <span className="font-semibold">本月总预算</span>
                {summary.is_over ? (
                  <span className="flex items-center gap-1 text-red-500 text-sm"><AlertTriangle size={14} /> 已超支</span>
                ) : (
                  <span className="flex items-center gap-1 text-green-500 text-sm"><CheckCircle size={14} /> 在预算内</span>
                )}
              </div>
              <div className="relative h-4 bg-gray-100 rounded-full overflow-hidden mb-2">
                <div className="absolute inset-0 bg-gradient-to-r from-emerald-400 to-red-400 transition-all"
                  style={{ width: `${Math.min(summary.overall_percent, 100)}%` }} />
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-500">已花 ¥{summary.total_spent.toLocaleString()}</span>
                <span className="font-bold text-gray-900">剩余 ¥{Math.max(0, summary.overall_remaining).toLocaleString()}</span>
                <span className="text-gray-500">预算 ¥{summary.total_budget.toLocaleString()}</span>
              </div>
            </div>

            {summary.categories.length > 0 ? (
              <div className="space-y-3">
                <h2 className="font-semibold text-gray-700">分类预算</h2>
                {summary.categories.map((cat, i) => (
                  <div key={cat.category} className="card">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <div className="w-3 h-3 rounded-full" style={{ backgroundColor: COLORS[i % COLORS.length] }} />
                        <span className="font-medium">{cat.category}</span>
                      </div>
                      <div className="flex items-center gap-3 text-sm">
                        <span className={cat.is_over ? 'text-red-500' : 'text-gray-500'}>
                          ¥{cat.spent.toLocaleString()} / ¥{cat.budget.toLocaleString()}
                        </span>
                        <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${cat.is_over ? 'bg-red-50 text-red-600' : 'bg-green-50 text-green-600'}`}>
                          {cat.percent}%
                        </span>
                      </div>
                    </div>
                    <div className="relative h-2 bg-gray-100 rounded-full overflow-hidden">
                      <div className="absolute inset-y-0 left-0 rounded-full transition-all"
                        style={{
                          width: `${Math.min(cat.percent, 100)}%`,
                          backgroundColor: cat.is_over ? '#ef4444' : COLORS[i % COLORS.length],
                        }} />
                    </div>
                    {cat.is_over && (
                      <p className="text-xs text-red-500 mt-1 flex items-center gap-1">
                        <AlertTriangle size={12} /> 已超支 ¥{(cat.spent - cat.budget).toLocaleString()}，注意控制！
                      </p>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-12 text-gray-400">
                <Wallet size={40} className="mx-auto mb-3 opacity-40" />
                <p>还没有设置预算，点击右上角开始规划</p>
              </div>
            )}

            {budgets.length > 0 && (
              <div className="space-y-2">
                <h2 className="font-semibold text-gray-700">已设置的预算</h2>
                <div className="flex flex-wrap gap-2">
                  {budgets.map(b => (
                    <div key={b.id} className="card !p-3 flex items-center gap-3">
                      <span className="text-sm">{b.category}</span>
                      <span className="text-sm font-bold">¥{b.budget_amount}</span>
                      <button onClick={() => handleDeleteBudget(b.id)} className="text-gray-400 hover:text-red-500 text-xs">删除</button>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </>
        ) : null
      }

      {showBudgetForm && (
        <div className="card border-brand-200">
          <h3 className="font-semibold mb-4">设置 {monthLabel} 预算</h3>
          <form onSubmit={handleSetBudget} className="space-y-4">
            <div>
              <label className="text-sm font-medium text-gray-600 mb-1 block">支出分类</label>
              <select className="input-field" value={budgetForm.category}
                onChange={e => setBudgetForm({ ...budgetForm, category: e.target.value })} required>
                <option value="">选择分类</option>
                {CATEGORIES.map(c => <option key={c} value={c}>{c}</option>)}
              </select>
            </div>
            <div>
              <label className="text-sm font-medium text-gray-600 mb-1 block">预算金额（元）</label>
              <input className="input-field" type="number" step="0.01" placeholder="如 2000"
                value={budgetForm.budget_amount}
                onChange={e => setBudgetForm({ ...budgetForm, budget_amount: e.target.value })} required />
            </div>
            <div className="flex gap-3">
              <button type="submit" className="btn-primary">保存</button>
              <button type="button" onClick={() => setShowBudgetForm(false)} className="btn-secondary">取消</button>
            </div>
          </form>
        </div>
      )}
    </div>
  )
}

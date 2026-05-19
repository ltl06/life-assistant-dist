import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../utils/api'
import {
  Heart, TrendingUp, CheckSquare, MessageCircle, ArrowRight, Activity, Wallet, Clock,
  Sun, Cloud, Wind, BookOpen, AlertTriangle, CheckCircle,
} from 'lucide-react'

function StatCard({ icon: Icon, label, value, sub, color }) {
  return (
    <div className="card flex items-start gap-4">
      <div className={`w-12 h-12 rounded-xl flex items-center justify-center shrink-0 ${color}`}>
        <Icon className="w-6 h-6 text-white" />
      </div>
      <div>
        <div className="stat-value">{value ?? '--'}</div>
        <div className="stat-label">{label}</div>
        {sub && <div className="text-xs text-gray-400 mt-0.5">{sub}</div>}
      </div>
    </div>
  )
}

export default function Dashboard() {
  const [stats, setStats] = useState({ health: null, finance: null, todos: null, habits: null })
  const [weather, setWeather] = useState(null)
  const [budget, setBudget] = useState(null)
  const [diary, setDiary] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      api.weather.current().catch(() => null),
      api.health.stats(7).catch(() => null),
      api.finance.stats(7).catch(() => null),
      api.productivity.todos.list({ completed: false }).catch(() => []),
      api.productivity.habits.list().catch(() => []),
    ]).then(([w, health, finance, todos, habits]) => {
      setWeather(w)
      setStats({ health, finance, todos, habits })
      setLoading(false)
    })

    const currentYM = `${new Date().getFullYear()}-${String(new Date().getMonth() + 1).padStart(2, '0')}`
    api.budget.summary(currentYM).then(b => setBudget(b)).catch(() => {})

    api.diary.list({ limit: 1 }).then(d => setDiary(d[0] || null)).catch(() => {})
  }, [])

  const greeting = () => {
    const h = new Date().getHours()
    if (h < 12) return '早上好'
    if (h < 18) return '下午好'
    return '晚上好'
  }

  const quickActions = [
    { to: '/health', icon: Activity, label: '记录健康', color: 'bg-pink-500' },
    { to: '/finance', icon: Wallet, label: '记一笔账', color: 'bg-green-500' },
    { to: '/productivity', icon: Clock, label: '添加待办', color: 'bg-amber-500' },
    { to: '/diary', icon: BookOpen, label: '写日记', color: 'bg-indigo-500' },
  ]

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">{greeting()} 👋</h1>
          <p className="text-gray-500 mt-1">
            今天是 {new Date().toLocaleDateString('zh-CN', { weekday: 'long', month: 'long', day: 'numeric' })}
          </p>
        </div>
        {weather && (
          <div className="card !p-3 text-center min-w-[100px]">
            <div className="text-3xl">{weather.icon}</div>
            <div className="text-xl font-bold">{weather.temp}°</div>
            <div className="text-xs text-gray-500">{weather.city}</div>
          </div>
        )}
      </div>

      {weather && (
        <div className={`card flex items-center gap-4 ${weather.condition.includes('雨') || weather.condition.includes('雷') ? 'bg-blue-50 border-blue-100' : weather.condition.includes('霾') || weather.condition.includes('雾') ? 'bg-yellow-50 border-yellow-100' : 'bg-brand-50 border-brand-100'} border`}>
          <div className="text-4xl">{weather.icon}</div>
          <div className="flex-1">
            <div className="font-medium">{weather.condition} · {weather.temp}°C · {weather.city}</div>
            <div className="text-sm text-gray-500 flex items-center gap-3 mt-1">
              <span className="flex items-center gap-1"><Wind size={14} />{weather.wind_speed}m/s</span>
              <span>湿度 {weather.humidity}%</span>
            </div>
          </div>
          <div className="text-sm text-gray-600 max-w-xs hidden md:block">
            {weather.suggestion}
          </div>
        </div>
      )}

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {quickActions.map(({ to, icon: Icon, label, color }) => (
          <Link key={to} to={to} className="card flex flex-col items-center gap-2 py-4 hover:border-brand-200 transition-all">
            <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${color}`}>
              <Icon className="w-5 h-5 text-white" />
            </div>
            <span className="text-sm font-medium text-gray-700">{label}</span>
          </Link>
        ))}
      </div>

      {budget && budget.total_budget > 0 && (
        <div className={`card border ${budget.is_over ? 'border-red-200 bg-red-50' : 'border-green-100 bg-green-50'}`}>
          <div className="flex items-center justify-between mb-2">
            <div className="font-semibold text-sm">本月预算</div>
            {budget.is_over
              ? <span className="text-xs text-red-600 flex items-center gap-1"><AlertTriangle size={12} /> 已超支 ¥{(budget.total_spent - budget.total_budget).toLocaleString()}</span>
              : <span className="text-xs text-green-600 flex items-center gap-1"><CheckCircle size={12} /> 剩余 ¥{budget.overall_remaining.toLocaleString()}</span>
            }
          </div>
          <div className="relative h-3 bg-white rounded-full overflow-hidden">
            <div className="absolute inset-y-0 left-0 rounded-full transition-all"
              style={{ width: `${Math.min(budget.overall_percent, 100)}%`, backgroundColor: budget.is_over ? '#ef4444' : '#10b981' }} />
          </div>
          <div className="flex justify-between text-xs text-gray-500 mt-1">
            <span>¥{budget.total_spent.toLocaleString()}</span>
            <span>¥{budget.total_budget.toLocaleString()}</span>
          </div>
        </div>
      )}

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard icon={Heart} label="本周记录" value={stats.health?.total_records} sub="健康记录数" color="bg-rose-500" />
        <StatCard icon={TrendingUp} label="本周支出" value={stats.finance ? `¥${stats.finance.total_expense}` : '--'} sub={stats.finance?.top_expense_category ? `最高: ${stats.finance.top_expense_category}` : ''} color="bg-emerald-500" />
        <StatCard icon={CheckSquare} label="待办事项" value={stats.todos?.length ?? '--'} sub="未完成" color="bg-amber-500" />
        <StatCard icon={Activity} label="习惯追踪" value={stats.habits?.length ?? '--'} sub="进行中" color="bg-violet-500" />
      </div>

      <div className="grid md:grid-cols-2 gap-4">
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold">待办事项</h2>
            <Link to="/productivity" className="text-sm text-brand-600 flex items-center gap-1 hover:underline">
              查看全部 <ArrowRight size={14} />
            </Link>
          </div>
          {loading ? <div className="space-y-2">{[1, 2].map(i => <div key={i} className="h-10 bg-gray-100 rounded-xl animate-pulse" />)}</div>
            : stats.todos?.length > 0 ? (
              <div className="space-y-2">
                {stats.todos.slice(0, 5).map((todo) => (
                  <div key={todo.id} className="flex items-center gap-3 p-2 rounded-xl hover:bg-gray-50 transition-colors">
                    <div className={`w-4 h-4 rounded-full border-2 ${todo.completed ? 'border-green-500 bg-green-500' : 'border-gray-300'}`} />
                    <span className={`flex-1 text-sm ${todo.completed ? 'line-through text-gray-400' : 'text-gray-700'}`}>{todo.title}</span>
                    {todo.due_date && <span className="text-xs text-gray-400">{new Date(todo.due_date).toLocaleDateString('zh-CN')}</span>}
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-6 text-gray-400 text-sm">
                <CheckSquare size={24} className="mx-auto mb-2 opacity-40" />
                <p>暂无待办</p>
              </div>
            )
          }
        </div>

        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold">最近日记</h2>
            <Link to="/diary" className="text-sm text-brand-600 flex items-center gap-1 hover:underline">
              查看全部 <ArrowRight size={14} />
            </Link>
          </div>
          {diary ? (
            <div className="text-sm">
              <div className="flex items-center gap-2 mb-2">
                {diary.mood && <span className="text-xl">{diary.mood}</span>}
                <span className="text-gray-400 text-xs">{diary.date?.slice(0, 10)}</span>
              </div>
              <p className="text-gray-600 line-clamp-3">{diary.content}</p>
            </div>
          ) : (
            <div className="text-center py-6 text-gray-400 text-sm">
              <BookOpen size={24} className="mx-auto mb-2 opacity-40" />
              <p>还没有日记</p>
              <Link to="/diary" className="text-brand-500 text-xs mt-1 inline-block hover:underline">写一篇？</Link>
            </div>
          )}
        </div>
      </div>

      {!loading && stats.health?.total_records > 0 && (
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold">本周健康概览</h2>
            <Link to="/health" className="text-sm text-brand-600 flex items-center gap-1 hover:underline">
              详细数据 <ArrowRight size={14} />
            </Link>
          </div>
          <div className="grid grid-cols-3 gap-4 text-center">
            <div className="p-4 bg-rose-50 rounded-xl">
              <div className="text-2xl font-bold text-rose-600">{stats.health.avg_weight ?? '--'}</div>
              <div className="text-xs text-rose-400 mt-1">平均体重 (kg)</div>
            </div>
            <div className="p-4 bg-indigo-50 rounded-xl">
              <div className="text-2xl font-bold text-indigo-600">{stats.health.avg_sleep ?? '--'}</div>
              <div className="text-xs text-indigo-400 mt-1">平均睡眠 (h)</div>
            </div>
            <div className="p-4 bg-green-50 rounded-xl">
              <div className="text-2xl font-bold text-green-600">{stats.health.avg_steps?.toLocaleString() ?? '--'}</div>
              <div className="text-xs text-green-400 mt-1">平均步数</div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

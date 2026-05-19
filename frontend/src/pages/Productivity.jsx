import { useEffect, useState } from 'react'
import { api } from '../utils/api'
import { CheckSquare, Plus, Flame, Bell, Trash2, Check, Circle, Zap } from 'lucide-react'

export default function Productivity() {
  const [todos, setTodos] = useState([])
  const [habits, setHabits] = useState([])
  const [reminders, setReminders] = useState([])
  const [tab, setTab] = useState('todos')
  const [showTodo, setShowTodo] = useState(false)
  const [showHabit, setShowHabit] = useState(false)
  const [showReminder, setShowReminder] = useState(false)
  const [todoForm, setTodoForm] = useState({ title: '', description: '', priority: 'medium' })
  const [habitForm, setHabitForm] = useState({ name: '', frequency: 'daily' })
  const [reminderForm, setReminderForm] = useState({ title: '', message: '', remind_at: '' })
  const [loading, setLoading] = useState(true)

  useEffect(() => { loadData() }, [])
  async function loadData() {
    try {
      const [t, h, r] = await Promise.all([
        api.productivity.todos.list(),
        api.productivity.habits.list(),
        api.productivity.reminders.list(),
      ])
      setTodos(t); setHabits(h); setReminders(r)
    } catch {} finally { setLoading(false) }
  }

  async function toggleTodo(id, completed) {
    await api.productivity.todos.update(id, !completed)
    setTodos(todos.map(t => t.id === id ? { ...t, completed: !completed } : t))
  }

  async function deleteTodo(id) {
    await api.productivity.todos.delete(id)
    setTodos(todos.filter(t => t.id !== id))
  }

  async function createTodo(e) {
    e.preventDefault()
    const t = await api.productivity.todos.create(todoForm)
    setTodos([t, ...todos])
    setShowTodo(false)
    setTodoForm({ title: '', description: '', priority: 'medium' })
  }

  async function createHabit(e) {
    e.preventDefault()
    const h = await api.productivity.habits.create(habitForm)
    setHabits([...habits, h])
    setShowHabit(false)
    setHabitForm({ name: '', frequency: 'daily' })
  }

  async function checkinHabit(id) {
    await api.productivity.habits.checkin(id)
    setHabits(habits.map(h => h.id === id ? { ...h, current_streak: h.current_streak + 1 } : h))
  }

  async function createReminder(e) {
    e.preventDefault()
    const r = await api.productivity.reminders.create(reminderForm)
    setReminders([...reminders, r])
    setShowReminder(false)
    setReminderForm({ title: '', message: '', remind_at: '' })
  }

  async function deleteReminder(id) {
    await api.productivity.reminders.delete(id)
    setReminders(reminders.filter(r => r.id !== id))
  }

  const priorityColors = { high: 'badge-red', medium: 'badge-yellow', low: 'badge-blue' }
  const tabs = [
    { key: 'todos', label: '待办', icon: CheckSquare, count: todos.filter(t => !t.completed).length },
    { key: 'habits', label: '习惯', icon: Flame, count: habits.length },
    { key: 'reminders', label: '提醒', icon: Bell, count: reminders.length },
  ]

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <CheckSquare className="w-7 h-7 text-amber-500" /> 效率工具
          </h1>
          <p className="text-gray-500 mt-1">待办、习惯、打卡，一个都不能少</p>
        </div>
        <button onClick={() => {
          if (tab === 'todos') setShowTodo(true)
          else if (tab === 'habits') setShowHabit(true)
          else setShowReminder(true)
        }} className="btn-primary flex items-center gap-2">
          <Plus size={18} /> 添加
        </button>
      </div>

      <div className="flex gap-2 bg-gray-100 p-1 rounded-2xl w-fit">
        {tabs.map(({ key, label, icon: Icon, count }) => (
          <button key={key} onClick={() => setTab(key)}
            className={`flex items-center gap-2 px-5 py-2 rounded-xl text-sm font-medium transition-all ${tab === key ? 'bg-white shadow-sm text-gray-900' : 'text-gray-500 hover:text-gray-700'}`}>
            <Icon size={16} /> {label} {count > 0 && <span className="bg-brand-500 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center">{count}</span>}
          </button>
        ))}
      </div>

      {tab === 'todos' && (
        <div className="space-y-3">
          {showTodo && (
            <div className="card border-brand-200">
              <h3 className="font-semibold mb-3">新建待办</h3>
              <form onSubmit={createTodo} className="space-y-3">
                <input className="input-field" placeholder="待办事项标题" value={todoForm.title}
                  onChange={e => setTodoForm({ ...todoForm, title: e.target.value })} required />
                <textarea className="input-field" rows={2} placeholder="详细描述（可选）" value={todoForm.description}
                  onChange={e => setTodoForm({ ...todoForm, description: e.target.value })} />
                <div className="flex gap-2">
                  {['high', 'medium', 'low'].map(p => (
                    <button key={p} type="button" onClick={() => setTodoForm({ ...todoForm, priority: p })}
                      className={`px-4 py-1.5 rounded-lg text-sm font-medium transition-all ${todoForm.priority === p ? (p === 'high' ? 'bg-red-500 text-white' : p === 'medium' ? 'bg-yellow-500 text-white' : 'bg-blue-500 text-white') : 'bg-gray-100'}`}>
                      {p === 'high' ? '高' : p === 'medium' ? '中' : '低'}优先级
                    </button>
                  ))}
                </div>
                <div className="flex gap-3">
                  <button type="submit" className="btn-primary">保存</button>
                  <button type="button" onClick={() => setShowTodo(false)} className="btn-secondary">取消</button>
                </div>
              </form>
            </div>
          )}
          {loading ? <div className="space-y-2">{[1,2,3].map(i => <div key={i} className="h-14 bg-gray-100 rounded-xl animate-pulse" />)}</div>
            : todos.length === 0 ? <div className="text-center py-16 text-gray-400"><CheckSquare size={40} className="mx-auto mb-3 opacity-40" /><p>所有任务都完成了，太棒了！</p></div>
            : <>
              {todos.filter(t => !t.completed).map(t => (
                <div key={t.id} className="card flex items-center gap-4 group">
                  <button onClick={() => toggleTodo(t.id, t.completed)} className="shrink-0">
                    <Circle size={22} className="text-gray-300 hover:text-brand-500 transition-colors" />
                  </button>
                  <div className="flex-1 min-w-0">
                    <div className="font-medium text-sm truncate">{t.title}</div>
                    {t.description && <div className="text-xs text-gray-400 truncate">{t.description}</div>}
                  </div>
                  <span className={`badge ${priorityColors[t.priority] || 'badge-blue'}`}>{t.priority === 'high' ? '高' : t.priority === 'medium' ? '中' : '低'}</span>
                  <button onClick={() => deleteTodo(t.id)} className="opacity-0 group-hover:opacity-100 p-1 text-gray-400 hover:text-red-500 transition-all">
                    <Trash2 size={16} />
                  </button>
                </div>
              ))}
              {todos.filter(t => t.completed).length > 0 && (
                <>
                  <div className="text-sm text-gray-400 font-medium px-2">已完成</div>
                  {todos.filter(t => t.completed).map(t => (
                    <div key={t.id} className="card flex items-center gap-4 group opacity-60">
                      <button onClick={() => toggleTodo(t.id, t.completed)}>
                        <Check size={22} className="text-green-500" />
                      </button>
                      <div className="flex-1 line-through text-sm text-gray-400">{t.title}</div>
                      <button onClick={() => deleteTodo(t.id)} className="opacity-0 group-hover:opacity-100 p-1 text-gray-400 hover:text-red-500">
                        <Trash2 size={16} />
                      </button>
                    </div>
                  ))}
                </>
              )}
            </>
          }
        </div>
      )}

      {tab === 'habits' && (
        <div className="space-y-3">
          {showHabit && (
            <div className="card border-brand-200">
              <h3 className="font-semibold mb-3">新建习惯</h3>
              <form onSubmit={createHabit} className="space-y-3">
                <input className="input-field" placeholder="习惯名称，如：每日阅读30分钟" value={habitForm.name}
                  onChange={e => setHabitForm({ ...habitForm, name: e.target.value })} required />
                <div className="flex gap-2">
                  {[['daily', '每日'], ['weekly', '每周']].map(([v, l]) => (
                    <button key={v} type="button" onClick={() => setHabitForm({ ...habitForm, frequency: v })}
                      className={`px-4 py-1.5 rounded-lg text-sm font-medium ${habitForm.frequency === v ? 'bg-brand-500 text-white' : 'bg-gray-100'}`}>{l}</button>
                  ))}
                </div>
                <div className="flex gap-3">
                  <button type="submit" className="btn-primary">保存</button>
                  <button type="button" onClick={() => setShowHabit(false)} className="btn-secondary">取消</button>
                </div>
              </form>
            </div>
          )}
          {habits.length === 0 && !showHabit && <div className="text-center py-16 text-gray-400"><Flame size={40} className="mx-auto mb-3 opacity-40" /><p>还没有习惯，创建一个吧！</p></div>}
          <div className="grid md:grid-cols-2 gap-4">
            {habits.map(h => (
              <div key={h.id} className="card flex items-center gap-4">
                <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-orange-400 to-rose-500 flex flex-col items-center justify-center text-white">
                  <Flame size={20} />
                  <span className="text-xs font-bold">{h.current_streak}</span>
                </div>
                <div className="flex-1">
                  <div className="font-semibold">{h.name}</div>
                  <div className="text-xs text-gray-400 capitalize">{h.frequency} · 目标 {h.target}/天</div>
                </div>
                <button onClick={() => checkinHabit(h.id)} className="w-10 h-10 rounded-xl bg-emerald-500 text-white flex items-center justify-center hover:bg-emerald-600 transition-colors">
                  <Zap size={18} />
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {tab === 'reminders' && (
        <div className="space-y-3">
          {showReminder && (
            <div className="card border-brand-200">
              <h3 className="font-semibold mb-3">新建提醒</h3>
              <form onSubmit={createReminder} className="space-y-3">
                <input className="input-field" placeholder="提醒标题" value={reminderForm.title}
                  onChange={e => setReminderForm({ ...reminderForm, title: e.target.value })} required />
                <input className="input-field" type="datetime-local" value={reminderForm.remind_at}
                  onChange={e => setReminderForm({ ...reminderForm, remind_at: e.target.value })} required />
                <div className="flex gap-3">
                  <button type="submit" className="btn-primary">保存</button>
                  <button type="button" onClick={() => setShowReminder(false)} className="btn-secondary">取消</button>
                </div>
              </form>
            </div>
          )}
          {reminders.length === 0 && !showReminder && <div className="text-center py-16 text-gray-400"><Bell size={40} className="mx-auto mb-3 opacity-40" /><p>还没有提醒</p></div>}
          {reminders.map(r => (
            <div key={r.id} className="card flex items-center gap-4 group">
              <Bell size={20} className="text-violet-500" />
              <div className="flex-1">
                <div className="font-medium text-sm">{r.title}</div>
                <div className="text-xs text-gray-400">{new Date(r.remind_at).toLocaleString('zh-CN')}</div>
              </div>
              <button onClick={() => deleteReminder(r.id)} className="opacity-0 group-hover:opacity-100 p-1 text-gray-400 hover:text-red-500 transition-all">
                <Trash2 size={16} />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

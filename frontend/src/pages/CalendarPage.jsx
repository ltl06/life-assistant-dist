import { useEffect, useState } from 'react'
import { api } from '../utils/api'
import { Flame, Plus, Calendar, ChevronLeft, ChevronRight, Check } from 'lucide-react'

const WEEKDAYS = ['一', '二', '三', '四', '五', '六', '日']

function getMonthDays(year, month) {
  const firstDay = new Date(year, month - 1, 1)
  let dayOfWeek = firstDay.getDay()
  dayOfWeek = dayOfWeek === 0 ? 6 : dayOfWeek - 1
  const daysInMonth = new Date(year, month, 0).getDate()
  const cells = []
  for (let i = 0; i < dayOfWeek; i++) cells.push(null)
  for (let d = 1; d <= daysInMonth; d++) cells.push(d)
  return cells
}

function today() {
  const d = new Date()
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

export default function CalendarPage() {
  const [year, setYear] = useState(new Date().getFullYear())
  const [month, setMonth] = useState(new Date().getMonth() + 1)
  const [habits, setHabits] = useState([])
  const [checkins, setCheckins] = useState({})
  const [showNewHabit, setShowNewHabit] = useState(false)
  const [newHabit, setNewHabit] = useState({ name: '', frequency: 'daily', target: 1 })
  const todayStr = today()

  useEffect(() => { loadData() }, [year, month])

  async function loadData() {
    try {
      const [h, checkinsData] = await Promise.all([
        api.habits.list(),
        api.habits.calendar(year, month),
      ])
      setHabits(h)
      const map = {}
      checkinsData.forEach(c => {
        c.dates.forEach(d => {
          if (!map[d]) map[d] = new Set()
          map[d].add(c.habit_id)
        })
      })
      setCheckins(map)
    } catch {}
  }

  async function handleCheckin(habitId, dateStr) {
    const [y, m, d] = dateStr.split('-').map(Number)
    const check_date = `${y}-${String(m).padStart(2, '0')}-${String(d).padStart(2, '0')}`
    await api.habits.checkin(habitId, check_date)
    await loadData()
  }

  async function handleCreateHabit(e) {
    e.preventDefault()
    if (!newHabit.name) return
    await api.habits.create(newHabit.name, newHabit.frequency, newHabit.target)
    setShowNewHabit(false)
    setNewHabit({ name: '', frequency: 'daily', target: 1 })
    loadData()
  }

  async function handleDeleteHabit(id) {
    if (!confirm('确定删除这个习惯？')) return
    await api.habits.delete(id)
    loadData()
  }

  function prevMonth() {
    if (month === 1) { setYear(year - 1); setMonth(12) }
    else setMonth(month - 1)
  }

  function nextMonth() {
    if (month === 12) { setYear(year + 1); setMonth(1) }
    else setMonth(month + 1)
  }

  const cells = getMonthDays(year, month)
  const monthStr = `${year}-${String(month).padStart(2, '0')}`

  const habitColors = ['bg-rose-400', 'bg-amber-400', 'bg-emerald-400', 'bg-violet-400', 'bg-cyan-400', 'bg-pink-400']

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Calendar className="w-7 h-7 text-violet-500" /> 习惯日历
          </h1>
          <p className="text-gray-500 mt-1">追踪每日习惯打卡情况</p>
        </div>
        <button onClick={() => setShowNewHabit(true)} className="btn-primary flex items-center gap-2">
          <Plus size={18} /> 新建习惯
        </button>
      </div>

      {showNewHabit && (
        <div className="card border-brand-200">
          <h3 className="font-semibold mb-3">新建习惯</h3>
          <form onSubmit={handleCreateHabit} className="space-y-3">
            <input className="input-field" placeholder="习惯名称，如：晨跑 30 分钟"
              value={newHabit.name} onChange={e => setNewHabit({ ...newHabit, name: e.target.value })} required />
            <div className="flex gap-2">
              {[['daily', '每日'], ['weekly', '每周']].map(([v, l]) => (
                <button key={v} type="button" onClick={() => setNewHabit({ ...newHabit, frequency: v })}
                  className={`px-4 py-2 rounded-xl text-sm font-medium ${newHabit.frequency === v ? 'bg-brand-500 text-white' : 'bg-gray-100'}`}>
                  {l}
                </button>
              ))}
            </div>
            <div className="flex gap-3">
              <button type="submit" className="btn-primary">创建</button>
              <button type="button" onClick={() => setShowNewHabit(false)} className="btn-secondary">取消</button>
            </div>
          </form>
        </div>
      )}

      <div className="flex items-center gap-4 justify-center">
        <button onClick={prevMonth} className="p-2 rounded-xl hover:bg-gray-100"><ChevronLeft size={20} /></button>
        <span className="text-xl font-bold">{year}年{month}月</span>
        <button onClick={nextMonth} className="p-2 rounded-xl hover:bg-gray-100"><ChevronRight size={20} /></button>
      </div>

      {habits.length === 0 ? (
        <div className="text-center py-16 text-gray-400">
          <Flame size={40} className="mx-auto mb-3 opacity-40" />
          <p>还没有习惯，点击右上角创建一个</p>
        </div>
      ) : (
        <>
          <div className="flex flex-wrap gap-3">
            {habits.map((h, i) => (
              <div key={h.id} className="card !p-3 flex items-center gap-3">
                <div className={`w-8 h-8 rounded-lg flex items-center justify-center text-white text-sm ${habitColors[i % habitColors.length]}`}>
                  <Flame size={14} />
                </div>
                <div>
                  <div className="text-sm font-medium">{h.name}</div>
                  <div className="text-xs text-gray-400 flex items-center gap-1">
                    <span className="text-amber-500 font-bold">{h.current_streak}</span>天连续
                  </div>
                </div>
                <button onClick={() => handleDeleteHabit(h.id)} className="text-xs text-gray-400 hover:text-red-500 ml-1">删除</button>
              </div>
            ))}
          </div>

          <div className="card">
            <div className="grid mb-2" style={{ gridTemplateColumns: `repeat(7, 1fr)` }}>
              {WEEKDAYS.map(d => (
                <div key={d} className="text-center text-xs font-medium text-gray-400 py-1">{d}</div>
              ))}
            </div>
            <div className="grid gap-1" style={{ gridTemplateColumns: `repeat(7, 1fr)` }}>
              {cells.map((day, idx) => {
                if (!day) return <div key={`empty-${idx}`} />
                const dayStr = `${year}-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}`
                const checked = checkins[dayStr] || new Set()
                const isToday = dayStr === todayStr
                return (
                  <div key={day}
                    className={`aspect-square rounded-xl flex flex-col items-center justify-center text-sm relative
                      ${isToday ? 'ring-2 ring-brand-500' : ''}
                      ${dayStr > todayStr ? 'opacity-30' : 'hover:bg-gray-50'}`}
                  >
                    <span className={`font-medium ${isToday ? 'text-brand-600' : 'text-gray-700'}`}>{day}</span>
                    {habits.length > 0 && (
                      <div className="flex gap-0.5 mt-0.5 flex-wrap justify-center">
                        {habits.slice(0, 5).map((h, hi) => (
                          <div key={h.id}
                            className={`w-2 h-2 rounded-full ${checked.has(h.id) ? habitColors[hi % habitColors.length].replace('bg-', 'bg-') : 'bg-gray-200'}`}
                            style={{ backgroundColor: checked.has(h.id) ? ['#fd3f4b', '#f59e0b', '#10b981', '#8b5cf6', '#06b6d4'][hi % 5] : undefined }} />
                        ))}
                      </div>
                    )}
                    {dayStr <= todayStr && habits.length > 0 && !checked.size && (
                      <button onClick={() => habits[0] && handleCheckin(habits[0].id, dayStr)}
                        className="absolute inset-0 opacity-0 hover:opacity-100 bg-brand-500/10 rounded-xl flex items-center justify-center">
                        <Check size={12} className="text-brand-500" />
                      </button>
                    )}
                  </div>
                )
              })}
            </div>
          </div>

          <div className="card">
            <h3 className="font-semibold mb-3 text-sm">打卡记录（点击格子补打卡）</h3>
            <div className="space-y-2">
              {habits.map((h, i) => {
                const color = ['#fd3f4b', '#f59e0b', '#10b981', '#8b5cf6', '#06b6d4'][i % 5]
                const monthDays = getMonthDays(year, month).filter(Boolean)
                return (
                  <div key={h.id} className="flex items-center gap-3">
                    <div className="flex items-center gap-2 w-32 shrink-0">
                      <div className="w-3 h-3 rounded-full shrink-0" style={{ backgroundColor: color }} />
                      <span className="text-sm truncate">{h.name}</span>
                    </div>
                    <div className="flex gap-1 flex-wrap">
                      {monthDays.map(d => {
                        const dayStr = `${year}-${String(month).padStart(2, '0')}-${String(d).padStart(2, '0')}`
                        const checked = (checkins[dayStr] || new Set()).has(h.id)
                        const isFuture = dayStr > todayStr
                        return (
                          <button key={d} disabled={isFuture}
                            onClick={() => handleCheckin(h.id, dayStr)}
                            className={`w-6 h-6 text-xs rounded flex items-center justify-center transition-all
                              ${checked ? 'text-white' : 'bg-gray-100 text-gray-400 hover:bg-gray-200'}
                              ${dayStr === todayStr ? 'ring-1 ring-brand-400' : ''}`}
                            style={checked ? { backgroundColor: color } : undefined}>
                            {d}
                          </button>
                        )
                      })}
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        </>
      )}
    </div>
  )
}

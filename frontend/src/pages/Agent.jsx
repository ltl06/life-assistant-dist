import { useState, useRef, useEffect } from 'react'
import { api } from '../utils/api'
import { MessageCircle, Send, Sparkles, Bot, User, CheckCircle, Clock, XCircle, Loader, Zap, ChevronDown, ChevronUp, Trash2 } from 'lucide-react'

const QUICK_ACTIONS = [
  { label: '帮我规划本周目标', icon: '🎯' },
  { label: '记录今天的健康数据', icon: '💪' },
  { label: '记账：午餐外卖 35 元', icon: '💰' },
  { label: '创建早睡习惯', icon: '🌙' },
  { label: '分析我的情绪趋势', icon: '📊' },
  { label: '写一篇日记', icon: '📝' },
]

function StepBadge({ tool }) {
  const icons = {
    log_health: '💪', get_health_summary: '📊',
    log_finance: '💰', get_finance_summary: '📈',
    create_todo: '✅', update_todo: '🔄', delete_todo: '🗑', get_todos: '📋',
    create_habit: '🌱', checkin_habit: '打卡', get_habit_summary: '📊',
    create_diary: '📝', get_diary_summary: '📖',
    remember_memory: '🧠', recall_memory: '🔍',
  }
  const names = {
    log_health: '记录健康', get_health_summary: '查看健康',
    log_finance: '记录账单', get_finance_summary: '查看财务',
    create_todo: '创建待办', update_todo: '更新待办', delete_todo: '删除待办', get_todos: '查看待办',
    create_habit: '创建习惯', checkin_habit: '习惯打卡', get_habit_summary: '查看习惯',
    create_diary: '写日记', get_diary_summary: '查看日记',
    remember_memory: '记住信息', recall_memory: '查询记忆',
  }
  return (
    <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-violet-100 text-violet-700 rounded-full text-xs font-medium">
      <span>{icons[tool] || '🔧'}</span>
      {names[tool] || tool}
    </span>
  )
}

function TaskCard({ task }) {
  const [expanded, setExpanded] = useState(false)
  const statusConfig = {
    pending: { icon: <Clock size={14} />, label: '进行中', cls: 'text-amber-600 bg-amber-50' },
    running: { icon: <Loader size={14} className="animate-spin" />, label: '执行中', cls: 'text-blue-600 bg-blue-50' },
    done: { icon: <CheckCircle size={14} />, label: '已完成', cls: 'text-emerald-600 bg-emerald-50' },
    failed: { icon: <XCircle size={14} />, label: '失败', cls: 'text-red-600 bg-red-50' },
  }
  const cfg = statusConfig[task.status] || statusConfig.pending
  let steps = []
  try { steps = task.steps || [] } catch(e) { steps = [] }

  return (
    <div className="border border-gray-200 rounded-xl p-4 bg-white">
      <div className="flex items-center justify-between gap-3">
        <div className="flex items-center gap-2 min-w-0">
          <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium ${cfg.cls}`}>
            {cfg.icon} {cfg.label}
          </span>
          <span className="text-sm text-gray-600 truncate">{task.goal}</span>
        </div>
        <button onClick={() => setExpanded(!expanded)} className="p-1 hover:bg-gray-100 rounded-lg shrink-0">
          {expanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
        </button>
      </div>
      {expanded && steps.length > 0 && (
        <div className="mt-3 space-y-2">
          {steps.map((s, i) => (
            <div key={i} className="flex items-start gap-2 text-xs">
              <span className="text-gray-400 mt-0.5 shrink-0">{i + 1}.</span>
              <div className="flex-1 min-w-0">
                <StepBadge tool={s.tool} />
                <div className="text-gray-600 mt-1 break-all">
                  {JSON.stringify(s.result)?.length > 100
                    ? JSON.stringify(s.result)?.slice(0, 100) + '...'
                    : JSON.stringify(s.result)}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default function Agent() {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [currentTask, setCurrentTask] = useState(null)
  const [recentTasks, setRecentTasks] = useState([])
  const [activeTab, setActiveTab] = useState('chat')
  const bottomRef = useRef(null)
  const inputRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, currentTask])

  useEffect(() => {
    loadRecentTasks()
  }, [])

  async function loadRecentTasks() {
    try {
      const tasks = await api.agent.tasks()
      setRecentTasks(tasks.slice(0, 5))
    } catch(e) { /* 静默 */ }
  }

  async function send(text) {
    if (!text.trim() || loading) return
    const userMsg = { role: 'user', text: text.trim() }
    setMessages(prev => [...prev, userMsg])
    setInput('')
    setLoading(true)
    setCurrentTask(null)
    try {
      const res = await api.agent.chat({ message: text.trim(), history: messages.slice(-10) })
      const assistantMsg = { role: 'assistant', text: res.reply }
      setMessages(prev => [...prev, assistantMsg])
      setCurrentTask({ goal: text.trim(), steps: res.steps || [], status: res.status })
      await loadRecentTasks()
    } catch(err) {
      setMessages(prev => [...prev, { role: 'assistant', text: `出错了：${err.message}` }])
    } finally {
      setLoading(false)
      inputRef.current?.focus()
    }
  }

  return (
    <div className="flex flex-col h-[calc(100vh-100px)]">
      {/* Header */}
      <div className="mb-4">
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <Zap className="w-7 h-7 text-amber-500" />
          Agent 小周
        </h1>
        <p className="text-gray-500 mt-1">自主规划、闭环执行，你的生活管家</p>
      </div>

      {/* Tab Switcher */}
      <div className="flex gap-1 mb-4 bg-gray-100 rounded-xl p-1 w-fit">
        <button onClick={() => setActiveTab('chat')}
          className={`px-4 py-1.5 rounded-lg text-sm font-medium transition-all ${activeTab === 'chat' ? 'bg-white shadow text-gray-900' : 'text-gray-500 hover:text-gray-700'}`}>
          对话
        </button>
        <button onClick={() => setActiveTab('tasks')}
          className={`px-4 py-1.5 rounded-lg text-sm font-medium transition-all ${activeTab === 'tasks' ? 'bg-white shadow text-gray-900' : 'text-gray-500 hover:text-gray-700'}`}>
          执行记录
        </button>
      </div>

      {activeTab === 'chat' ? (
        <>
          {/* Quick Actions */}
          {messages.length === 0 && (
            <div className="mb-4">
              <p className="text-xs text-gray-400 mb-2 font-medium">快捷指令</p>
              <div className="flex flex-wrap gap-2">
                {QUICK_ACTIONS.map(a => (
                  <button key={a.label} onClick={() => send(a.label)}
                    className="flex items-center gap-1.5 px-3 py-1.5 bg-white border border-gray-200 hover:border-violet-300 hover:bg-violet-50 rounded-xl text-sm text-gray-600 hover:text-violet-700 transition-all">
                    <span>{a.icon}</span> {a.label}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Current Task Panel */}
          {currentTask && (
            <div className="mb-4 border border-violet-200 bg-violet-50 rounded-xl p-3">
              <div className="flex items-center gap-2 mb-2">
                <Zap size={14} className="text-violet-600" />
                <span className="text-xs font-semibold text-violet-700">正在执行</span>
                <span className="text-xs text-gray-500 ml-auto">{currentTask.steps.length} 步</span>
              </div>
              <p className="text-sm font-medium text-gray-800 mb-2">{currentTask.goal}</p>
              {currentTask.steps.length > 0 && (
                <div className="space-y-1.5">
                  {currentTask.steps.map((s, i) => (
                    <div key={i} className="flex items-center gap-2">
                      <span className="text-xs text-gray-400 w-4">{i + 1}.</span>
                      <StepBadge tool={s.tool} />
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Chat Area */}
          <div className="flex-1 overflow-y-auto space-y-4 mb-4 pr-2">
            {messages.length === 0 && (
              <div className="text-center py-10">
                <div className="w-16 h-16 rounded-3xl bg-gradient-to-br from-amber-400 to-orange-500 flex items-center justify-center mx-auto mb-4">
                  <Sparkles className="w-8 h-8 text-white" />
                </div>
                <h2 className="text-xl font-bold mb-2">Agent 小周，随时待命</h2>
                <p className="text-gray-400 max-w-sm mx-auto">告诉我你想做什么，我会帮你规划并执行到底</p>
              </div>
            )}

            {messages.map((msg, i) => (
              <div key={i} className={`flex gap-3 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}>
                <div className={`w-8 h-8 rounded-xl flex items-center justify-center shrink-0 ${msg.role === 'user' ? 'bg-brand-500' : 'bg-gradient-to-br from-amber-400 to-orange-500'}`}>
                  {msg.role === 'user' ? <User size={16} className="text-white" /> : <Bot size={16} className="text-white" />}
                </div>
                <div className={`max-w-[75%] px-4 py-3 rounded-2xl text-sm leading-relaxed ${msg.role === 'user' ? 'bg-brand-500 text-white rounded-tr-sm' : 'bg-gray-100 text-gray-800 rounded-tl-sm'}`}>
                  {msg.text}
                </div>
              </div>
            ))}

            {loading && (
              <div className="flex gap-3">
                <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-amber-400 to-orange-500 flex items-center justify-center">
                  <Bot size={16} className="text-white" />
                </div>
                <div className="bg-gray-100 px-4 py-3 rounded-2xl rounded-tl-sm flex items-center gap-2">
                  <Loader size={14} className="animate-spin text-violet-500" />
                  <span className="text-sm text-gray-500">小周正在思考和执行中...</span>
                </div>
              </div>
            )}
            <div ref={bottomRef} />
          </div>

          {/* Input */}
          <div className="flex gap-3">
            <input
              ref={inputRef}
              className="input-field flex-1"
              placeholder="告诉小周你想做什么，比如：帮我规划这周的健身计划"
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && send(input)}
              disabled={loading}
            />
            <button onClick={() => send(input)} disabled={loading || !input.trim()} className="btn-primary px-5">
              <Send size={18} />
            </button>
          </div>
        </>
      ) : (
        /* Task History Tab */
        <div className="flex-1 overflow-y-auto space-y-3">
          {recentTasks.length === 0 ? (
            <div className="text-center py-16 text-gray-400">
              <Bot size={40} className="mx-auto mb-3 opacity-30" />
              <p>还没有执行记录</p>
            </div>
          ) : (
            recentTasks.map(t => <TaskCard key={t.id} task={t} />)
          )}
        </div>
      )}
    </div>
  )
}

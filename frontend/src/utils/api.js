const BASE = '/api'

async function request(path, options = {}) {
  const token = localStorage.getItem('token')
  const headers = { 'Content-Type': 'application/json', ...(token && { Authorization: `Bearer ${token}` }) }
  const res = await fetch(`${BASE}${path}`, { ...options, headers: { ...headers, ...options.headers } })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || `请求失败 (${res.status})`)
  }
  return res.json()
}

function downloadBlob(path, filename) {
  const token = localStorage.getItem('token')
  fetch(`${BASE}${path}`, {
    headers: { Authorization: `Bearer ${token}` },
  }).then(r => r.blob()).then(blob => {
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    a.click()
    URL.revokeObjectURL(url)
  })
}

export const api = {
  auth: {
    register: (data) => request('/auth/register', { method: 'POST', body: JSON.stringify(data) }),
    login: (data) => request('/auth/token', { method: 'POST', body: JSON.stringify(data) }),
    me: () => request('/auth/me'),
    updateSettings: (data) => request('/auth/settings', { method: 'PATCH', body: JSON.stringify(data) }),
  },
  health: {
    list: (params = {}) => request('/health/records?' + new URLSearchParams(params)),
    create: (data) => request('/health/records', { method: 'POST', body: JSON.stringify(data) }),
    stats: (days = 30) => request(`/health/stats?days=${days}`),
  },
  finance: {
    list: (params = {}) => request('/finance/records?' + new URLSearchParams(params)),
    create: (data) => request('/finance/records', { method: 'POST', body: JSON.stringify(data) }),
    stats: (days = 30) => request(`/finance/stats?days=${days}`),
  },
  productivity: {
    todos: {
      list: (params = {}) => request('/productivity/todos?' + new URLSearchParams(params)),
      create: (data) => request('/productivity/todos', { method: 'POST', body: JSON.stringify(data) }),
      update: (id, completed) => request(`/productivity/todos/${id}?completed=${completed}`, { method: 'PATCH' }),
      delete: (id) => request(`/productivity/todos/${id}`, { method: 'DELETE' }),
    },
    habits: {
      list: () => request('/productivity/habits'),
      create: (data) => request('/productivity/habits', { method: 'POST', body: JSON.stringify(data) }),
      checkin: (id) => request(`/productivity/habits/${id}/checkin`, { method: 'POST' }),
    },
    reminders: {
      list: () => request('/productivity/reminders'),
      create: (data) => request('/productivity/reminders', { method: 'POST', body: JSON.stringify(data) }),
      delete: (id) => request(`/productivity/reminders/${id}`, { method: 'DELETE' }),
    },
  },
  habits: {
    list: () => request('/habits/habits'),
    create: (name, frequency, target) => request(`/habits/habits`, {
      method: 'POST',
      body: JSON.stringify({ name, frequency, target }),
    }),
    checkin: (habit_id, check_date) => request('/habits/checkin', {
      method: 'POST',
      body: JSON.stringify({ habit_id, check_date }),
    }),
    delete: (habit_id) => request(`/habits/habits/${habit_id}`, { method: 'DELETE' }),
    calendar: (year, month) => request(`/habits/calendar/${year}/${month}`),
  },
  weather: {
    current: (city) => request('/weather/current' + (city ? `?city=${encodeURIComponent(city)}` : '')),
  },
  diary: {
    list: (params = {}) => request('/diary/records?' + new URLSearchParams(params)),
    get: (id) => request(`/diary/records/${id}`),
    create: (data) => request('/diary/records', { method: 'POST', body: JSON.stringify(data) }),
    update: (id, data) => request(`/diary/records/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
    delete: (id) => request(`/diary/records/${id}`, { method: 'DELETE' }),
    stats: (days = 30) => request(`/diary/stats?days=${days}`),
  },
  budget: {
    list: (year_month) => request('/budget/budgets' + (year_month ? `?year_month=${year_month}` : '')),
    create: (data) => request('/budget/budgets', { method: 'POST', body: JSON.stringify(data) }),
    delete: (id) => request(`/budget/budgets/${id}`, { method: 'DELETE' }),
    summary: (year_month) => request(`/budget/summary/${year_month}`),
  },
  export: {
    health: () => downloadBlob('/export/health', `health_${new Date().toISOString().slice(0, 10)}.csv`),
    finance: () => downloadBlob('/export/finance', `finance_${new Date().toISOString().slice(0, 10)}.csv`),
    diary: () => downloadBlob('/export/diary', `diary_${new Date().toISOString().slice(0, 10)}.csv`),
    todos: () => downloadBlob('/export/todos', `todos_${new Date().toISOString().slice(0, 10)}.csv`),
  },
  quick: {
    add: (text) => request('/quick/quick-add', { method: 'POST', body: JSON.stringify({ text }) }),
  },
  agent: {
    chat: (data) => request('/agent/chat', { method: 'POST', body: JSON.stringify(data) }),
    tasks: () => request('/agent/tasks'),
    task: (id) => request(`/agent/tasks/${id}`),
    memory: () => request('/agent/memory'),
    setMemory: (key, value) => request('/agent/memory', { method: 'POST', body: JSON.stringify({ key, value }) }),
    delMemory: (key) => request(`/agent/memory/${encodeURIComponent(key)}`, { method: 'DELETE' }),
  },
}

import { useState } from 'react'
import { api } from '../utils/api'
import { useAuthStore } from '../stores/authStore'
import { Settings as SettingsIcon, MapPin, Download, User, Bell } from 'lucide-react'

const EXPORT_ITEMS = [
  { key: 'health', label: '健康数据', desc: '导出体重、步数、睡眠等健康记录' },
  { key: 'finance', label: '财务记录', desc: '导出收支明细、分类统计' },
  { key: 'diary', label: '日记笔记', desc: '导出所有日记内容和标签' },
  { key: 'todos', label: '待办清单', desc: '导出所有待办事项及状态' },
]

export default function Settings() {
  const user = useAuthStore(s => s.user)
  const [location, setLocation] = useState(user?.location || '')
  const [saved, setSaved] = useState(false)
  const [saving, setSaving] = useState(false)
  const [exporting, setExporting] = useState('')

  async function handleSaveLocation(e) {
    e.preventDefault()
    setSaving(true)
    try {
      await api.auth.updateSettings({ location })
      setSaved(true)
      setTimeout(() => setSaved(false), 2000)
    } catch {} finally { setSaving(false) }
  }

  async function handleExport(key) {
    setExporting(key)
    try {
      api.export[key]()
    } catch {} finally { setTimeout(() => setExporting(''), 1000) }
  }

  return (
    <div className="space-y-8 max-w-2xl">
      <div>
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <SettingsIcon className="w-7 h-7 text-gray-500" /> 设置
        </h1>
        <p className="text-gray-500 mt-1">个性化配置与数据管理</p>
      </div>

      <section className="card">
        <h2 className="font-semibold mb-4 flex items-center gap-2">
          <MapPin size={18} className="text-brand-500" /> 天气设置
        </h2>
        <form onSubmit={handleSaveLocation} className="space-y-3">
          <div>
            <label className="text-sm font-medium text-gray-600 mb-1 block">所在城市</label>
            <input className="input-field max-w-sm" placeholder="如：北京、上海、广州"
              value={location} onChange={e => setLocation(e.target.value)} />
            <p className="text-xs text-gray-400 mt-1">用于显示本地天气，建议填写城市名称</p>
          </div>
          <button type="submit" className="btn-primary" disabled={saving}>
            {saving ? '保存中...' : saved ? '✓ 已保存' : '保存设置'}
          </button>
        </form>
      </section>

      <section className="card">
        <h2 className="font-semibold mb-4 flex items-center gap-2">
          <Download size={18} className="text-emerald-500" /> 数据导出
        </h2>
        <p className="text-sm text-gray-500 mb-4">导出您的所有数据，数据以 CSV 格式下载，可在 Excel 中打开分析</p>
        <div className="grid grid-cols-2 gap-3">
          {EXPORT_ITEMS.map(item => (
            <div key={item.key} className="border border-gray-100 rounded-xl p-4 hover:border-brand-200 transition-colors">
              <div className="font-medium text-sm mb-1">{item.label}</div>
              <div className="text-xs text-gray-400 mb-3">{item.desc}</div>
              <button onClick={() => handleExport(item.key)}
                disabled={exporting === item.key}
                className="text-xs px-3 py-1.5 bg-emerald-50 text-emerald-600 rounded-lg hover:bg-emerald-100 transition-colors disabled:opacity-50">
                {exporting === item.key ? '导出中...' : '导出 CSV'}
              </button>
            </div>
          ))}
        </div>
      </section>

      <section className="card">
        <h2 className="font-semibold mb-4 flex items-center gap-2">
          <User size={18} className="text-violet-500" /> 账户信息
        </h2>
        <div className="space-y-2 text-sm">
          <div className="flex gap-2"><span className="text-gray-500 w-16">用户名</span><span className="font-medium">{user?.username || '--'}</span></div>
          <div className="flex gap-2"><span className="text-gray-500 w-16">邮箱</span><span className="font-medium">{user?.email || '--'}</span></div>
        </div>
      </section>

      <section className="card">
        <h2 className="font-semibold mb-4 flex items-center gap-2">
          <Bell size={18} className="text-amber-500" /> 关于
        </h2>
        <div className="space-y-2 text-sm text-gray-500">
          <p>生活小助手 v2.0.0</p>
          <p>一个帮助你管理健康、财务、待办和习惯的私人助理</p>
          <p className="text-xs text-gray-400 mt-3">天气数据由 WeatherAPI.com 提供</p>
        </div>
      </section>
    </div>
  )
}

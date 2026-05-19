import { Link, useLocation } from 'react-router-dom'
import { useAuthStore } from '../stores/authStore'
import {
  LayoutDashboard, Heart, TrendingUp, CheckSquare, MessageCircle, BookOpen,
  Wallet, Calendar, Settings, LogOut, Sparkles, Menu, X, Zap,
} from 'lucide-react'
import { useState } from 'react'

const navItems = [
  { to: '/', icon: LayoutDashboard, label: '仪表盘' },
  { to: '/health', icon: Heart, label: '健康' },
  { to: '/finance', icon: TrendingUp, label: '财务' },
  { to: '/budget', icon: Wallet, label: '预算' },
  { to: '/productivity', icon: CheckSquare, label: '效率' },
  { to: '/calendar', icon: Calendar, label: '习惯日历' },
  { to: '/diary', icon: BookOpen, label: '日记' },
  { to: '/ai', icon: MessageCircle, label: 'AI 助手' },
  { to: '/agent', icon: Zap, label: 'Agent', highlight: true },
]

const bottomItems = [
  { to: '/settings', icon: Settings, label: '设置' },
]

export default function Sidebar() {
  const location = useLocation()
  const logout = useAuthStore((s) => s.logout)
  const [mobileOpen, setMobileOpen] = useState(false)

  return (
    <>
      <aside className="hidden md:flex flex-col w-64 bg-white border-r border-gray-100 min-h-screen fixed left-0 top-0 p-4 z-20">
        <div className="flex items-center gap-3 px-2 mb-6">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-brand-500 to-cyan-400 flex items-center justify-center">
            <Sparkles className="w-5 h-5 text-white" />
          </div>
          <div>
            <div className="font-bold text-gray-900">生活小助手</div>
            <div className="text-xs text-gray-400">v2.0</div>
          </div>
        </div>

        <nav className="flex-1 space-y-0.5 overflow-y-auto">
          {navItems.map(({ to, icon: Icon, label, highlight }) => (
            <Link
              key={to}
              to={to}
              className={`nav-link ${highlight ? 'highlight' : ''} ${location.pathname === to ? 'active' : ''}`}
            >
              <Icon size={20} />
              {label}
            </Link>
          ))}
        </nav>

        <div className="border-t border-gray-100 pt-3 mt-2 space-y-0.5">
          {bottomItems.map(({ to, icon: Icon, label, highlight }) => (
            <Link
              key={to}
              to={to}
              className={`nav-link ${highlight ? 'highlight' : ''} ${location.pathname === to ? 'active' : ''}`}
            >
              <Icon size={20} />
              {label}
            </Link>
          ))}
          <button onClick={logout} className="nav-link text-red-500 hover:bg-red-50 w-full">
            <LogOut size={20} />
            退出登录
          </button>
        </div>
      </aside>

      <div className="md:hidden fixed top-0 left-0 right-0 z-30 bg-white border-b border-gray-100 px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-brand-500 to-cyan-400 flex items-center justify-center">
            <Sparkles className="w-4 h-4 text-white" />
          </div>
          <span className="font-bold">生活小助手</span>
        </div>
        <button onClick={() => setMobileOpen(!mobileOpen)} className="p-2 rounded-lg hover:bg-gray-100">
          {mobileOpen ? <X size={20} /> : <Menu size={20} />}
        </button>
      </div>

      {mobileOpen && (
        <div className="md:hidden fixed inset-0 z-20 bg-white pt-16">
          <nav className="p-4 space-y-0.5">
            {[...navItems, ...bottomItems].map(({ to, icon: Icon, label, highlight }) => (
              <Link
                key={to}
                to={to}
                onClick={() => setMobileOpen(false)}
                className={`nav-link ${highlight ? 'highlight' : ''} ${location.pathname === to ? 'active' : ''}`}
              >
                <Icon size={20} />
                {label}
              </Link>
            ))}
            <button onClick={logout} className="nav-link text-red-500 hover:bg-red-50 w-full">
              <LogOut size={20} />
              退出登录
            </button>
          </nav>
        </div>
      )}
    </>
  )
}

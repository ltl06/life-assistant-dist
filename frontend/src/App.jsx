import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { useAuthStore } from './stores/authStore'
import { useEffect } from 'react'
import Dashboard from './pages/Dashboard'
import Login from './pages/Login'
import Register from './pages/Register'
import Health from './pages/Health'
import Finance from './pages/Finance'
import Productivity from './pages/Productivity'
import AIChat from './pages/AIChat'
import Agent from './pages/Agent'
import Diary from './pages/Diary'
import Budget from './pages/Budget'
import CalendarPage from './pages/CalendarPage'
import Settings from './pages/Settings'
import Sidebar from './components/Sidebar'
import QuickFloat from './components/QuickFloat'

function Layout({ children }) {
  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <main className="flex-1 md:ml-64 p-4 md:p-8 max-w-5xl md:max-w-6xl w-full mx-auto pt-16 md:pt-0">
        {children}
      </main>
      <QuickFloat />
    </div>
  )
}

function ProtectedRoute({ children }) {
  const token = useAuthStore((s) => s.token)
  const fetchUser = useAuthStore((s) => s.fetchUser)
  useEffect(() => { fetchUser() }, [])
  if (!token) return <Navigate to="/login" replace />
  return <Layout>{children}</Layout>
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
        <Route path="/health" element={<ProtectedRoute><Health /></ProtectedRoute>} />
        <Route path="/finance" element={<ProtectedRoute><Finance /></ProtectedRoute>} />
        <Route path="/productivity" element={<ProtectedRoute><Productivity /></ProtectedRoute>} />
        <Route path="/ai" element={<ProtectedRoute><AIChat /></ProtectedRoute>} />
        <Route path="/agent" element={<ProtectedRoute><Agent /></ProtectedRoute>} />
        <Route path="/diary" element={<ProtectedRoute><Diary /></ProtectedRoute>} />
        <Route path="/budget" element={<ProtectedRoute><Budget /></ProtectedRoute>} />
        <Route path="/calendar" element={<ProtectedRoute><CalendarPage /></ProtectedRoute>} />
        <Route path="/settings" element={<ProtectedRoute><Settings /></ProtectedRoute>} />
      </Routes>
    </BrowserRouter>
  )
}

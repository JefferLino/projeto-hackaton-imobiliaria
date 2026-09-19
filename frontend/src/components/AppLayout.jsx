import { useState } from 'react'
import { LogOut, Menu } from 'lucide-react'
import { Outlet, useNavigate } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { logout } from '../services/auth'
import Sidebar from './Sidebar'
import ErrorBoundary from './ErrorBoundary'

export default function AppLayout() {
  const navigate = useNavigate()
  const [sidebarOpen, setSidebarOpen] = useState(false)

  const user = (() => {
    try {
      return JSON.parse(localStorage.getItem('auth_user') || 'null')
    } catch {
      return null
    }
  })()

  function handleLogout() {
    logout()
    navigate('/login', { replace: true })
  }

  return (
    <div className="min-h-screen flex flex-col">
      <header className="border-b px-4 py-3 flex items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <Button
            variant="ghost"
            size="icon"
            className="md:hidden"
            onClick={() => setSidebarOpen(true)}
            aria-label="Abrir menu"
          >
            <Menu className="h-5 w-5" />
          </Button>
          <span className="text-sm text-muted-foreground">
            {user?.nome ? `Olá, ${user.nome}` : 'Sistema de Gestão'}
          </span>
        </div>
        <Button variant="ghost" size="sm" onClick={handleLogout}>
          <LogOut className="h-4 w-4 mr-2" />
          Sair
        </Button>
      </header>
      <div className="flex flex-1 overflow-hidden">
        <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />
        <main className="flex-1 overflow-auto">
          <ErrorBoundary>
            <Outlet />
          </ErrorBoundary>
        </main>
      </div>
    </div>
  )
}

import { Users, LayoutDashboard } from 'lucide-react'
import { Link, useLocation } from 'react-router-dom'
import { cn } from '@/lib/utils'

const NAV_ITEMS = [
  { label: 'Corretores', href: '/corretores', icon: Users },
  { label: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
]

export default function Sidebar({ isOpen, onClose }) {
  const location = useLocation()

  const nav = (
    <nav className="flex flex-col gap-1 p-3">
      {NAV_ITEMS.map(({ label, href, icon: Icon }) => {
        const active = location.pathname === href
        return (
          <Link
            key={href}
            to={href}
            onClick={onClose}
            className={cn(
              'flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors',
              active
                ? 'bg-accent text-accent-foreground'
                : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground'
            )}
          >
            <Icon className="h-4 w-4 shrink-0" />
            {label}
          </Link>
        )
      })}
    </nav>
  )

  return (
    <>
      {/* Desktop sidebar */}
      <aside className="hidden md:flex flex-col w-64 border-r shrink-0 bg-background">
        {nav}
      </aside>

      {/* Mobile drawer */}
      {isOpen && (
        <div
          className="fixed inset-0 z-40 md:hidden"
          onClick={onClose}
          aria-hidden="true"
        >
          <div className="absolute inset-0 bg-black/40" />
        </div>
      )}
      <aside
        className={cn(
          'fixed inset-y-0 left-0 z-50 w-64 border-r bg-background transition-transform duration-200 md:hidden flex flex-col',
          isOpen ? 'translate-x-0' : '-translate-x-full'
        )}
      >
        {nav}
      </aside>
    </>
  )
}

import type { ReactNode } from 'react'
import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { AppShell } from '@/components/app-shell'
import { useAuthStore } from '@/stores/auth-store'

export function ProtectedLayout() {
  return (
    <AppShell>
      <Outlet />
    </AppShell>
  )
}

export function RootRedirect() {
  const user = useAuthStore((state) => state.user)
  return <Navigate to={user ? '/notes/overview' : '/login'} replace />
}

export function RequireAuthBoundary() {
  const location = useLocation()
  const user = useAuthStore((state) => state.user)

  if (!user) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />
  }

  return <Outlet />
}

export function RoutePending({ message = '页面加载中...' }: { message?: string }) {
  return (
    <div className="fabric-panel flex min-h-[240px] items-center justify-center">
      <div className="text-sm text-cloth-muted">{message}</div>
    </div>
  )
}

export function RouteSectionPending({ children }: { children?: ReactNode }) {
  return (
    <div className="fabric-panel flex min-h-[240px] items-center justify-center">
      {children ?? <div className="text-sm text-cloth-muted">页面加载中...</div>}
    </div>
  )
}

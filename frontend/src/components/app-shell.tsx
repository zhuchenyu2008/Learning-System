import { useEffect, useMemo, useState } from 'react'
import { NavLink, useLocation, useNavigate } from 'react-router-dom'
import clsx from 'clsx'
import { ChevronDown, LogOut, Menu } from 'lucide-react'
import { navSections, roleMeta } from '@/app/navigation'
import { useAuthStore } from '@/stores/auth-store'
import { apiClient } from '@/lib/api-client'

interface AppShellProps {
  children: React.ReactNode
}

export function AppShell({ children }: AppShellProps) {
  const location = useLocation()
  const navigate = useNavigate()
  const { user, accessToken, refreshToken, clearSession } = useAuthStore()
  const [mobileNavOpen, setMobileNavOpen] = useState(false)
  const visibleSections = useMemo(
    () =>
      navSections.map((section) => ({
        ...section,
        children: section.children.filter((item) => !(user?.role === 'viewer' && item.hiddenForViewer)),
      })),
    [user?.role],
  )
  const [expandedSections, setExpandedSections] = useState<Record<string, boolean>>(() =>
    Object.fromEntries(navSections.map((section) => [section.path, false])),
  )

  const activeSection = useMemo(
    () => visibleSections.find((section) => location.pathname.startsWith(section.path)) ?? visibleSections[0] ?? navSections[0],
    [location.pathname, visibleSections],
  )

  const activeLeaf = activeSection.children.find((item) => location.pathname === item.path) ?? activeSection.children[0]
  const roleInfo = user ? roleMeta[user.role] : null
  const pageTitle = activeLeaf ? `${activeSection.label}/${activeLeaf.label}` : activeSection.label

  useEffect(() => {
    setExpandedSections((current) => ({
      ...Object.fromEntries(navSections.map((section) => [section.path, false])),
      ...current,
      [activeSection.path]: true,
    }))
  }, [activeSection.path])

  useEffect(() => {
    setMobileNavOpen(false)
  }, [location.pathname])

  const handleLogout = async () => {
    try {
      if (refreshToken) {
        await apiClient.auth.logout(refreshToken, accessToken)
      }
    } catch {
      // noop: logout should still clear local state
    } finally {
      clearSession()
      navigate('/login', { replace: true })
    }
  }

  const toggleSection = (path: string) => {
    setExpandedSections((current) => ({
      ...current,
      [path]: !current[path],
    }))
  }

  const sidebar = (
    <div className="flex h-full flex-col gap-4">
      <div>
        <p className="text-xs uppercase tracking-[0.24em] text-cloth-accent">learning-system</p>
        <h1 className="mt-2 font-serif text-2xl text-cloth-ink">学习系统</h1>
      </div>

      <nav className="space-y-3">
        {visibleSections.map((section) => {
          const Icon = section.icon
          const isExpanded = expandedSections[section.path]
          const isActive = location.pathname.startsWith(section.path)

          return (
            <section key={section.path} className="rounded-2xl border border-cloth-line/70 bg-white/35">
              <button
                type="button"
                onClick={() => toggleSection(section.path)}
                className={clsx(
                  'flex w-full items-center gap-3 rounded-2xl px-4 py-3 text-left text-sm',
                  isActive ? 'text-cloth-ink' : 'text-cloth-muted hover:text-cloth-ink',
                )}
              >
                <Icon className="h-4 w-4" />
                <span className="font-medium">{section.label}</span>
                <ChevronDown className={clsx('ml-auto h-4 w-4 transition-transform', isExpanded && 'rotate-180')} />
              </button>

              {isExpanded ? (
                <div className="space-y-2 px-3 pb-3">
                  {section.children.map((item) => {
                    const locked = item.adminOnly && user?.role !== 'admin'
                    return (
                      <NavLink
                        key={item.path}
                        to={item.path}
                        className={({ isActive: leafActive }) =>
                          clsx(
                            'flex items-center justify-between gap-3 rounded-xl border px-3 py-2 text-sm',
                            leafActive
                              ? 'border-cloth-accent/50 bg-cloth-panelStrong text-cloth-ink shadow-panel'
                              : 'border-cloth-line/60 bg-white/50 text-cloth-muted hover:border-cloth-accent/35 hover:text-cloth-ink',
                            locked && 'opacity-70',
                          )
                        }
                        title={locked ? '普通用户不可执行管理操作' : undefined}
                      >
                        <span>{item.label}</span>
                        {locked ? <span className="rounded-full bg-cloth-panel px-2 py-0.5 text-[10px] uppercase tracking-[0.18em]">只读</span> : null}
                      </NavLink>
                    )
                  })}
                </div>
              ) : null}
            </section>
          )
        })}
      </nav>

      {roleInfo ? (
        <section className="mt-auto rounded-2xl border border-cloth-line/80 bg-white/55 p-4">
          <div className="flex items-center gap-3">
            <roleInfo.icon className="h-5 w-5 text-cloth-accent" />
            <div>
              <p className="text-sm font-semibold text-cloth-ink">{user?.username}</p>
              <p className="text-xs uppercase tracking-[0.18em] text-cloth-muted">{roleInfo.label}</p>
            </div>
          </div>
          <p className="mt-3 text-sm text-cloth-muted">{roleInfo.description}</p>
          <button type="button" onClick={handleLogout} className="fabric-btn mt-4 w-full">
            <LogOut className="h-4 w-4" />
            退出登录
          </button>
        </section>
      ) : null}
    </div>
  )

  return (
    <div className="min-h-screen p-3 md:p-6">
      <div className="mx-auto grid min-h-[calc(100vh-1.5rem)] max-w-[1600px] grid-cols-1 gap-4 xl:grid-cols-[300px_minmax(0,1fr)]">
        <aside className="fabric-panel scrollbar-thin hidden overflow-auto p-5 xl:block">{sidebar}</aside>

        {mobileNavOpen ? (
          <div className="fixed inset-0 z-40 xl:hidden" aria-hidden="true">
            <div className="absolute inset-0 bg-black/30" onClick={() => setMobileNavOpen(false)} />
            <aside className="fabric-panel scrollbar-thin absolute left-3 top-3 bottom-3 w-[min(88vw,360px)] overflow-auto p-4">
              {sidebar}
            </aside>
          </div>
        ) : null}

        <main className="min-w-0 space-y-4">
          <header className="fabric-panel flex flex-col gap-3 p-4 md:p-5 lg:flex-row lg:items-center lg:justify-between">
            <div className="flex min-w-0 items-center gap-3">
              <button
                type="button"
                className="fabric-btn h-10 w-10 shrink-0 p-0 xl:hidden"
                onClick={() => setMobileNavOpen(true)}
                aria-label="打开导航菜单"
              >
                <Menu className="h-4 w-4" />
              </button>
              <h2 className="truncate text-lg font-semibold text-cloth-ink md:text-xl">{pageTitle}</h2>
            </div>
            <button type="button" onClick={handleLogout} className="fabric-btn hidden sm:inline-flex xl:hidden">
              <LogOut className="h-4 w-4" />
              退出登录
            </button>
          </header>
          {children}
        </main>
      </div>
    </div>
  )
}

import { useMemo } from 'react'
import { NavLink, useLocation, useNavigate } from 'react-router-dom'
import clsx from 'clsx'
import { ChevronRight, LogOut } from 'lucide-react'
import { navSections, roleMeta, shellQuickLinks } from '@/app/navigation'
import { useAuthStore } from '@/stores/auth-store'
import { apiClient } from '@/lib/api-client'

interface AppShellProps {
  children: React.ReactNode
}

export function AppShell({ children }: AppShellProps) {
  const location = useLocation()
  const navigate = useNavigate()
  const { user, accessToken, refreshToken, clearSession } = useAuthStore()

  const activeSection = useMemo(
    () => navSections.find((section) => location.pathname.startsWith(section.path)) ?? navSections[0],
    [location.pathname],
  )

  const activeLeaf = activeSection.children.find((item) => location.pathname === item.path) ?? activeSection.children[0]
  const roleInfo = user ? roleMeta[user.role] : null

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

  return (
    <div className="min-h-screen p-4 md:p-6">
      <div className="mx-auto grid min-h-[calc(100vh-2rem)] max-w-[1600px] grid-cols-1 gap-4 xl:grid-cols-[96px_220px_260px_minmax(0,1fr)]">
        <aside className="fabric-panel hidden xl:flex xl:flex-col xl:items-center xl:justify-between xl:px-3 xl:py-5">
          <div className="flex flex-col items-center gap-4">
            <div className="flex h-14 w-14 items-center justify-center rounded-2xl border border-cloth-line bg-cloth-panelStrong text-lg font-semibold text-cloth-accent shadow-panel">
              LS
            </div>
            <div className="space-y-3">
              {navSections.map((section) => {
                const Icon = section.icon
                const isActive = location.pathname.startsWith(section.path)
                return (
                  <NavLink
                    key={section.path}
                    to={section.children[0]?.path ?? section.path}
                    className={clsx(
                      'flex h-12 w-12 items-center justify-center rounded-2xl border text-cloth-muted',
                      isActive
                        ? 'border-cloth-accent/50 bg-cloth-accent text-white shadow-panel'
                        : 'border-cloth-line bg-cloth-panelStrong/70 hover:border-cloth-accent/40 hover:text-cloth-accent',
                    )}
                    title={section.label}
                  >
                    <Icon className="h-5 w-5" />
                  </NavLink>
                )
              })}
            </div>
          </div>
          <button type="button" onClick={handleLogout} className="fabric-btn h-12 w-12 p-0" title="退出登录">
            <LogOut className="h-4 w-4" />
          </button>
        </aside>

        <aside className="fabric-panel scrollbar-thin flex min-h-[180px] flex-col gap-5 overflow-auto p-5">
          <div>
            <p className="text-xs uppercase tracking-[0.24em] text-cloth-accent">learning-system</p>
            <h1 className="mt-2 font-serif text-2xl text-cloth-ink">织物质感学习台</h1>
            <p className="mt-2 text-sm text-cloth-muted">本地 Markdown / Obsidian 优先，数据库负责索引与任务状态。</p>
          </div>

          <div className="space-y-3">
            <p className="text-xs uppercase tracking-[0.2em] text-cloth-muted">一级导航</p>
            {navSections.map((section) => {
              const Icon = section.icon
              const isActive = section.path === activeSection.path
              return (
                <NavLink
                  key={section.path}
                  to={section.children[0]?.path ?? section.path}
                  className={clsx(
                    'flex items-center gap-3 rounded-xl border px-3 py-3 text-sm',
                    isActive
                      ? 'border-cloth-accent/45 bg-white/70 text-cloth-ink shadow-panel'
                      : 'border-transparent text-cloth-muted hover:border-cloth-line hover:bg-white/45',
                  )}
                >
                  <Icon className="h-4 w-4" />
                  <span>{section.label}</span>
                  <ChevronRight className="ml-auto h-4 w-4 opacity-60" />
                </NavLink>
              )
            })}
          </div>

          <div className="space-y-3">
            <p className="text-xs uppercase tracking-[0.2em] text-cloth-muted">系统特征</p>
            <div className="grid gap-2">
              {shellQuickLinks.map(({ label, icon: Icon }) => (
                <div key={label} className="rounded-xl border border-cloth-line/70 bg-white/40 px-3 py-2 text-sm text-cloth-muted">
                  <div className="flex items-center gap-2">
                    <Icon className="h-4 w-4 text-cloth-accent" />
                    <span>{label}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </aside>

        <aside className="fabric-panel scrollbar-thin flex min-h-[180px] flex-col gap-4 overflow-auto p-5">
          <div>
            <p className="text-xs uppercase tracking-[0.2em] text-cloth-muted">二级导航</p>
            <h2 className="mt-1 font-serif text-2xl text-cloth-ink">{activeSection.label}</h2>
          </div>

          <nav className="space-y-2">
            {activeSection.children.map((item) => {
              const locked = item.adminOnly && user?.role !== 'admin'
              return (
                <NavLink
                  key={item.path}
                  to={item.path}
                  className={({ isActive }) =>
                    clsx(
                      'block rounded-xl border px-4 py-3 text-sm',
                      isActive
                        ? 'border-cloth-accent/50 bg-cloth-panelStrong text-cloth-ink shadow-panel'
                        : 'border-cloth-line/70 bg-white/40 text-cloth-muted hover:border-cloth-accent/35 hover:text-cloth-ink',
                      locked && 'opacity-70',
                    )
                  }
                  title={locked ? '普通用户仅可查看禁用态，不可执行管理操作' : undefined}
                >
                  <div className="flex items-center justify-between gap-3">
                    <span>{item.label}</span>
                    {locked ? <span className="rounded-full bg-cloth-panel px-2 py-0.5 text-[10px] uppercase tracking-[0.18em]">只读</span> : null}
                  </div>
                </NavLink>
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
              <button type="button" onClick={handleLogout} className="fabric-btn mt-4 w-full xl:hidden">
                <LogOut className="h-4 w-4" />
                退出登录
              </button>
            </section>
          ) : null}
        </aside>

        <main className="min-w-0 space-y-4">
          <header className="fabric-panel flex flex-col gap-3 p-5 lg:flex-row lg:items-end lg:justify-between">
            <div>
              <p className="text-xs uppercase tracking-[0.22em] text-cloth-accent">{activeSection.label}</p>
              <h2 className="mt-1 font-serif text-3xl text-cloth-ink">{activeLeaf?.label ?? activeSection.label}</h2>
              <p className="mt-2 text-sm text-cloth-muted">SA-04 仅实现前端壳层、主题、登录守卫、权限态组件与基础客户端，为后续模块页面预留挂载点。</p>
            </div>
            <div className="rounded-2xl border border-cloth-line/80 bg-white/50 px-4 py-3 text-sm text-cloth-muted">
              <span className="font-medium text-cloth-ink">角色策略：</span>
              未登录禁止进入；普通用户保留页面入口，但管理能力以灰态禁用呈现。
            </div>
          </header>
          {children}
        </main>
      </div>
    </div>
  )
}

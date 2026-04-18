import { useQuery } from '@tanstack/react-query'
import { Activity, Clock3, RefreshCw, ShieldCheck, UserRound } from 'lucide-react'
import { ApiError } from '@/lib/api-client'
import { settingsApi } from '@/lib/settings-api'
import { EmptyStateCard, ReadonlyNotice, SectionStatus, SettingsSection } from '@/components/settings-section'
import { PagePlaceholder } from '@/components/page-placeholder'
import { PermissionButton } from '@/components/permission-gate'
import { useAuthStore } from '@/stores/auth-store'

function formatDate(value?: string | null) {
  if (!value) return '—'
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString()
}

export function SettingsUsersPage() {
  const isAdmin = useAuthStore((state) => state.user?.role === 'admin')

  const usersQuery = useQuery({ queryKey: ['admin', 'users'], queryFn: () => settingsApi.listUsers(), enabled: isAdmin })
  const activityQuery = useQuery({ queryKey: ['admin', 'user-activity'], queryFn: () => settingsApi.listUserActivity(), enabled: isAdmin })
  const loginEventsQuery = useQuery({ queryKey: ['admin', 'login-events'], queryFn: () => settingsApi.listLoginEvents(), enabled: isAdmin })

  const usersUnavailable = isAdmin && usersQuery.data == null && !usersQuery.isLoading && !usersQuery.error
  const activityUnavailable = isAdmin && activityQuery.data == null && !activityQuery.isLoading && !activityQuery.error
  const eventsUnavailable = isAdmin && loginEventsQuery.data == null && !loginEventsQuery.isLoading && !loginEventsQuery.error

  return (
    <PagePlaceholder
      title="用户与登录情况"
      description="管理员可查看用户列表、角色状态、登录事件与活动概览；若后端未就绪则以结构化占位降级。"
      className="space-y-4"
      actions={
        <PermissionButton
          allowed={isAdmin}
          reason="仅管理员可刷新用户与审计数据"
          onClick={() => {
            void usersQuery.refetch()
            void activityQuery.refetch()
            void loginEventsQuery.refetch()
          }}
        >
          <RefreshCw className="h-4 w-4" />
          刷新列表
        </PermissionButton>
      }
    >
      <ReadonlyNotice isAdmin={isAdmin} reason="普通用户可查看后台信息结构，但用户管理与审计能力保持禁用。" />

      <SettingsSection title="用户列表" description="展示角色、状态、最近登录时间与创建时间。" className="md:col-span-2 xl:col-span-2">
        {usersQuery.error ? (
          <div className="rounded-xl border border-red-200 bg-red-50/80 p-4 text-sm text-red-700">
            {usersQuery.error instanceof ApiError ? usersQuery.error.message : '用户列表加载失败。'}
          </div>
        ) : usersQuery.data?.length ? (
          <div className="overflow-auto">
            <table className="min-w-full text-sm">
              <thead>
                <tr className="border-b border-cloth-line/70 text-left text-cloth-muted">
                  <th className="px-3 py-2">用户</th>
                  <th className="px-3 py-2">角色</th>
                  <th className="px-3 py-2">状态</th>
                  <th className="px-3 py-2">最近登录</th>
                </tr>
              </thead>
              <tbody>
                {usersQuery.data.map((user) => (
                  <tr key={String(user.id)} className="border-b border-cloth-line/40 text-cloth-ink">
                    <td className="px-3 py-3">
                      <div className="flex items-center gap-2">
                        <UserRound className="h-4 w-4 text-cloth-accent" />
                        <div>
                          <div className="font-medium">{user.username}</div>
                          <div className="text-xs text-cloth-muted">{user.email || '无邮箱'}</div>
                        </div>
                      </div>
                    </td>
                    <td className="px-3 py-3">{user.role}</td>
                    <td className="px-3 py-3">
                      <SectionStatus status={user.is_active ? 'active' : 'inactive'} tone={user.is_active ? 'success' : 'warning'} />
                    </td>
                    <td className="px-3 py-3">{formatDate(user.last_login_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <EmptyStateCard title={usersUnavailable ? '用户接口未就绪' : '暂无用户数据'} description={usersUnavailable ? '保留表结构与管理员入口，但不伪造 `/admin/users` 返回结果。' : '当前没有可展示的用户记录。'} />
        )}
      </SettingsSection>

      <SettingsSection title="用户活动概览" description="观看时长、复习次数、最近活跃时间等。" className="md:col-span-2 xl:col-span-1">
        {activityQuery.error ? (
          <div className="rounded-xl border border-red-200 bg-red-50/80 p-4 text-sm text-red-700">
            {activityQuery.error instanceof ApiError ? activityQuery.error.message : '活动数据加载失败。'}
          </div>
        ) : activityQuery.data?.length ? (
          <div className="space-y-3">
            {activityQuery.data.slice(0, 6).map((item, index) => (
              <div key={String(item.id ?? item.user_id ?? index)} className="rounded-xl border border-cloth-line/70 bg-white/45 p-4">
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <p className="text-sm font-semibold text-cloth-ink">{item.username ?? `用户 #${item.user_id ?? index + 1}`}</p>
                    <p className="mt-1 text-xs text-cloth-muted">最近活跃：{formatDate(item.last_seen_at as string | null | undefined)}</p>
                  </div>
                  <Activity className="h-4 w-4 text-cloth-accent" />
                </div>
                <div className="mt-3 grid gap-2 text-xs text-cloth-muted">
                  <div className="flex items-center gap-2"><Clock3 className="h-3.5 w-3.5" />观看时长：{String(item.total_watch_seconds ?? 0)} 秒</div>
                  <div className="flex items-center gap-2"><ShieldCheck className="h-3.5 w-3.5" />复习次数：{String(item.review_count ?? 0)}</div>
                  <div className="flex items-center gap-2"><Activity className="h-3.5 w-3.5" />页面访问：{String(item.page_view_count ?? 0)} 次</div>
                  <div className="flex items-center gap-2"><UserRound className="h-3.5 w-3.5" />笔记查看：{String(item.note_view_count ?? 0)} 次</div>
                  <div className="flex items-center gap-2"><Clock3 className="h-3.5 w-3.5" />复习时长：{String(item.review_watch_seconds ?? 0)} 秒</div>
                  <div className="flex items-center gap-2"><ShieldCheck className="h-3.5 w-3.5" />最近事件：{String(item.last_event_type ?? '—')}</div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <EmptyStateCard title={activityUnavailable ? '活动接口未就绪' : '暂无活动数据'} description={activityUnavailable ? '当前仅显示结构化活动面板。' : '后续用户产生观看与复习行为后会在此显示。'} />
        )}
      </SettingsSection>

      <SettingsSection title="登录事件" description="展示最近登录审计事件、事件类型与时间。" className="md:col-span-2 xl:col-span-3">
        {loginEventsQuery.error ? (
          <div className="rounded-xl border border-red-200 bg-red-50/80 p-4 text-sm text-red-700">
            {loginEventsQuery.error instanceof ApiError ? loginEventsQuery.error.message : '登录事件加载失败。'}
          </div>
        ) : loginEventsQuery.data?.length ? (
          <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
            {loginEventsQuery.data.slice(0, 9).map((event, index) => (
              <article key={String(event.id ?? index)} className="rounded-xl border border-cloth-line/70 bg-white/45 p-4">
                <p className="text-sm font-semibold text-cloth-ink">{event.username ?? `用户 #${event.user_id ?? index + 1}`}</p>
                <p className="mt-2 text-sm text-cloth-muted">事件：{String(event.event_type ?? 'login')}</p>
                <p className="mt-1 text-xs text-cloth-muted">时间：{formatDate(event.created_at as string | null | undefined)}</p>
                <p className="mt-1 text-xs text-cloth-muted">IP：{String(event.ip_address ?? '—')}</p>
              </article>
            ))}
          </div>
        ) : (
          <EmptyStateCard title={eventsUnavailable ? '登录事件接口未就绪' : '暂无登录事件'} description={eventsUnavailable ? '保持审计面板可见，但不会假造事件列表。' : '当用户登录后，这里会展示最近事件。'} />
        )}
      </SettingsSection>
    </PagePlaceholder>
  )
}

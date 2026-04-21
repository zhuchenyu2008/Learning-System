import { useQuery } from '@tanstack/react-query'
import { Clock3, DatabaseZap, RefreshCw, TimerReset } from 'lucide-react'
import { ApiError } from '@/lib/api-client'
import { settingsApi } from '@/lib/settings-api'
import { PagePlaceholder } from '@/components/page-placeholder'
import { PermissionButton } from '@/components/permission-gate'
import { EmptyStateCard, ErrorStateCard, LoadingStateCard, ReadonlyNotice, SectionStatus, SettingsField, SettingsSection } from '@/components/settings-section'
import { useAuthStore } from '@/stores/auth-store'

function formatTimestamp(value?: string | null) {
  if (!value) return '—'
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString()
}

function stringifyPayload(payload?: Record<string, unknown> | null) {
  if (!payload || !Object.keys(payload).length) return '—'
  try {
    return JSON.stringify(payload, null, 2)
  } catch {
    return 'payload unavailable'
  }
}

export function SettingsJobsPage() {
  const isAdmin = useAuthStore((state) => state.user?.role === 'admin')

  const schedulerQuery = useQuery({ queryKey: ['scheduler', 'tasks'], queryFn: () => settingsApi.listSchedulerTasks(), enabled: isAdmin })
  const jobsQuery = useQuery({ queryKey: ['jobs'], queryFn: () => settingsApi.listJobs(), enabled: isAdmin })
  const systemQuery = useQuery({ queryKey: ['settings', 'system', 'jobs-page'], queryFn: () => settingsApi.getSystemSettings(), enabled: isAdmin })

  const schedulerUnavailable = isAdmin && schedulerQuery.data == null && !schedulerQuery.isLoading && !schedulerQuery.error
  const systemUnavailable = isAdmin && systemQuery.data == null && !systemQuery.isLoading && !systemQuery.error

  return (
    <PagePlaceholder
      title="任务与调度"
      description="查看调度任务、后台 job 与系统调度相关设置。"
      className="space-y-4"
      actions={
        <PermissionButton
          allowed={isAdmin}
          reason="仅管理员可刷新任务与调度信息"
          onClick={() => {
            void schedulerQuery.refetch()
            void jobsQuery.refetch()
            void systemQuery.refetch()
          }}
        >
          <RefreshCw className="h-4 w-4" />
          刷新任务状态
        </PermissionButton>
      }
    >
      <ReadonlyNotice isAdmin={isAdmin} reason="普通用户仅可查看任务和调度信息，不可修改任何调度策略。" />

      <SettingsSection title="系统调度策略" description="注册开关、时区与复习保留目标。" className="md:col-span-2 xl:col-span-1">
        {systemQuery.isLoading ? (
          <LoadingStateCard title="正在加载系统调度策略" description="读取系统级开关、时区与保留策略。" />
        ) : systemQuery.error ? (
          <ErrorStateCard description={systemQuery.error instanceof ApiError ? systemQuery.error.message : '系统配置加载失败。'} />
        ) : systemQuery.data ? (
          <div className="space-y-4">
            <SettingsField label="allow_registration">
              <div className="rounded-xl border border-cloth-line/70 bg-white/45 px-3 py-2 text-sm text-cloth-ink">{systemQuery.data.allow_registration ? '开启' : '关闭'}</div>
            </SettingsField>
            <SettingsField label="timezone">
              <div className="rounded-xl border border-cloth-line/70 bg-white/45 px-3 py-2 text-sm text-cloth-ink">{systemQuery.data.timezone}</div>
            </SettingsField>
            <SettingsField label="review_retention_target">
              <div className="rounded-xl border border-cloth-line/70 bg-white/45 px-3 py-2 text-sm text-cloth-ink">{systemQuery.data.review_retention_target}</div>
            </SettingsField>
          </div>
        ) : (
          <EmptyStateCard title={systemUnavailable ? '系统设置接口未就绪' : '暂无系统配置'} description={systemUnavailable ? '当前仅保留任务策略展示框架。' : '系统设置为空时将在此展示占位状态。'} />
        )}
      </SettingsSection>

      <SettingsSection title="Scheduler Tasks" description="已注册调度任务。" className="md:col-span-2 xl:col-span-2">
        {schedulerQuery.isLoading ? (
          <LoadingStateCard title="正在加载调度任务" description="读取 `/scheduler/tasks` 返回的注册任务。" />
        ) : schedulerQuery.error ? (
          <ErrorStateCard description={schedulerQuery.error instanceof ApiError ? schedulerQuery.error.message : '调度任务加载失败。'} />
        ) : schedulerQuery.data?.length ? (
          <div className="grid gap-3 md:grid-cols-2">
            {schedulerQuery.data.map((task) => (
              <article key={task.name} className="rounded-xl border border-cloth-line/70 bg-white/45 p-4">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <p className="text-sm font-semibold text-cloth-ink">{task.name}</p>
                    <p className="mt-1 text-xs text-cloth-muted">{task.description || '暂无描述'}</p>
                  </div>
                  <TimerReset className="h-4 w-4 text-cloth-accent" />
                </div>
                <div className="mt-3 flex flex-wrap gap-2 text-xs text-cloth-muted">
                  <SectionStatus status={task.enabled === false ? 'disabled' : 'enabled'} tone={task.enabled === false ? 'warning' : 'success'} />
                  <span className="rounded-full border border-cloth-line/80 bg-white/70 px-2.5 py-1">{task.schedule || 'schedule unavailable'}</span>
                </div>
              </article>
            ))}
          </div>
        ) : (
          <EmptyStateCard title={schedulerUnavailable ? '调度接口未就绪' : '暂无调度任务'} description={schedulerUnavailable ? '页面会如实显示 `/scheduler/tasks` 不可用，而不是伪造任务列表。' : '当前没有可展示的 scheduler task。'} />
        )}
      </SettingsSection>

      <SettingsSection title="后台 Jobs" description="最近异步任务状态。" className="md:col-span-2 xl:col-span-3">
        {jobsQuery.isLoading ? (
          <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
            {Array.from({ length: 3 }).map((_, index) => (
              <LoadingStateCard key={index} title="正在加载后台任务" description="系统正在读取最近的异步 job 状态与执行结果。" />
            ))}
          </div>
        ) : jobsQuery.error ? (
          <ErrorStateCard description={jobsQuery.error instanceof ApiError ? jobsQuery.error.message : 'Job 列表加载失败。'} />
        ) : jobsQuery.data?.length ? (
          <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
            {jobsQuery.data.slice(0, 12).map((job) => {
              const latestLog = job.logs_json?.length ? job.logs_json[job.logs_json.length - 1] : null
              return (
                <article key={job.id} className="rounded-xl border border-cloth-line/70 bg-white/45 p-4 fabric-glow">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <p className="text-sm font-semibold text-cloth-ink">#{job.id} · {job.job_type}</p>
                      <p className="mt-1 text-xs text-cloth-muted">创建：{formatTimestamp(job.created_at)}</p>
                    </div>
                    {job.status === 'completed' ? <DatabaseZap className="h-4 w-4 text-emerald-600" /> : <Clock3 className="h-4 w-4 text-cloth-accent" />}
                  </div>
                  <div className="mt-3 flex flex-wrap gap-2">
                    <SectionStatus
                      status={job.status}
                      tone={job.status === 'completed' ? 'success' : job.status === 'failed' ? 'danger' : 'warning'}
                    />
                    {job.celery_task_id ? <span className="rounded-full border border-cloth-line/80 bg-white/70 px-2.5 py-1 text-[11px] text-cloth-muted">task {job.celery_task_id}</span> : null}
                  </div>
                  {job.error_message ? <p className="mt-3 rounded-lg border border-red-200 bg-red-50/70 px-3 py-2 text-xs leading-6 text-red-700">{job.error_message}</p> : null}
                  <div className="mt-3 grid gap-2 text-xs text-cloth-muted sm:grid-cols-2">
                    <p>开始：{formatTimestamp(job.started_at)}</p>
                    <p>结束：{formatTimestamp(job.finished_at)}</p>
                    <p>更新：{formatTimestamp(job.updated_at)}</p>
                    {latestLog && typeof latestLog.message === 'string' ? <p className="sm:col-span-2">最新日志：{latestLog.message}</p> : null}
                  </div>
                  <details className="mt-3 rounded-lg border border-cloth-line/60 bg-white/55 p-3 open:fabric-card-soft">
                    <summary className="cursor-pointer text-xs font-medium text-cloth-ink">查看任务详情</summary>
                    <div className="mt-3 grid gap-3 xl:grid-cols-2">
                      <div>
                        <p className="mb-1 text-[11px] uppercase tracking-[0.14em] text-cloth-muted">payload</p>
                        <pre className="max-h-56 overflow-auto rounded-md bg-cloth-panel/70 p-2 text-[11px] leading-5 text-cloth-ink">{stringifyPayload(job.payload_json)}</pre>
                      </div>
                      <div>
                        <p className="mb-1 text-[11px] uppercase tracking-[0.14em] text-cloth-muted">result</p>
                        <pre className="max-h-56 overflow-auto rounded-md bg-cloth-panel/70 p-2 text-[11px] leading-5 text-cloth-ink">{stringifyPayload(job.result_json)}</pre>
                      </div>
                    </div>
                  </details>
                </article>
              )
            })}
          </div>
        ) : (
          <EmptyStateCard title="暂无任务记录" description="当前没有可展示的后台 job；当笔记生成、总结、思维导图等任务运行后，这里会自动显示。" />
        )}
      </SettingsSection>
    </PagePlaceholder>
  )
}

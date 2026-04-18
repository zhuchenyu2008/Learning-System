import { useMemo } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { ArrowRight, BrainCircuit, GitBranchPlus, ListChecks, Sparkles } from 'lucide-react'
import { Link } from 'react-router-dom'
import { PermissionButton } from '@/components/permission-gate'
import { StatCard } from '@/components/stat-card'
import { notesApi } from '@/lib/notes-api'
import { reviewApi } from '@/lib/review-api'
import { useAuthStore } from '@/stores/auth-store'

function formatDateTime(value: string) {
  return new Intl.DateTimeFormat('zh-CN', { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(value))
}

function formatSeconds(totalSeconds: number) {
  if (!totalSeconds) return '0 分钟'
  const minutes = Math.floor(totalSeconds / 60)
  const seconds = totalSeconds % 60
  if (!minutes) return `${seconds} 秒`
  if (!seconds) return `${minutes} 分钟`
  return `${minutes} 分 ${seconds} 秒`
}

export function ReviewOverviewPage() {
  const queryClient = useQueryClient()
  const isAdmin = useAuthStore((state) => state.user?.role === 'admin')

  const overviewQuery = useQuery({ queryKey: ['review-overview'], queryFn: () => reviewApi.getOverview() })
  const logsQuery = useQuery({ queryKey: ['review-logs', 10], queryFn: () => reviewApi.listLogs(10) })
  const summariesQuery = useQuery({ queryKey: ['summaries'], queryFn: () => reviewApi.listSummaries() })
  const mindmapsQuery = useQuery({ queryKey: ['mindmaps'], queryFn: () => reviewApi.listMindmaps() })
  const notesQuery = useQuery({ queryKey: ['notes'], queryFn: () => notesApi.listNotes(), enabled: isAdmin })

  const bootstrapMutation = useMutation({
    mutationFn: () => reviewApi.bootstrapCards({ note_ids: [], all_notes: true }),
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['review-overview'] }),
        queryClient.invalidateQueries({ queryKey: ['review-queue'] }),
        queryClient.invalidateQueries({ queryKey: ['review-logs'] }),
      ])
    },
  })

  const recentActivity = useMemo(() => logsQuery.data ?? [], [logsQuery.data])
  const latestSummary = summariesQuery.data?.[0] ?? null
  const latestMindmap = mindmapsQuery.data?.[0] ?? null

  return (
    <div className="space-y-4">
      <section className="fabric-panel space-y-5">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.24em] text-cloth-accent">Review Overview</p>
            <h1 className="font-serif text-3xl text-cloth-ink">复习总览</h1>
            <p className="mt-2 max-w-3xl text-sm text-cloth-muted">聚合今日待复习量、FSRS 卡片规模、最近复习日志，以及总结/思维导图产物入口。</p>
          </div>
          <div className="flex flex-wrap gap-3">
            <Link to="/review/session" className="fabric-btn fabric-btn-primary">
              <BrainCircuit className="h-4 w-4" />
              开始复习
            </Link>
            <PermissionButton
              allowed={isAdmin}
              reason="仅管理员可初始化复习卡"
              onClick={() => bootstrapMutation.mutate()}
            >
              <GitBranchPlus className="h-4 w-4" />
              {bootstrapMutation.isPending ? '初始化中...' : '初始化复习卡'}
            </PermissionButton>
          </div>
        </div>

        {(bootstrapMutation.isError || overviewQuery.isError) ? (
          <div className="rounded-xl border border-cloth-warn/40 bg-cloth-warn/10 p-3 text-sm text-cloth-ink">
            {String((bootstrapMutation.error as Error | null)?.message ?? (overviewQuery.error as Error | null)?.message ?? '加载失败')}
          </div>
        ) : null}
        {bootstrapMutation.data ? (
          <div className="rounded-xl border border-cloth-success/40 bg-cloth-success/10 p-3 text-sm text-cloth-ink">
            已初始化 {bootstrapMutation.data.created_cards} 张复习卡，涉及 {bootstrapMutation.data.created_knowledge_points} 个知识点。
          </div>
        ) : null}

        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          <StatCard title="今日待复习" value={String(overviewQuery.data?.due_today_count ?? 0)}>
            已到期或应于今日完成的复习卡数量
          </StatCard>
          <StatCard title="总卡片数" value={String(overviewQuery.data?.total_cards ?? 0)} tone="accent">
            当前 FSRS 卡片总数
          </StatCard>
          <StatCard title="最近复习次数" value={String(overviewQuery.data?.recent_review_count ?? 0)} tone="success">
            最近 7 天内写入的复习日志数量
          </StatCard>
          <StatCard title="最近复习时长" value={formatSeconds(overviewQuery.data?.recent_review_seconds ?? 0)} tone="warn">
            最近 7 天累计复习时长
          </StatCard>
        </div>
      </section>

      <div className="grid gap-4 xl:grid-cols-3">
        <section className="fabric-panel xl:col-span-1">
          <div className="flex items-center justify-between gap-3">
            <div>
              <p className="text-xs uppercase tracking-[0.2em] text-cloth-muted">Recent Review Logs</p>
              <h2 className="mt-1 font-serif text-2xl text-cloth-ink">最近复习情况</h2>
            </div>
            <ListChecks className="h-5 w-5 text-cloth-accent" />
          </div>
          <div className="mt-4 space-y-3">
            {recentActivity.length ? (
              recentActivity.map((log) => (
                <div key={log.id} className="fabric-card space-y-2">
                  <div className="flex items-center justify-between gap-2">
                    <p className="text-sm font-semibold text-cloth-ink">卡片 #{log.review_card_id}</p>
                    <span className="rounded-full bg-cloth-panel px-2 py-1 text-xs text-cloth-muted">评分 {log.rating}</span>
                  </div>
                  <p className="text-xs text-cloth-muted">时长：{formatSeconds(log.duration_seconds)} · {formatDateTime(log.created_at)}</p>
                  {log.note ? <p className="text-sm text-cloth-ink">{log.note}</p> : <p className="text-sm text-cloth-muted">未填写复习备注</p>}
                </div>
              ))
            ) : (
              <div className="fabric-card text-sm text-cloth-muted">暂无复习日志，进入复习会话即可开始积累。</div>
            )}
          </div>
        </section>

        <section className="fabric-panel xl:col-span-1">
          <div className="flex items-center justify-between gap-3">
            <div>
              <p className="text-xs uppercase tracking-[0.2em] text-cloth-muted">Summary Output</p>
              <h2 className="mt-1 font-serif text-2xl text-cloth-ink">知识点总结</h2>
            </div>
            <Link to="/review/summaries" className="fabric-btn">
              查看全部
              <ArrowRight className="h-4 w-4" />
            </Link>
          </div>
          <div className="mt-4 space-y-3">
            {latestSummary ? (
              <div className="fabric-card space-y-2">
                <div className="flex items-center justify-between gap-3">
                  <p className="text-sm font-semibold text-cloth-ink">产物 #{latestSummary.id}</p>
                  <span className="rounded-full bg-cloth-panel px-2 py-1 text-xs text-cloth-muted">{latestSummary.status}</span>
                </div>
                <p className="text-xs text-cloth-muted">scope: {latestSummary.scope_type} · note_ids: {latestSummary.note_ids_json.length || '全部'}</p>
                <p className="text-xs text-cloth-muted">创建于 {formatDateTime(latestSummary.created_at)}</p>
              </div>
            ) : (
              <div className="fabric-card text-sm text-cloth-muted">暂无总结产物，可从右上角入口进入生成。</div>
            )}
          </div>
        </section>

        <section className="fabric-panel xl:col-span-1">
          <div className="flex items-center justify-between gap-3">
            <div>
              <p className="text-xs uppercase tracking-[0.2em] text-cloth-muted">Mindmap Output</p>
              <h2 className="mt-1 font-serif text-2xl text-cloth-ink">思维导图</h2>
            </div>
            <Link to="/review/mindmaps" className="fabric-btn">
              查看全部
              <ArrowRight className="h-4 w-4" />
            </Link>
          </div>
          <div className="mt-4 space-y-3">
            {latestMindmap ? (
              <div className="fabric-card space-y-2">
                <div className="flex items-center justify-between gap-3">
                  <p className="text-sm font-semibold text-cloth-ink">产物 #{latestMindmap.id}</p>
                  <span className="rounded-full bg-cloth-panel px-2 py-1 text-xs text-cloth-muted">{latestMindmap.status}</span>
                </div>
                <p className="text-xs text-cloth-muted">scope: {latestMindmap.scope_type} · note_ids: {latestMindmap.note_ids_json.length || '全部'}</p>
                <p className="text-xs text-cloth-muted">创建于 {formatDateTime(latestMindmap.created_at)}</p>
              </div>
            ) : (
              <div className="fabric-card text-sm text-cloth-muted">暂无思维导图产物，可进入页面查看 Mermaid 预览。</div>
            )}
          </div>
        </section>
      </div>

      {isAdmin ? (
        <section className="fabric-panel">
          <div className="flex items-center justify-between gap-3">
            <div>
              <p className="text-xs uppercase tracking-[0.2em] text-cloth-muted">Scope Snapshot</p>
              <h2 className="mt-1 font-serif text-2xl text-cloth-ink">可用于复习初始化的笔记</h2>
            </div>
            <Sparkles className="h-5 w-5 text-cloth-accent" />
          </div>
          <div className="mt-4 grid gap-3 md:grid-cols-2 xl:grid-cols-3">
            {(notesQuery.data ?? []).slice(0, 6).map((note) => (
              <div key={note.id} className="fabric-card space-y-2">
                <p className="text-sm font-semibold text-cloth-ink">{note.title}</p>
                <p className="text-xs text-cloth-muted">{note.relative_path}</p>
                <p className="text-xs text-cloth-muted">{note.note_type}</p>
              </div>
            ))}
            {!(notesQuery.data ?? []).length ? <div className="fabric-card text-sm text-cloth-muted">暂无笔记，无法初始化复习卡。</div> : null}
          </div>
        </section>
      ) : null}
    </div>
  )
}

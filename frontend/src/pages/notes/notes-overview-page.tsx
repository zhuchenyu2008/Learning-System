import { useMemo } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { ArrowRight, FolderSync, NotebookPen, ScanSearch } from 'lucide-react'
import { Link } from 'react-router-dom'
import { PermissionButton } from '@/components/permission-gate'
import { StatCard } from '@/components/stat-card'
import { notesApi } from '@/lib/notes-api'
import { useAuthStore } from '@/stores/auth-store'

function formatDate(value: string) {
  return new Intl.DateTimeFormat('zh-CN', { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(value))
}

export function NotesOverviewPage() {
  const queryClient = useQueryClient()
  const isAdmin = useAuthStore((state) => state.user?.role === 'admin')

  const sourcesQuery = useQuery({
    queryKey: ['sources'],
    queryFn: () => notesApi.listSources(),
    enabled: isAdmin,
  })
  const notesQuery = useQuery({ queryKey: ['notes'], queryFn: () => notesApi.listNotes() })
  const jobsQuery = useQuery({ queryKey: ['jobs'], queryFn: () => notesApi.listJobs(), enabled: isAdmin })

  const scanMutation = useMutation({
    mutationFn: () => notesApi.scanSources({ root_path: '.', recursive: true, include_hidden: false }),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['sources'] })
    },
  })

  const stats = useMemo(() => {
    const recentAssets = sourcesQuery.data?.slice(0, 5) ?? []
    const recentNotes = notesQuery.data?.slice(0, 5) ?? []
    const recentJobs = jobsQuery.data?.slice(0, 5) ?? []
    const pendingJobs = recentJobs.filter((job) => job.status === 'pending' || job.status === 'running').length

    return { recentAssets, recentNotes, recentJobs, pendingJobs }
  }, [jobsQuery.data, notesQuery.data, sourcesQuery.data])

  return (
    <div className="space-y-4">
      <section className="fabric-panel space-y-5">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.24em] text-cloth-accent">Notes Overview</p>
            <h1 className="font-serif text-3xl text-cloth-ink">笔记总览</h1>
            <p className="mt-2 max-w-3xl text-sm text-cloth-muted">查看工作目录扫描状态、近期生成笔记与任务情况，并快速进入扫描和生成链路。</p>
          </div>
          <div className="flex flex-wrap gap-3">
            <PermissionButton
              allowed={isAdmin}
              reason="仅管理员可扫描来源目录"
              className="fabric-btn-primary"
              onClick={() => scanMutation.mutate()}
            >
              <ScanSearch className="h-4 w-4" />
              {scanMutation.isPending ? '扫描中...' : '扫描工作目录'}
            </PermissionButton>
            <Link to="/notes/generate" className="fabric-btn">
              <NotebookPen className="h-4 w-4" />
              去生成笔记
            </Link>
          </div>
        </div>

        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          <StatCard title="来源资产" value={isAdmin ? String(sourcesQuery.data?.length ?? 0) : '--'}>
            {isAdmin ? '已登记的扫描资产总数' : '普通用户不展示后台资产数量'}
          </StatCard>
          <StatCard title="笔记总数" value={String(notesQuery.data?.length ?? 0)} tone="accent">
            当前已入库 Markdown 笔记数
          </StatCard>
          <StatCard title="待处理任务" value={isAdmin ? String(stats.pendingJobs) : '--'} tone="warn">
            {isAdmin ? 'pending / running 任务数量' : '普通用户不展示任务状态'}
          </StatCard>
          <StatCard title="最新更新时间" value={notesQuery.data?.[0] ? formatDate(notesQuery.data[0].updated_at) : '--'} tone="success">
            最近一篇笔记的更新时间
          </StatCard>
        </div>
      </section>

      <div className="grid gap-4 xl:grid-cols-3">
        <section className="fabric-panel xl:col-span-1">
          <div className="flex items-center justify-between gap-3">
            <div>
              <p className="text-xs uppercase tracking-[0.2em] text-cloth-muted">Recent Sources</p>
              <h2 className="mt-1 font-serif text-2xl text-cloth-ink">最近扫描资产</h2>
            </div>
            <FolderSync className="h-5 w-5 text-cloth-accent" />
          </div>
          <div className="mt-4 space-y-3">
            {!isAdmin ? (
              <div className="fabric-card text-sm text-cloth-muted">普通用户可见页面，但不展示后台来源清单。</div>
            ) : stats.recentAssets.length ? (
              stats.recentAssets.map((asset) => (
                <div key={asset.id} className="fabric-card space-y-2">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <p className="text-sm font-semibold text-cloth-ink">{asset.file_path}</p>
                      <p className="text-xs uppercase tracking-[0.18em] text-cloth-muted">{asset.file_type}</p>
                    </div>
                    <span className="rounded-full bg-cloth-panel px-2 py-1 text-xs text-cloth-muted">#{asset.id}</span>
                  </div>
                  <p className="text-xs text-cloth-muted">导入时间：{formatDate(asset.imported_at)}</p>
                </div>
              ))
            ) : (
              <div className="fabric-card text-sm text-cloth-muted">暂无扫描结果，可先执行工作目录扫描。</div>
            )}
          </div>
        </section>

        <section className="fabric-panel xl:col-span-1">
          <div className="flex items-center justify-between gap-3">
            <div>
              <p className="text-xs uppercase tracking-[0.2em] text-cloth-muted">Recent Notes</p>
              <h2 className="mt-1 font-serif text-2xl text-cloth-ink">最近生成笔记</h2>
            </div>
            <Link to="/notes/library" className="fabric-btn">
              查看笔记库
              <ArrowRight className="h-4 w-4" />
            </Link>
          </div>
          <div className="mt-4 space-y-3">
            {stats.recentNotes.length ? (
              stats.recentNotes.map((note) => (
                <div key={note.id} className="fabric-card space-y-2">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <p className="text-sm font-semibold text-cloth-ink">{note.title}</p>
                      <p className="text-xs text-cloth-muted">{note.relative_path}</p>
                    </div>
                    <span className="rounded-full bg-cloth-panel px-2 py-1 text-xs text-cloth-muted">{note.note_type}</span>
                  </div>
                  <p className="text-xs text-cloth-muted">更新于 {formatDate(note.updated_at)}</p>
                </div>
              ))
            ) : (
              <div className="fabric-card text-sm text-cloth-muted">当前还没有生成后的笔记记录。</div>
            )}
          </div>
        </section>

        <section className="fabric-panel xl:col-span-1">
          <div>
            <p className="text-xs uppercase tracking-[0.2em] text-cloth-muted">Recent Jobs</p>
            <h2 className="mt-1 font-serif text-2xl text-cloth-ink">最近任务</h2>
          </div>
          <div className="mt-4 space-y-3">
            {!isAdmin ? (
              <div className="fabric-card text-sm text-cloth-muted">普通用户不展示任务列表，但保留页面一致性。</div>
            ) : stats.recentJobs.length ? (
              stats.recentJobs.map((job) => (
                <div key={job.id} className="fabric-card space-y-2">
                  <div className="flex items-center justify-between gap-3">
                    <p className="text-sm font-semibold text-cloth-ink">{job.job_type}</p>
                    <span className="rounded-full bg-cloth-panel px-2 py-1 text-xs uppercase tracking-[0.16em] text-cloth-muted">{job.status}</span>
                  </div>
                  <p className="text-xs text-cloth-muted">任务 #{job.id} · 更新于 {formatDate(job.updated_at)}</p>
                </div>
              ))
            ) : (
              <div className="fabric-card text-sm text-cloth-muted">暂无任务记录。</div>
            )}
          </div>
        </section>
      </div>
    </div>
  )
}

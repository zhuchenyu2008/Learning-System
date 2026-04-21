import { useEffect, useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Eye, FileStack, FileText, Sparkles, Trash2 } from 'lucide-react'
import { NoteDetailRenderer } from '@/components/note-detail-renderer'
import { EmptyStateCard, ErrorStateCard, LoadingStateCard } from '@/components/settings-section'
import { PermissionButton, PermissionGate } from '@/components/permission-gate'
import { notesApi } from '@/lib/notes-api'
import { reviewApi } from '@/lib/review-api'
import { getArtifactOutputNoteId, getArtifactStatusMessage, normalizeArtifactJobStatus } from '@/pages/review/artifact-job-status'
import { useAuthStore } from '@/stores/auth-store'
import type { ArtifactScopeType, NoteDetail } from '@/types/notes'

function formatDateTime(value: string) {
  return new Intl.DateTimeFormat('zh-CN', { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(value))
}

export function ReviewSummariesPage() {
  const queryClient = useQueryClient()
  const isAdmin = useAuthStore((state) => state.user?.role === 'admin')
  const [scope, setScope] = useState<ArtifactScopeType>('manual')
  const [promptExtra, setPromptExtra] = useState('')
  const [selectedNoteIds, setSelectedNoteIds] = useState<number[]>([])
  const [selectedArtifactId, setSelectedArtifactId] = useState<number | null>(null)
  const [activeJob, setActiveJob] = useState<import('@/types/notes').ArtifactGenerateResult | null>(null)

  const summariesQuery = useQuery({ queryKey: ['summaries'], queryFn: () => reviewApi.listSummaries() })
  const notesQuery = useQuery({ queryKey: ['notes', 'artifacts'], queryFn: () => notesApi.listNotes({ includeArtifacts: true }) })
  const jobQuery = useQuery({
    queryKey: ['job', 'summary-artifact', activeJob?.job_id],
    queryFn: () => reviewApi.getJob(activeJob!.job_id),
    enabled: activeJob != null,
    refetchInterval: (query) => {
      const currentJob = query.state.data
      const status = normalizeArtifactJobStatus(currentJob?.status ?? activeJob?.status)
      return status === 'completed' || status === 'failed' ? false : 1500
    },
  })

  const generateMutation = useMutation({
    mutationFn: () =>
      reviewApi.generateSummary({
        scope,
        note_ids: selectedNoteIds,
        prompt_extra: promptExtra.trim() || null,
      }),
    onSuccess: async (result) => {
      setPromptExtra('')
      setSelectedNoteIds([])
      setActiveJob(result)
      if (result.artifact_id != null) {
        setSelectedArtifactId(result.artifact_id)
      }
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['summaries'] }),
        queryClient.invalidateQueries({ queryKey: ['notes'] }),
        queryClient.invalidateQueries({ queryKey: ['jobs'] }),
      ])
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (artifactId: number) => reviewApi.deleteSummary(artifactId),
    onSuccess: async (_, deletedArtifactId) => {
      if (selectedArtifactId === deletedArtifactId) {
        setSelectedArtifactId(null)
      }
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['summaries'] }),
        queryClient.invalidateQueries({ queryKey: ['notes'] }),
      ])
    },
  })

  const summaryNotes = useMemo(
    () => (notesQuery.data ?? []).filter((note) => note.note_type === 'summary'),
    [notesQuery.data],
  )
  const selectedArtifact = useMemo(
    () => (summariesQuery.data ?? []).find((artifact) => artifact.id === selectedArtifactId) ?? summariesQuery.data?.[0] ?? null,
    [summariesQuery.data, selectedArtifactId],
  )
  const selectedOutputNoteId = selectedArtifact?.output_note_id ?? getArtifactOutputNoteId(jobQuery.data ?? null, activeJob)

  const generateStatus = useMemo(
    () => getArtifactStatusMessage('总结', jobQuery.data ?? null, activeJob),
    [activeJob, jobQuery.data],
  )

  useEffect(() => {
    if (!activeJob) return
    const status = normalizeArtifactJobStatus(jobQuery.data?.status ?? activeJob.status)
    if (status === 'completed') {
      const artifactId = (jobQuery.data?.result_json?.artifact_id as number | undefined) ?? activeJob.artifact_id
      if (artifactId != null) {
        setSelectedArtifactId(artifactId)
      }
      void Promise.all([
        queryClient.invalidateQueries({ queryKey: ['summaries'] }),
        queryClient.invalidateQueries({ queryKey: ['notes'] }),
      ])
    }
  }, [activeJob, jobQuery.data, queryClient])

  const outputNoteQuery = useQuery({
    queryKey: ['note-detail', 'summary-output', selectedOutputNoteId],
    queryFn: () => notesApi.getNoteDetail(selectedOutputNoteId as number),
    enabled: selectedOutputNoteId != null,
  })

  const toggleNote = (noteId: number) => {
    setSelectedNoteIds((current) => (current.includes(noteId) ? current.filter((id) => id !== noteId) : [...current, noteId]))
  }

  const selectedNote = outputNoteQuery.data as NoteDetail | undefined

  const handleDeleteArtifact = (artifactId: number) => {
    if (!window.confirm(`确认删除总结产物 #${artifactId}？此操作会同时删除输出笔记与文件。`)) return
    deleteMutation.mutate(artifactId)
  }

  return (
    <div className="space-y-4">
      <section className="fabric-panel space-y-5">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.24em] text-cloth-accent">Summary Generator</p>
            <h1 className="font-serif text-3xl text-cloth-ink">知识点总结</h1>
            <p className="mt-2 max-w-3xl text-sm text-cloth-muted">查看 summary 产物，并支持管理员手动生成。</p>
          </div>
          <PermissionButton
            allowed={isAdmin}
            reason="仅管理员可生成知识点总结"
            className="fabric-btn-primary"
            onClick={() => generateMutation.mutate()}
          >
            <Sparkles className="h-4 w-4" />
            {generateMutation.isPending ? '生成中...' : '生成总结'}
          </PermissionButton>
        </div>

        {(summariesQuery.isError || generateMutation.isError || outputNoteQuery.isError || deleteMutation.isError) ? (
          <ErrorStateCard
            title="总结任务状态异常"
            description={String(
              (summariesQuery.error as Error | null)?.message ??
                (generateMutation.error as Error | null)?.message ??
                (outputNoteQuery.error as Error | null)?.message ??
                (deleteMutation.error as Error | null)?.message ??
                '加载失败',
            )}
          />
        ) : null}
        {generateStatus ? (
          <div
            className={`rounded-xl border p-3 text-sm ${
              generateStatus.tone === 'success'
                ? 'border-cloth-success/40 bg-cloth-success/10 text-cloth-ink'
                : generateStatus.tone === 'error'
                  ? 'border-red-300 bg-red-50 text-red-700'
                  : 'border-cloth-accent/30 bg-cloth-panel/60 text-cloth-ink'
            }`}
          >
            {generateStatus.text}
          </div>
        ) : null}

        <div className="grid gap-4 xl:grid-cols-[minmax(0,1.15fr)_minmax(0,1.85fr)]">
          <PermissionGate allowed={isAdmin} reason="仅管理员可提交生成请求">
            <section className="fabric-card fabric-panel-stitched space-y-4">
              <div>
                <p className="text-sm font-semibold text-cloth-ink">手动生成</p>
                <p className="mt-1 text-sm text-cloth-muted">支持 manual / scheduled；不选笔记则默认全部。</p>
              </div>

              <label className="block space-y-2">
                <span className="text-sm font-semibold text-cloth-ink">生成范围</span>
                <select value={scope} onChange={(event) => setScope(event.target.value as ArtifactScopeType)} className="fabric-input" disabled={!isAdmin}>
                  <option value="manual">manual</option>
                  <option value="scheduled">scheduled</option>
                </select>
              </label>

              <label className="block space-y-2">
                <span className="text-sm font-semibold text-cloth-ink">额外提示词</span>
                <textarea
                  value={promptExtra}
                  onChange={(event) => setPromptExtra(event.target.value)}
                  className="fabric-input min-h-[120px] resize-y"
                  placeholder="例如：请突出定义、公式、常见易错点，并用分层列表输出。"
                  disabled={!isAdmin}
                />
              </label>

              <div className="rounded-xl border border-cloth-line/70 bg-white/50 p-3 text-sm text-cloth-muted">
                已选择 {selectedNoteIds.length} 篇笔记；留空则由后端按全部笔记生成。
              </div>
            </section>
          </PermissionGate>

          <section className="fabric-card space-y-4">
            <div className="flex items-center justify-between gap-3">
              <div>
                <p className="text-sm font-semibold text-cloth-ink">笔记范围选择</p>
                <p className="mt-1 text-sm text-cloth-muted">支持多选。</p>
              </div>
              <FileStack className="h-5 w-5 text-cloth-accent" />
            </div>
            <div className="max-h-[360px] space-y-3 overflow-auto pr-1 scrollbar-thin">
              {notesQuery.isLoading ? (
                <LoadingStateCard title="正在加载笔记范围" description="加载完成后可按笔记范围生成总结。" />
              ) : (notesQuery.data ?? []).length ? (
                (notesQuery.data ?? []).map((note) => {
                  const selected = selectedNoteIds.includes(note.id)
                  return (
                    <label key={note.id} className={`fabric-select-card ${selected ? 'is-selected' : ''}`} data-selected={selected ? 'true' : 'false'}>
                      <div className="flex items-start gap-3">
                        <input type="checkbox" checked={selected} onChange={() => toggleNote(note.id)} disabled={!isAdmin} className="fabric-checkbox mt-1" />
                        <div className="min-w-0 flex-1">
                          <div className="flex items-start justify-between gap-3">
                            <div className="min-w-0">
                              <p className="truncate font-semibold text-cloth-ink">{note.title}</p>
                              <p className="mt-1 truncate text-xs text-cloth-muted">{note.relative_path}</p>
                            </div>
                            <span className="rounded-full bg-cloth-panel px-2 py-1 text-xs text-cloth-muted">{note.note_type}</span>
                          </div>
                        </div>
                      </div>
                    </label>
                  )
                })
              ) : (
                <EmptyStateCard title="暂无笔记可用于总结生成" description="请先完成笔记生成，或检查当前数据源是否为空。" />
              )}
            </div>
          </section>
        </div>
      </section>

      <div className="grid gap-4 xl:grid-cols-[minmax(0,360px)_minmax(0,1fr)]">
        <section className="fabric-panel min-h-[680px] min-w-0 overflow-hidden">
          <div className="flex items-center justify-between gap-3">
            <div>
              <p className="text-xs uppercase tracking-[0.2em] text-cloth-muted">Summary Artifacts</p>
              <h2 className="mt-1 font-serif text-2xl text-cloth-ink">产物列表</h2>
            </div>
            <FileText className="h-5 w-5 text-cloth-accent" />
          </div>
          <div className="mt-4 space-y-3">
            {summariesQuery.isLoading ? (
              <LoadingStateCard title="正在加载总结产物" description="稍候将展示最近生成的总结结果。" />
            ) : (summariesQuery.data ?? []).length ? (
              (summariesQuery.data ?? []).map((artifact) => {
                const active = artifact.id === selectedArtifact?.id
                const linkedNote = summaryNotes.find((note) => note.id === artifact.output_note_id)
                const deleting = deleteMutation.isPending && deleteMutation.variables === artifact.id
                return (
                  <div
                    key={artifact.id}
                    className={`rounded-xl border p-4 ${active ? 'border-cloth-accent/55 bg-white/85 shadow-panel fabric-glow' : 'border-cloth-line/70 bg-white/45 hover:bg-white/65'}`}
                  >
                    <div className="flex items-start justify-between gap-3">
                      <button type="button" onClick={() => setSelectedArtifactId(artifact.id)} className="min-w-0 flex-1 text-left">
                        <p className="text-sm font-semibold text-cloth-ink">产物 #{artifact.id}</p>
                        <p className="mt-2 text-xs text-cloth-muted">scope: {artifact.scope_type}</p>
                        <p className="mt-1 text-xs text-cloth-muted">{artifact.note_ids_json.length ? `note_ids: ${artifact.note_ids_json.join(', ')}` : '全部笔记'}</p>
                        <p className="mt-1 text-xs text-cloth-muted">输出：{linkedNote?.title ?? `#${artifact.output_note_id ?? '--'}`}</p>
                        <p className="mt-1 text-xs text-cloth-muted">创建于 {formatDateTime(artifact.created_at)}</p>
                      </button>
                      <div className="flex items-center gap-2">
                        <span className="rounded-full bg-cloth-panel px-2 py-1 text-xs text-cloth-muted">{artifact.status}</span>
                        <button
                          type="button"
                          className="inline-flex h-9 w-9 items-center justify-center rounded-lg border border-cloth-line/70 bg-white/80 text-cloth-muted transition hover:text-cloth-danger disabled:cursor-not-allowed disabled:opacity-60"
                          onClick={() => handleDeleteArtifact(artifact.id)}
                          disabled={deleting}
                          aria-label={`删除总结产物 ${artifact.id}`}
                          title="删除总结产物"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </div>
                    </div>
                    {artifact.prompt_extra ? <p className="mt-3 rounded-xl border border-cloth-line/60 bg-white/65 p-3 text-xs leading-6 text-cloth-ink">提示词：{artifact.prompt_extra}</p> : null}
                  </div>
                )
              })
            ) : (
              <EmptyStateCard title="暂无总结产物" description="当后台总结任务产出结果后，这里会自动显示最新内容。" />
            )}
          </div>
        </section>

        <section className="fabric-panel min-w-0 min-h-[680px]">
          <div className="flex items-center justify-between gap-3">
            <div>
              <p className="text-xs uppercase tracking-[0.2em] text-cloth-muted">Summary Preview</p>
              <h2 className="mt-1 font-serif text-2xl text-cloth-ink">产物详情</h2>
            </div>
            <Eye className="h-5 w-5 text-cloth-accent" />
          </div>
          <div className="mt-4 min-w-0">
            {outputNoteQuery.isLoading ? (
              <LoadingStateCard title="正在加载总结详情" description="系统正在读取对应输出笔记内容。" />
            ) : selectedNote ? (
              <NoteDetailRenderer note={selectedNote} />
            ) : (
              <EmptyStateCard title="请选择一条知识点总结产物" description="选择左侧产物后，这里会展示对应 Markdown 详情与预览。" />
            )}
          </div>
        </section>
      </div>
    </div>
  )
}

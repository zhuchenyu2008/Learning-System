import { useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { FileStack, FileText, Sparkles } from 'lucide-react'
import { EmptyStateCard, ErrorStateCard, LoadingStateCard } from '@/components/settings-section'
import { PermissionButton, PermissionGate } from '@/components/permission-gate'
import { notesApi } from '@/lib/notes-api'
import { reviewApi } from '@/lib/review-api'
import { useAuthStore } from '@/stores/auth-store'
import type { ArtifactScopeType } from '@/types/notes'

function formatDateTime(value: string) {
  return new Intl.DateTimeFormat('zh-CN', { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(value))
}

export function ReviewSummariesPage() {
  const queryClient = useQueryClient()
  const isAdmin = useAuthStore((state) => state.user?.role === 'admin')
  const [scope, setScope] = useState<ArtifactScopeType>('manual')
  const [promptExtra, setPromptExtra] = useState('')
  const [selectedNoteIds, setSelectedNoteIds] = useState<number[]>([])

  const summariesQuery = useQuery({ queryKey: ['summaries'], queryFn: () => reviewApi.listSummaries() })
  const notesQuery = useQuery({ queryKey: ['notes'], queryFn: () => notesApi.listNotes() })

  const generateMutation = useMutation({
    mutationFn: () =>
      reviewApi.generateSummary({
        scope,
        note_ids: selectedNoteIds,
        prompt_extra: promptExtra.trim() || null,
      }),
    onSuccess: async () => {
      setPromptExtra('')
      setSelectedNoteIds([])
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

  const toggleNote = (noteId: number) => {
    setSelectedNoteIds((current) => (current.includes(noteId) ? current.filter((id) => id !== noteId) : [...current, noteId]))
  }

  return (
    <div className="space-y-4">
      <section className="fabric-panel space-y-5">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.24em] text-cloth-accent">Summary Generator</p>
            <h1 className="font-serif text-3xl text-cloth-ink">知识点总结</h1>
            <p className="mt-2 max-w-3xl text-sm text-cloth-muted">展示已有 summary 产物，并支持管理员按全部笔记或指定笔记范围手动触发新总结。</p>
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

        {(summariesQuery.isError || generateMutation.isError) ? (
          <ErrorStateCard
            title="总结任务状态异常"
            description={String((summariesQuery.error as Error | null)?.message ?? (generateMutation.error as Error | null)?.message ?? '加载失败')}
          />
        ) : null}
        {generateMutation.data ? (
          <div className="rounded-xl border border-cloth-success/40 bg-cloth-success/10 p-3 text-sm text-cloth-ink">
            已创建总结任务 #{generateMutation.data.job_id}，输出笔记 #{generateMutation.data.output_note_id}（{generateMutation.data.relative_path}）。
          </div>
        ) : null}

        <div className="grid gap-4 xl:grid-cols-[1.15fr_1.85fr]">
          <PermissionGate allowed={isAdmin} reason="仅管理员可提交生成请求">
            <section className="fabric-card space-y-4">
              <div>
                <p className="text-sm font-semibold text-cloth-ink">手动生成</p>
                <p className="mt-1 text-sm text-cloth-muted">scope 固定支持 manual / scheduled，note_ids 留空则表示全部笔记。</p>
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
                <p className="mt-1 text-sm text-cloth-muted">可选任意笔记作为总结输入范围，支持多选。</p>
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
                    <label key={note.id} className={`block rounded-xl border p-4 text-sm ${selected ? 'border-cloth-accent/60 bg-white/80' : 'border-cloth-line/70 bg-white/45'}`}>
                      <div className="flex items-start gap-3">
                        <input type="checkbox" checked={selected} onChange={() => toggleNote(note.id)} disabled={!isAdmin} className="mt-1" />
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

      <section className="fabric-panel">
        <div className="flex items-center justify-between gap-3">
          <div>
            <p className="text-xs uppercase tracking-[0.2em] text-cloth-muted">Summary Artifacts</p>
            <h2 className="mt-1 font-serif text-2xl text-cloth-ink">已有总结产物</h2>
          </div>
          <FileText className="h-5 w-5 text-cloth-accent" />
        </div>
        <div className="mt-4 grid gap-3 md:grid-cols-2 xl:grid-cols-3">
          {summariesQuery.isLoading ? (
            Array.from({ length: 3 }).map((_, index) => (
              <LoadingStateCard key={index} title="正在加载总结产物" description="稍候将展示最近生成的总结结果。" />
            ))
          ) : (summariesQuery.data ?? []).length ? (
            (summariesQuery.data ?? []).map((artifact) => {
              const linkedNote = summaryNotes.find((note) => note.id === artifact.output_note_id)
              return (
                <article key={artifact.id} className="fabric-card fabric-glow space-y-3">
                  <div className="flex items-center justify-between gap-3">
                    <p className="text-sm font-semibold text-cloth-ink">产物 #{artifact.id}</p>
                    <span className="rounded-full bg-cloth-panel px-2 py-1 text-xs text-cloth-muted">{artifact.status}</span>
                  </div>
                  <div className="space-y-1 text-sm text-cloth-muted">
                    <p>scope: {artifact.scope_type}</p>
                    <p>note_ids: {artifact.note_ids_json.length ? artifact.note_ids_json.join(', ') : '全部笔记'}</p>
                    <p>创建于：{formatDateTime(artifact.created_at)}</p>
                  </div>
                  {artifact.prompt_extra ? <p className="rounded-xl border border-cloth-line/60 bg-white/50 p-3 text-sm leading-6 text-cloth-ink">提示词：{artifact.prompt_extra}</p> : null}
                  {linkedNote ? (
                    <div className="rounded-xl border border-cloth-line/70 bg-white/55 p-3 text-sm text-cloth-ink">
                      <p className="font-semibold">输出笔记</p>
                      <p className="mt-1 line-clamp-2 leading-6">{linkedNote.title}</p>
                      <p className="mt-1 break-all text-xs text-cloth-muted">{linkedNote.relative_path}</p>
                    </div>
                  ) : (
                    <div className="rounded-xl border border-cloth-line/70 bg-white/55 p-3 text-sm text-cloth-muted">输出笔记 #{artifact.output_note_id ?? '--'} 尚未在前端笔记列表中命中。</div>
                  )}
                </article>
              )
            })
          ) : (
            <EmptyStateCard title="暂无总结产物" description="当后台总结任务产出结果后，这里会自动显示最新内容。" />
          )}
        </div>
      </section>
    </div>
  )
}

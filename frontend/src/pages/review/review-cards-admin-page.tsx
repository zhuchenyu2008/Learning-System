import { useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Plus, RefreshCcw, Trash2 } from 'lucide-react'
import { reviewApi } from '@/lib/review-api'
import { notesApi } from '@/lib/notes-api'

function formatDateTime(value: string) {
  return new Intl.DateTimeFormat('zh-CN', { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(value))
}

function splitTags(value: string) {
  return value
    .split(/[，,]/)
    .map((item) => item.trim())
    .filter(Boolean)
}

export function ReviewCardsAdminPage() {
  const queryClient = useQueryClient()
  const [subject, setSubject] = useState('')
  const [query, setQuery] = useState('')
  const [noteId, setNoteId] = useState('')
  const [form, setForm] = useState({
    noteId: '',
    title: '',
    contentMd: '',
    summaryText: '',
    sourceAnchor: '',
    tagsText: '',
    subject: '',
    suspended: false,
  })

  const notesQuery = useQuery({ queryKey: ['notes'], queryFn: () => notesApi.listNotes() })
  const subjectsQuery = useQuery({ queryKey: ['review-subjects'], queryFn: () => reviewApi.listSubjects() })
  const cardsQuery = useQuery({
    queryKey: ['review-admin-cards', subject, query, noteId],
    queryFn: () =>
      reviewApi.listAdminCards({
        subject: subject || null,
        query: query || undefined,
        noteId: noteId ? Number(noteId) : undefined,
        limit: 100,
      }),
  })

  const createMutation = useMutation({
    mutationFn: () =>
      reviewApi.createAdminCard({
        note_id: Number(form.noteId),
        title: form.title.trim(),
        content_md: form.contentMd.trim(),
        summary_text: form.summaryText.trim() || null,
        source_anchor: form.sourceAnchor.trim() || null,
        tags: splitTags(form.tagsText),
        subject: form.subject.trim() || null,
        suspended: form.suspended,
      }),
    onSuccess: async () => {
      setForm({ noteId: '', title: '', contentMd: '', summaryText: '', sourceAnchor: '', tagsText: '', subject: '', suspended: false })
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['review-admin-cards'] }),
        queryClient.invalidateQueries({ queryKey: ['review-subjects'] }),
        queryClient.invalidateQueries({ queryKey: ['review-queue'] }),
      ])
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (cardId: number) => reviewApi.deleteAdminCard(cardId),
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['review-admin-cards'] }),
        queryClient.invalidateQueries({ queryKey: ['review-subjects'] }),
        queryClient.invalidateQueries({ queryKey: ['review-queue'] }),
      ])
    },
  })

  const noteOptions = useMemo(() => notesQuery.data ?? [], [notesQuery.data])

  return (
    <div className="space-y-4">
      <section className="fabric-panel space-y-5">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.24em] text-cloth-accent">Review Card Admin</p>
            <h1 className="font-serif text-3xl text-cloth-ink">复习卡片管理</h1>
            <p className="mt-2 max-w-3xl text-sm text-cloth-muted">管理员可按学科/笔记筛选、手动新增卡片，并删除不需要的复习卡。</p>
          </div>
          <button type="button" className="fabric-btn" onClick={() => cardsQuery.refetch()}>
            <RefreshCcw className="h-4 w-4" />
            刷新列表
          </button>
        </div>

        {(cardsQuery.isError || createMutation.isError || deleteMutation.isError) ? (
          <div className="rounded-xl border border-cloth-warn/40 bg-cloth-warn/10 p-3 text-sm text-cloth-ink">
            {String((cardsQuery.error as Error | null)?.message ?? (createMutation.error as Error | null)?.message ?? (deleteMutation.error as Error | null)?.message ?? '操作失败')}
          </div>
        ) : null}

        <div className="grid gap-4 xl:grid-cols-[420px_minmax(0,1fr)]">
          <section className="fabric-card space-y-4">
            <div>
              <p className="text-sm font-semibold text-cloth-ink">手动新增卡片</p>
              <p className="mt-1 text-sm text-cloth-muted">最小闭环：选择笔记、填写题面与答案要点。</p>
            </div>

            <label className="block space-y-2">
              <span className="text-sm font-semibold text-cloth-ink">来源笔记</span>
              <select className="fabric-input" value={form.noteId} onChange={(event) => setForm((current) => ({ ...current, noteId: event.target.value }))}>
                <option value="">请选择笔记</option>
                {noteOptions.map((note) => (
                  <option key={note.id} value={note.id}>{note.title}</option>
                ))}
              </select>
            </label>

            <label className="block space-y-2">
              <span className="text-sm font-semibold text-cloth-ink">标题</span>
              <input className="fabric-input" value={form.title} onChange={(event) => setForm((current) => ({ ...current, title: event.target.value }))} />
            </label>

            <label className="block space-y-2">
              <span className="text-sm font-semibold text-cloth-ink">内容</span>
              <textarea className="fabric-input min-h-[140px] resize-y" value={form.contentMd} onChange={(event) => setForm((current) => ({ ...current, contentMd: event.target.value }))} />
            </label>

            <label className="block space-y-2">
              <span className="text-sm font-semibold text-cloth-ink">总结答案</span>
              <textarea className="fabric-input min-h-[96px] resize-y" value={form.summaryText} onChange={(event) => setForm((current) => ({ ...current, summaryText: event.target.value }))} />
            </label>

            <div className="grid gap-3 md:grid-cols-2">
              <label className="block space-y-2">
                <span className="text-sm font-semibold text-cloth-ink">学科</span>
                <input className="fabric-input" value={form.subject} onChange={(event) => setForm((current) => ({ ...current, subject: event.target.value }))} placeholder="例如：数学" />
              </label>
              <label className="block space-y-2">
                <span className="text-sm font-semibold text-cloth-ink">标签</span>
                <input className="fabric-input" value={form.tagsText} onChange={(event) => setForm((current) => ({ ...current, tagsText: event.target.value }))} placeholder="逗号分隔" />
              </label>
            </div>

            <label className="block space-y-2">
              <span className="text-sm font-semibold text-cloth-ink">锚点</span>
              <input className="fabric-input" value={form.sourceAnchor} onChange={(event) => setForm((current) => ({ ...current, sourceAnchor: event.target.value }))} />
            </label>

            <label className="flex items-center gap-3 text-sm text-cloth-ink">
              <input type="checkbox" checked={form.suspended} onChange={(event) => setForm((current) => ({ ...current, suspended: event.target.checked }))} className="fabric-checkbox" />
              新建后直接暂停
            </label>

            <button
              type="button"
              className="fabric-btn fabric-btn-primary"
              disabled={!form.noteId || !form.title.trim() || !form.contentMd.trim() || createMutation.isPending}
              onClick={() => createMutation.mutate()}
            >
              <Plus className="h-4 w-4" />
              {createMutation.isPending ? '创建中...' : '新增复习卡'}
            </button>
          </section>

          <section className="fabric-card space-y-4 min-w-0">
            <div className="grid gap-3 md:grid-cols-3">
              <label className="block space-y-2">
                <span className="text-sm font-semibold text-cloth-ink">学科筛选</span>
                <select className="fabric-input" value={subject} onChange={(event) => setSubject(event.target.value)}>
                  <option value="">全部学科</option>
                  {(subjectsQuery.data ?? []).map((item) => (
                    <option key={item.subject} value={item.subject}>{item.subject}（到期 {item.due_cards}）</option>
                  ))}
                </select>
              </label>
              <label className="block space-y-2">
                <span className="text-sm font-semibold text-cloth-ink">按笔记筛选</span>
                <select className="fabric-input" value={noteId} onChange={(event) => setNoteId(event.target.value)}>
                  <option value="">全部笔记</option>
                  {noteOptions.map((note) => (
                    <option key={note.id} value={note.id}>{note.title}</option>
                  ))}
                </select>
              </label>
              <label className="block space-y-2">
                <span className="text-sm font-semibold text-cloth-ink">关键词</span>
                <input className="fabric-input" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="标题 / 内容" />
              </label>
            </div>

            <div className="space-y-3 max-h-[720px] overflow-auto pr-1">
              {(cardsQuery.data ?? []).length ? (
                (cardsQuery.data ?? []).map((card) => (
                  <div key={card.card_id} className="rounded-2xl border border-cloth-line/70 bg-white/55 p-4 space-y-3">
                    <div className="flex items-start justify-between gap-3">
                      <div className="min-w-0">
                        <p className="text-sm font-semibold text-cloth-ink">#{card.card_id} · {card.knowledge_point.title}</p>
                        <p className="mt-1 text-xs text-cloth-muted">{card.subject ?? '未分类'} · {card.note.title}</p>
                      </div>
                      <button type="button" className="fabric-btn" onClick={() => deleteMutation.mutate(card.card_id)} disabled={deleteMutation.isPending}>
                        <Trash2 className="h-4 w-4" /> 删除
                      </button>
                    </div>
                    <p className="text-sm whitespace-pre-wrap text-cloth-ink">{card.knowledge_point.content_md}</p>
                    {card.knowledge_point.summary_text ? <p className="text-xs text-cloth-muted">答案：{card.knowledge_point.summary_text}</p> : null}
                    <div className="flex flex-wrap gap-2 text-xs text-cloth-muted">
                      <span>到期：{formatDateTime(card.due_at)}</span>
                      <span>路径：{card.note.relative_path}</span>
                      {card.suspended ? <span>已暂停</span> : <span>启用中</span>}
                    </div>
                  </div>
                ))
              ) : (
                <div className="fabric-card text-sm text-cloth-muted">暂无复习卡，调整筛选条件或先手动新增。</div>
              )}
            </div>
          </section>
        </div>
      </section>
    </div>
  )
}

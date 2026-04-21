import { useEffect, useMemo, useRef, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { CheckCircle2, Clock3, RefreshCcw, Sparkles, TimerReset } from 'lucide-react'
import { useSearchParams } from 'react-router-dom'
import { MarkdownContent } from '@/components/note-detail-renderer'
import { PermissionButton } from '@/components/permission-gate'
import { reviewApi } from '@/lib/review-api'
import { useAuthStore } from '@/stores/auth-store'
import type { ReviewJudgeResult, ReviewQueueItem } from '@/types/notes'

const RATING_OPTIONS = [
  { label: 'Again', value: 1 as const, description: '完全没想起，需要尽快重学', className: 'border-cloth-warn/60' },
  { label: 'Hard', value: 2 as const, description: '勉强回忆，仍需加密复习', className: '' },
  { label: 'Good', value: 3 as const, description: '正常回忆，推荐默认评分', className: 'fabric-btn-primary' },
  { label: 'Easy', value: 4 as const, description: '掌握稳定，可适当拉长间隔', className: 'border-cloth-success/60' },
]

function formatDateTime(value: string) {
  return new Intl.DateTimeFormat('zh-CN', { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(value))
}

function formatSeconds(totalSeconds: number) {
  if (!totalSeconds) return '0 秒'
  const minutes = Math.floor(totalSeconds / 60)
  const seconds = totalSeconds % 60
  if (!minutes) return `${seconds} 秒`
  if (!seconds) return `${minutes} 分钟`
  return `${minutes} 分 ${seconds} 秒`
}

function extractTags(item: ReviewQueueItem) {
  const rawTags = item.knowledge_point.tags_json
  const tags = rawTags.tags
  return Array.isArray(tags) ? tags.filter((tag): tag is string => typeof tag === 'string') : []
}

export function ReviewSessionPage() {
  const queryClient = useQueryClient()
  const currentUser = useAuthStore((state) => state.user)
  const [searchParams, setSearchParams] = useSearchParams()
  const selectedSubject = searchParams.get('subject') ?? ''
  const selectedLimit = Math.max(1, Math.min(Number(searchParams.get('limit') ?? '20') || 20, 200))
  const queueQuery = useQuery({
    queryKey: ['review-queue', selectedSubject, selectedLimit],
    queryFn: () => reviewApi.getQueue({ limit: selectedLimit, dueOnly: true, subject: selectedSubject || null }),
  })
  const logsQuery = useQuery({ queryKey: ['review-logs', 8], queryFn: () => reviewApi.listLogs(8) })
  const subjectsQuery = useQuery({ queryKey: ['review-subjects'], queryFn: () => reviewApi.listSubjects() })

  const [currentIndex, setCurrentIndex] = useState(0)
  const [answer, setAnswer] = useState('')
  const [sessionNote, setSessionNote] = useState('')
  const [manualDuration, setManualDuration] = useState('')
  const [judgeResult, setJudgeResult] = useState<ReviewJudgeResult | null>(null)
  const [selectedRating, setSelectedRating] = useState<1 | 2 | 3 | 4 | null>(null)
  const startedAtRef = useRef<number | null>(null)
  const finalizedCardIdRef = useRef<number | null>(null)
  const latestManualDurationRef = useRef('')
  const latestServerDurationRef = useRef(0)
  const [serverDurationSeconds, setServerDurationSeconds] = useState(0)
  const [, setTick] = useState(0)

  const queue = queueQuery.data ?? []
  const currentCard = queue[currentIndex] ?? null

  useEffect(() => {
    startedAtRef.current = currentCard ? Date.now() : null
    setAnswer('')
    setSessionNote('')
    setManualDuration('')
    setJudgeResult(null)
    setSelectedRating(null)
    setServerDurationSeconds(0)
  }, [currentCard])

  useEffect(() => {
    if (currentIndex > Math.max(queue.length - 1, 0)) {
      setCurrentIndex(0)
    }
  }, [currentIndex, queue.length])

  useEffect(() => {
    latestManualDurationRef.current = manualDuration
  }, [manualDuration])

  useEffect(() => {
    latestServerDurationRef.current = serverDurationSeconds
  }, [serverDurationSeconds])

  useEffect(() => {
    if (!currentCard || manualDuration.trim()) return
    const intervalId = window.setInterval(() => {
      setTick((value) => value + 1)
    }, 1000)
    return () => window.clearInterval(intervalId)
  }, [currentCard?.card_id, manualDuration])

  const derivedDuration = useMemo(() => {
    if (!currentCard) return 0
    if (manualDuration.trim()) {
      const parsed = Number(manualDuration)
      return Number.isFinite(parsed) && parsed >= 0 ? Math.floor(parsed) : 0
    }
    if (!startedAtRef.current) return serverDurationSeconds
    const localSeconds = Math.max(0, Math.floor((Date.now() - startedAtRef.current) / 1000))
    return Math.max(localSeconds, serverDurationSeconds)
  }, [currentCard, manualDuration, serverDurationSeconds])

  useEffect(() => {
    if (!currentCard) return
    finalizedCardIdRef.current = null
    let cancelled = false
    let intervalId: number | null = null

    const startSession = async () => {
      try {
        const state = await reviewApi.startSession(currentCard.card_id)
        if (!cancelled) {
          setServerDurationSeconds(state.accumulated_seconds ?? 0)
        }
      } catch {
        // keep local timer fallback
      }

      intervalId = window.setInterval(async () => {
        try {
          const state = await reviewApi.heartbeatSession(currentCard.card_id)
          if (!cancelled) {
            setServerDurationSeconds(state.accumulated_seconds ?? 0)
          }
        } catch {
          // keep local timer fallback
        }
      }, 15000)
    }

    void startSession()

    return () => {
      cancelled = true
      if (intervalId != null) window.clearInterval(intervalId)
      if (finalizedCardIdRef.current === currentCard.card_id) return
      const fallbackDuration = latestManualDurationRef.current.trim()
        ? Math.max(0, Math.floor(Number(latestManualDurationRef.current) || 0))
        : Math.max(latestServerDurationRef.current, startedAtRef.current ? Math.max(0, Math.floor((Date.now() - startedAtRef.current) / 1000)) : 0)
      void reviewApi.finalizeSession(currentCard.card_id, { duration_seconds: fallbackDuration }).catch(() => undefined)
    }
  }, [currentCard?.card_id])

  const judgeMutation = useMutation({
    mutationFn: ({ cardId, answerText, durationSeconds, note }: { cardId: number; answerText: string; durationSeconds: number; note: string }) =>
      reviewApi.judgeAnswer(cardId, {
        answer: answerText.trim(),
        duration_seconds: durationSeconds,
        note: note.trim() || null,
      }),
    onSuccess: (result) => {
      setJudgeResult(result)
      setSelectedRating(result.suggested_rating)
    },
  })

  const gradeMutation = useMutation({
    mutationFn: ({ cardId, rating, durationSeconds, note, answerText, judge }: { cardId: number; rating: 1 | 2 | 3 | 4; durationSeconds: number; note: string; answerText: string; judge: ReviewJudgeResult | null }) =>
      reviewApi.gradeCard(cardId, {
        rating,
        duration_seconds: durationSeconds,
        note: note.trim() || null,
        answer: answerText.trim() || null,
        ai_judge: (judge as unknown as Record<string, unknown> | null) ?? null,
      }),
    onSuccess: async (_, variables) => {
      setAnswer('')
      setSessionNote('')
      setManualDuration('')
      setJudgeResult(null)
      setSelectedRating(null)
      startedAtRef.current = null
      setServerDurationSeconds(0)
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['review-queue'] }),
        queryClient.invalidateQueries({ queryKey: ['review-overview'] }),
        queryClient.invalidateQueries({ queryKey: ['review-logs'] }),
      ])

      setCurrentIndex((index) => {
        const nextLength = Math.max(queue.length - 1, 0)
        if (!nextLength) return 0
        const currentPosition = queue.findIndex((item) => item.card_id === variables.cardId)
        if (currentPosition === -1) return Math.min(index, nextLength - 1)
        return Math.min(currentPosition, nextLength - 1)
      })
    },
  })

  const handleJudge = () => {
    if (!currentCard || !answer.trim()) return
    judgeMutation.mutate({
      cardId: currentCard.card_id,
      answerText: answer,
      durationSeconds: derivedDuration,
      note: sessionNote,
    })
  }

  const handleGrade = async (ratingOverride?: 1 | 2 | 3 | 4) => {
    if (!currentCard) return
    const finalRating = ratingOverride ?? selectedRating
    if (!finalRating) return
    let finalDuration = derivedDuration
    try {
      const finalized = await reviewApi.finalizeSession(currentCard.card_id, { duration_seconds: derivedDuration })
      finalizedCardIdRef.current = currentCard.card_id
      finalDuration = finalized.duration_seconds
      setServerDurationSeconds(finalized.server_accumulated_seconds)
    } catch {
      // fallback to local/manual duration
    }
    gradeMutation.mutate({
      cardId: currentCard.card_id,
      rating: finalRating,
      durationSeconds: finalDuration,
      note: sessionNote,
      answerText: answer,
      judge: judgeResult,
    })
  }

  return (
    <div className="space-y-4">
      <section className="fabric-panel space-y-5">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.24em] text-cloth-accent">Review Session</p>
            <h1 className="font-serif text-3xl text-cloth-ink">复习会话</h1>
            <p className="mt-2 max-w-3xl text-sm text-cloth-muted">按队列逐条复习知识点，支持 Again / Hard / Good / Easy 评分，并将时长与备注写入复习日志。</p>
          </div>
          <div className="flex flex-wrap gap-3">
            <PermissionButton allowed className="fabric-btn" onClick={() => queueQuery.refetch()}>
              <RefreshCcw className="h-4 w-4" />
              刷新队列
            </PermissionButton>
          </div>
        </div>

        {(queueQuery.isError || judgeMutation.isError || gradeMutation.isError) ? (
          <div className="rounded-xl border border-cloth-warn/40 bg-cloth-warn/10 p-3 text-sm text-cloth-ink">
            {String((queueQuery.error as Error | null)?.message ?? (judgeMutation.error as Error | null)?.message ?? (gradeMutation.error as Error | null)?.message ?? '操作失败')}
          </div>
        ) : null}

        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-[minmax(0,1.1fr)_repeat(4,minmax(0,1fr))]">
          <div className="fabric-card space-y-3">
            <p className="text-xs uppercase tracking-[0.2em] text-cloth-muted">Scope</p>
            <div className="grid gap-3">
              <label className="block space-y-2">
                <span className="text-sm text-cloth-ink">学科</span>
                <select
                  className="fabric-input"
                  value={selectedSubject}
                  onChange={(event) => {
                    const next = new URLSearchParams(searchParams)
                    if (event.target.value) next.set('subject', event.target.value)
                    else next.delete('subject')
                    setSearchParams(next)
                  }}
                >
                  <option value="">全部学科</option>
                  {(subjectsQuery.data ?? []).map((item) => (
                    <option key={item.subject} value={item.subject}>{item.subject}（到期 {item.due_cards}）</option>
                  ))}
                </select>
              </label>
              <label className="block space-y-2">
                <span className="text-sm text-cloth-ink">本轮数量</span>
                <input
                  inputMode="numeric"
                  className="fabric-input"
                  value={String(selectedLimit)}
                  onChange={(event) => {
                    const next = new URLSearchParams(searchParams)
                    const parsed = Math.max(1, Math.min(Number(event.target.value.replace(/[^\d]/g, '')) || 20, 200))
                    next.set('limit', String(parsed))
                    setSearchParams(next)
                  }}
                />
              </label>
            </div>
          </div>
          <div className="fabric-card">
            <p className="text-xs uppercase tracking-[0.2em] text-cloth-muted">Queue</p>
            <p className="mt-3 text-3xl font-semibold text-cloth-ink">{queue.length}</p>
            <p className="mt-2 text-sm text-cloth-muted">当前待处理的到期复习卡</p>
          </div>
          <div className="fabric-card">
            <p className="text-xs uppercase tracking-[0.2em] text-cloth-muted">Position</p>
            <p className="mt-3 text-3xl font-semibold text-cloth-ink">{currentCard ? `${currentIndex + 1} / ${queue.length}` : '--'}</p>
            <p className="mt-2 text-sm text-cloth-muted">当前会话进度</p>
          </div>
          <div className="fabric-card">
            <p className="text-xs uppercase tracking-[0.2em] text-cloth-muted">Duration</p>
            <p className="mt-3 text-3xl font-semibold text-cloth-ink">{formatSeconds(derivedDuration)}</p>
            <p className="mt-2 text-sm text-cloth-muted">默认显示前端停留时长与服务端累计时长的较大值</p>
          </div>
          <div className="fabric-card">
            <p className="text-xs uppercase tracking-[0.2em] text-cloth-muted">Actor</p>
            <p className="mt-3 text-3xl font-semibold text-cloth-ink">{currentUser?.role === 'admin' ? '管理员' : '普通用户'}</p>
            <p className="mt-2 text-sm text-cloth-muted">viewer / admin 均可提交评分与日志</p>
          </div>
        </div>
      </section>

      {!currentCard ? (
        <section className="fabric-panel">
          <div className="fabric-card space-y-3 text-center">
            <h2 className="font-serif text-2xl text-cloth-ink">当前没有待复习卡片</h2>
            <p className="text-sm text-cloth-muted">如果这是首次使用，请让管理员在复习总览中先初始化复习卡，或稍后刷新队列。</p>
          </div>
        </section>
      ) : (
        <div className="grid gap-4 xl:grid-cols-[minmax(0,1.6fr)_minmax(0,420px)]">
          <section className="fabric-panel min-w-0 overflow-hidden">
            <div className="space-y-4">
              <div className="flex flex-wrap items-center gap-2">
                <span className="rounded-full bg-cloth-panel px-3 py-1 text-xs uppercase tracking-[0.18em] text-cloth-muted">Card #{currentCard.card_id}</span>
                <span className="rounded-full bg-cloth-panel px-3 py-1 text-xs text-cloth-muted">来源笔记 #{currentCard.note.id}</span>
                {currentCard.suspended ? <span className="rounded-full bg-cloth-warn/15 px-3 py-1 text-xs text-cloth-ink">已暂停</span> : null}
              </div>

              <div className="rounded-2xl border border-cloth-line/80 bg-white/60 p-5 shadow-panel">
                <p className="text-xs uppercase tracking-[0.2em] text-cloth-muted">Knowledge Point</p>
                <h2 className="mt-2 break-words font-serif text-3xl text-cloth-ink">{currentCard.knowledge_point.title}</h2>
                <div className="mt-3 min-w-0">
                  <MarkdownContent content={currentCard.knowledge_point.content_md} className="border-0 bg-transparent p-0 shadow-none lg:p-0" />
                </div>
              </div>

              <div className="rounded-2xl border border-cloth-line/80 bg-white/55 p-5 shadow-panel">
                <div className="grid gap-4 md:grid-cols-2">
                  <div>
                    <p className="text-xs uppercase tracking-[0.2em] text-cloth-muted">Source Note</p>
                    <p className="mt-2 text-lg font-semibold text-cloth-ink">{currentCard.note.title}</p>
                    <p className="mt-1 text-sm text-cloth-muted">{currentCard.note.relative_path}</p>
                  </div>
                  <div>
                    <p className="text-xs uppercase tracking-[0.2em] text-cloth-muted">Due At</p>
                    <p className="mt-2 text-lg font-semibold text-cloth-ink">{formatDateTime(currentCard.due_at)}</p>
                    <div className="mt-2 flex flex-wrap gap-2">
                      {extractTags(currentCard).length ? (
                        extractTags(currentCard).map((tag) => (
                          <span key={tag} className="rounded-full bg-cloth-panel px-2 py-1 text-xs text-cloth-muted">#{tag}</span>
                        ))
                      ) : (
                        <span className="text-sm text-cloth-muted">暂无标签</span>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </section>

          <section className="fabric-panel min-w-0 space-y-4 overflow-hidden">
            <div>
              <p className="text-xs uppercase tracking-[0.2em] text-cloth-muted">Session Log</p>
              <h2 className="mt-1 font-serif text-2xl text-cloth-ink">作答、判分与确认</h2>
            </div>

            <div className="fabric-card space-y-4">
              <label className="block space-y-2">
                <span className="text-sm font-semibold text-cloth-ink">你的回答</span>
                <textarea
                  value={answer}
                  onChange={(event) => {
                    setAnswer(event.target.value)
                    if (judgeResult) {
                      setJudgeResult(null)
                      setSelectedRating(null)
                    }
                  }}
                  className="fabric-input min-h-[120px] resize-y"
                  placeholder="先按最小记忆单元用自己的话作答，再让 AI 给评分建议与讲解..."
                />
              </label>

              <label className="block space-y-2">
                <span className="text-sm font-semibold text-cloth-ink">复习备注</span>
                <textarea
                  value={sessionNote}
                  onChange={(event) => setSessionNote(event.target.value)}
                  className="fabric-input min-h-[96px] resize-y"
                  placeholder="可选填写：本次卡住点、联想到的例子、下次复习提醒..."
                />
              </label>

              <label className="block space-y-2">
                <span className="text-sm font-semibold text-cloth-ink">时长（秒，可选覆盖自动计时）</span>
                <input
                  inputMode="numeric"
                  value={manualDuration}
                  onChange={(event) => setManualDuration(event.target.value.replace(/[^\d]/g, ''))}
                  className="fabric-input"
                  placeholder="留空则自动按本卡停留时长估算"
                />
              </label>

              <div className="rounded-xl border border-cloth-line/70 bg-white/50 p-3 text-sm text-cloth-muted">
                <div className="flex items-center gap-2 text-cloth-ink">
                  <Clock3 className="h-4 w-4" /> 当前将提交时长：{formatSeconds(derivedDuration)}
                </div>
                <div className="mt-2 flex items-center gap-2">
                  <TimerReset className="h-4 w-4" /> 切换到下一卡后会自动重置计时与表单。
                </div>
                <div className="mt-2 text-xs text-cloth-muted">显示口径：前端展示为“当前卡本地停留时长”和“服务端心跳累计时长”中的较大值；后台累计口径以服务端 finalize 后写入日志的秒数为准。</div>
              </div>

              <div className="flex flex-wrap gap-3">
                <button
                  type="button"
                  onClick={handleJudge}
                  disabled={judgeMutation.isPending || gradeMutation.isPending || currentCard.suspended || !answer.trim()}
                  className="fabric-btn fabric-btn-primary"
                >
                  <Sparkles className="h-4 w-4" />
                  {judgeMutation.isPending ? 'AI 判分中...' : '获取 AI 评分建议'}
                </button>
              </div>
            </div>

            {judgeResult ? (
              <div className="fabric-card space-y-4 border-cloth-accent/40">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <p className="text-xs uppercase tracking-[0.2em] text-cloth-muted">AI Judge</p>
                    <h3 className="mt-1 text-lg font-semibold text-cloth-ink">评分建议与讲解</h3>
                  </div>
                  <span className="rounded-full bg-cloth-panel px-3 py-1 text-xs text-cloth-muted">
                    {judgeResult.judge_status === 'ai' ? 'AI 判分' : '回退判分'}
                  </span>
                </div>

                <div className="space-y-2 text-sm text-cloth-ink">
                  <p><span className="font-semibold">参考答案：</span>{judgeResult.expected_answer}</p>
                  <p><span className="font-semibold">正确性判断：</span>{judgeResult.correctness}</p>
                  <p><span className="font-semibold">讲解：</span>{judgeResult.explanation}</p>
                  {judgeResult.judge_error ? <p className="text-xs text-cloth-muted">回退原因：{judgeResult.judge_error}</p> : null}
                </div>

                <div className="grid gap-3 md:grid-cols-2">
                  {RATING_OPTIONS.map((option) => (
                    <button
                      key={option.value}
                      type="button"
                      onClick={() => setSelectedRating(option.value)}
                      disabled={gradeMutation.isPending || currentCard.suspended}
                      className={`fabric-btn min-h-[88px] flex-col items-start justify-start ${option.className} ${selectedRating === option.value ? 'ring-2 ring-cloth-accent' : ''}`}
                      title={option.description}
                    >
                      <span className="text-base font-semibold">{option.label}{judgeResult.suggested_rating === option.value ? ' · AI 推荐' : ''}</span>
                      <span className="text-left text-xs text-cloth-muted">{option.description}</span>
                    </button>
                  ))}
                </div>

                <div className="flex flex-wrap gap-3">
                  <button
                    type="button"
                    onClick={() => handleGrade()}
                    disabled={gradeMutation.isPending || currentCard.suspended || !selectedRating}
                    className="fabric-btn fabric-btn-primary"
                  >
                    <CheckCircle2 className="h-4 w-4" />
                    {gradeMutation.isPending ? '提交中...' : '确认评分并写入复习记录'}
                  </button>
                </div>
              </div>
            ) : null}
          </section>
        </div>
      )}

      <section className="fabric-panel">
        <div>
          <p className="text-xs uppercase tracking-[0.2em] text-cloth-muted">Recent Logs</p>
          <h2 className="mt-1 font-serif text-2xl text-cloth-ink">最近日志</h2>
        </div>
        <div className="mt-4 grid gap-3 md:grid-cols-2 xl:grid-cols-4">
          {(logsQuery.data ?? []).length ? (
            (logsQuery.data ?? []).map((log) => (
              <div key={log.id} className="fabric-card space-y-2">
                <div className="flex items-center justify-between gap-2">
                  <p className="text-sm font-semibold text-cloth-ink">卡片 #{log.review_card_id}</p>
                  <span className="rounded-full bg-cloth-panel px-2 py-1 text-xs text-cloth-muted">评分 {log.rating}</span>
                </div>
                <p className="text-xs text-cloth-muted">{formatDateTime(log.created_at)}</p>
                <p className="text-xs text-cloth-muted">时长：{formatSeconds(log.duration_seconds)}</p>
                <p className="text-sm text-cloth-ink">{log.note || '未填写备注'}</p>
              </div>
            ))
          ) : (
            <div className="fabric-card text-sm text-cloth-muted">暂无日志记录。</div>
          )}
        </div>
      </section>
    </div>
  )
}

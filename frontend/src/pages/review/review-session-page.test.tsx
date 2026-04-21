import { describe, expect, it, vi } from 'vitest'
import { fireEvent, screen, waitFor } from '@testing-library/react'
import { ReviewSessionPage } from '@/pages/review/review-session-page'
import { reviewApi } from '@/lib/review-api'
import { sampleReviewLogs, sampleReviewQueue, sampleReviewSubjects } from '@/test/fixtures'
import { createUser, renderWithProviders } from '@/test/test-utils'

vi.mock('@/lib/review-api', () => ({
  reviewApi: {
    getQueue: vi.fn(),
    listLogs: vi.fn(),
    listSubjects: vi.fn(),
    startSession: vi.fn(),
    heartbeatSession: vi.fn(),
    finalizeSession: vi.fn(),
    judgeAnswer: vi.fn(),
    gradeCard: vi.fn(),
  },
}))

describe('ReviewSessionPage', () => {
  it('renders queue and allows grading for viewer role', async () => {
    vi.mocked(reviewApi.getQueue).mockResolvedValue(sampleReviewQueue)
    vi.mocked(reviewApi.listLogs).mockResolvedValue(sampleReviewLogs)
    vi.mocked(reviewApi.listSubjects).mockResolvedValue(sampleReviewSubjects)
    vi.mocked(reviewApi.startSession).mockResolvedValue({
      active_card_id: 401,
      accumulated_seconds: 0,
      increment_seconds: 0,
      started_at: '2026-04-20T08:00:00Z',
      last_heartbeat_at: '2026-04-20T08:00:00Z',
    })
    vi.mocked(reviewApi.heartbeatSession).mockResolvedValue({
      active_card_id: 401,
      accumulated_seconds: 15,
      increment_seconds: 15,
      started_at: '2026-04-20T08:00:00Z',
      last_heartbeat_at: '2026-04-20T08:00:15Z',
    })
    vi.mocked(reviewApi.finalizeSession).mockResolvedValue({
      card_id: 401,
      duration_seconds: 15,
      server_accumulated_seconds: 15,
      client_reported_seconds: 0,
      finalized_at: '2026-04-20T08:00:15Z',
    })
    vi.mocked(reviewApi.judgeAnswer).mockResolvedValue({
      card_id: 401,
      answer: '先执行微任务，再进入下一个宏任务。',
      suggested_rating: 3,
      expected_answer: '事件循环会先清空微任务，再执行下一个宏任务。',
      correctness: 'correct',
      explanation: '回答覆盖了事件循环的关键调度顺序。',
      judge_status: 'ai',
      judge_error: null,
    })
    vi.mocked(reviewApi.gradeCard).mockResolvedValue({
      card: { id: 401, state_json: {}, due_at: '2026-04-20T08:00:00Z', last_reviewed_at: '2026-04-18T12:00:00Z' },
      review_log: sampleReviewLogs[0],
    })

    renderWithProviders(<ReviewSessionPage />, { user: createUser({ role: 'viewer' }), route: '/review/session?subject=%E8%AE%A1%E7%AE%97%E6%9C%BA&limit=5' })

    expect(await screen.findByText('Event Loop')).toBeInTheDocument()
    expect(screen.getByDisplayValue('计算机（到期 2）')).toBeInTheDocument()
    expect(screen.getByDisplayValue('5')).toBeInTheDocument()
    expect(document.querySelector('.note-prose .katex')).toBeTruthy()
    expect(screen.getByText('viewer / admin 均可提交评分与日志')).toBeInTheDocument()

    fireEvent.change(screen.getByPlaceholderText(/先按最小记忆单元用自己的话作答/i), { target: { value: '先执行微任务，再进入下一个宏任务。' } })
    fireEvent.click(screen.getByRole('button', { name: '获取 AI 评分建议' }))

    expect(await screen.findByText('评分建议与讲解')).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: /Good/i }))
    fireEvent.click(screen.getByRole('button', { name: '确认评分并写入复习记录' }))

    await waitFor(() => {
      expect(reviewApi.judgeAnswer).toHaveBeenCalledWith(401, expect.objectContaining({ answer: '先执行微任务，再进入下一个宏任务。' }))
      expect(reviewApi.finalizeSession).toHaveBeenCalledWith(401, expect.objectContaining({ duration_seconds: expect.any(Number) }))
      expect(reviewApi.gradeCard).toHaveBeenCalledWith(401, expect.objectContaining({ rating: 3, duration_seconds: 15 }))
    })
  })

  it('shows empty-state copy when queue is empty', async () => {
    vi.mocked(reviewApi.getQueue).mockResolvedValue([])
    vi.mocked(reviewApi.listLogs).mockResolvedValue([])
    vi.mocked(reviewApi.listSubjects).mockResolvedValue(sampleReviewSubjects)
    vi.mocked(reviewApi.startSession).mockResolvedValue({
      active_card_id: null,
      accumulated_seconds: 0,
      increment_seconds: 0,
      started_at: null,
      last_heartbeat_at: null,
    })
    vi.mocked(reviewApi.heartbeatSession).mockResolvedValue({
      active_card_id: null,
      accumulated_seconds: 0,
      increment_seconds: 0,
      started_at: null,
      last_heartbeat_at: null,
    })
    vi.mocked(reviewApi.finalizeSession).mockResolvedValue({
      card_id: 0,
      duration_seconds: 0,
      server_accumulated_seconds: 0,
      client_reported_seconds: 0,
      finalized_at: '2026-04-20T08:00:15Z',
    })

    renderWithProviders(<ReviewSessionPage />, { user: createUser() })

    expect(await screen.findByText('当前没有待复习卡片')).toBeInTheDocument()
  })
})

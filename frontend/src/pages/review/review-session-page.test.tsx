import { describe, expect, it, vi } from 'vitest'
import { fireEvent, screen, waitFor } from '@testing-library/react'
import { ReviewSessionPage } from '@/pages/review/review-session-page'
import { reviewApi } from '@/lib/review-api'
import { sampleReviewLogs, sampleReviewQueue } from '@/test/fixtures'
import { createUser, renderWithProviders } from '@/test/test-utils'

vi.mock('@/lib/review-api', () => ({
  reviewApi: {
    getQueue: vi.fn(),
    listLogs: vi.fn(),
    gradeCard: vi.fn(),
  },
}))

describe('ReviewSessionPage', () => {
  it('renders queue and allows grading for viewer role', async () => {
    vi.mocked(reviewApi.getQueue).mockResolvedValue(sampleReviewQueue)
    vi.mocked(reviewApi.listLogs).mockResolvedValue(sampleReviewLogs)
    vi.mocked(reviewApi.gradeCard).mockResolvedValue({
      card: { id: 401, state_json: {}, due_at: '2026-04-20T08:00:00Z', last_reviewed_at: '2026-04-18T12:00:00Z' },
      review_log: sampleReviewLogs[0],
    })

    renderWithProviders(<ReviewSessionPage />, { user: createUser({ role: 'viewer' }) })

    expect(await screen.findByText('Event Loop')).toBeInTheDocument()
    expect(screen.getByText('viewer / admin 均可提交评分与日志')).toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: /Good/i }))

    await waitFor(() => {
      expect(reviewApi.gradeCard).toHaveBeenCalledWith(401, expect.objectContaining({ rating: 3 }))
    })
  })

  it('shows empty-state copy when queue is empty', async () => {
    vi.mocked(reviewApi.getQueue).mockResolvedValue([])
    vi.mocked(reviewApi.listLogs).mockResolvedValue([])

    renderWithProviders(<ReviewSessionPage />, { user: createUser() })

    expect(await screen.findByText('当前没有待复习卡片')).toBeInTheDocument()
  })
})

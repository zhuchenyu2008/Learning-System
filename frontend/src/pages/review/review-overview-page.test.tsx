import { describe, expect, it, vi } from 'vitest'
import { fireEvent, screen, waitFor } from '@testing-library/react'
import { ReviewOverviewPage } from '@/pages/review/review-overview-page'
import { notesApi } from '@/lib/notes-api'
import { reviewApi } from '@/lib/review-api'
import { sampleNotes, sampleReviewLogs, sampleReviewOverview } from '@/test/fixtures'
import { createUser, renderWithProviders } from '@/test/test-utils'

vi.mock('@/lib/notes-api', () => ({
  notesApi: {
    listNotes: vi.fn(),
  },
}))

vi.mock('@/lib/review-api', () => ({
  reviewApi: {
    getOverview: vi.fn(),
    listLogs: vi.fn(),
    listSummaries: vi.fn(),
    listMindmaps: vi.fn(),
    bootstrapCards: vi.fn(),
  },
}))

describe('ReviewOverviewPage', () => {
  it('renders overview cards and keeps bootstrap disabled for viewer', async () => {
    vi.mocked(reviewApi.getOverview).mockResolvedValue(sampleReviewOverview)
    vi.mocked(reviewApi.listLogs).mockResolvedValue(sampleReviewLogs)
    vi.mocked(reviewApi.listSummaries).mockResolvedValue([])
    vi.mocked(reviewApi.listMindmaps).mockResolvedValue([])

    renderWithProviders(<ReviewOverviewPage />, { user: createUser({ role: 'viewer' }) })

    expect(await screen.findByText('复习总览')).toBeInTheDocument()
    expect(screen.getByText('当前 FSRS 卡片总数')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: '初始化复习卡' })).toBeDisabled()
  })

  it('allows admin to bootstrap review cards', async () => {
    vi.mocked(reviewApi.getOverview).mockResolvedValue(sampleReviewOverview)
    vi.mocked(reviewApi.listLogs).mockResolvedValue(sampleReviewLogs)
    vi.mocked(reviewApi.listSummaries).mockResolvedValue([])
    vi.mocked(reviewApi.listMindmaps).mockResolvedValue([])
    vi.mocked(notesApi.listNotes).mockResolvedValue(sampleNotes)
    vi.mocked(reviewApi.bootstrapCards).mockResolvedValue({
      created_cards: 5,
      created_knowledge_points: 4,
      note_ids: [101],
    })

    renderWithProviders(<ReviewOverviewPage />, { user: createUser({ role: 'admin' }) })

    fireEvent.click(await screen.findByRole('button', { name: '初始化复习卡' }))

    await waitFor(() => {
      expect(reviewApi.bootstrapCards).toHaveBeenCalledWith({ note_ids: [], all_notes: true })
    })
    expect(await screen.findByText('已初始化 5 张复习卡，涉及 4 个知识点。')).toBeInTheDocument()
  })
})

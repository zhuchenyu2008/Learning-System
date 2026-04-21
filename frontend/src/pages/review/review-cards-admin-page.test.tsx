import { describe, expect, it, vi } from 'vitest'
import { fireEvent, screen, waitFor } from '@testing-library/react'
import { ReviewCardsAdminPage } from '@/pages/review/review-cards-admin-page'
import { notesApi } from '@/lib/notes-api'
import { reviewApi } from '@/lib/review-api'
import { sampleNotes, sampleReviewQueue, sampleReviewSubjects } from '@/test/fixtures'
import { createUser, renderWithProviders } from '@/test/test-utils'

vi.mock('@/lib/notes-api', () => ({
  notesApi: {
    listNotes: vi.fn(),
  },
}))

vi.mock('@/lib/review-api', () => ({
  reviewApi: {
    listSubjects: vi.fn(),
    listAdminCards: vi.fn(),
    createAdminCard: vi.fn(),
    deleteAdminCard: vi.fn(),
  },
}))

describe('ReviewCardsAdminPage', () => {
  it('renders list and allows creating/deleting cards', async () => {
    vi.mocked(notesApi.listNotes).mockResolvedValue(sampleNotes)
    vi.mocked(reviewApi.listSubjects).mockResolvedValue(sampleReviewSubjects)
    vi.mocked(reviewApi.listAdminCards).mockImplementation(async () => sampleReviewQueue)
    vi.mocked(reviewApi.createAdminCard).mockResolvedValue(sampleReviewQueue[0])
    vi.mocked(reviewApi.deleteAdminCard).mockResolvedValue({ card_id: 401, deleted: true, deleted_knowledge_point_id: 501 })

    renderWithProviders(<ReviewCardsAdminPage />, { user: createUser({ role: 'admin' }) })

    expect(await screen.findByText('复习卡片管理')).toBeInTheDocument()
    await waitFor(() => {
      expect(reviewApi.listAdminCards).toHaveBeenCalled()
    })

    const selects = screen.getAllByRole('combobox')
    fireEvent.change(selects[0], { target: { value: '101' } })
    fireEvent.change(screen.getAllByRole('textbox')[0], { target: { value: '新卡片' } })
    fireEvent.change(screen.getAllByRole('textbox')[1], { target: { value: '新内容' } })
    fireEvent.click(screen.getByRole('button', { name: '新增复习卡' }))

    await waitFor(() => {
      expect(reviewApi.createAdminCard).toHaveBeenCalledWith(expect.objectContaining({ note_id: 101, title: '新卡片', content_md: '新内容' }))
    })

    fireEvent.click(screen.getByRole('button', { name: /删除/i }))
    await waitFor(() => {
      expect(reviewApi.deleteAdminCard).toHaveBeenCalledWith(401)
    })
  })
})

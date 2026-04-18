import { describe, expect, it, vi } from 'vitest'
import { fireEvent, screen, waitFor } from '@testing-library/react'
import { ReviewSummariesPage } from '@/pages/review/review-summaries-page'
import { notesApi } from '@/lib/notes-api'
import { reviewApi } from '@/lib/review-api'
import { sampleNotes } from '@/test/fixtures'
import { createUser, renderWithProviders } from '@/test/test-utils'

vi.mock('@/lib/notes-api', () => ({
  notesApi: {
    listNotes: vi.fn(),
  },
}))

vi.mock('@/lib/review-api', () => ({
  reviewApi: {
    listSummaries: vi.fn(),
    generateSummary: vi.fn(),
  },
}))

describe('ReviewSummariesPage', () => {
  it('blocks generation for viewer and still renders artifacts area', async () => {
    vi.mocked(notesApi.listNotes).mockResolvedValue(sampleNotes)
    vi.mocked(reviewApi.listSummaries).mockResolvedValue([])

    renderWithProviders(<ReviewSummariesPage />, { user: createUser({ role: 'viewer' }) })

    expect(screen.getByRole('button', { name: '生成总结' })).toBeDisabled()
    expect(await screen.findByText('暂无总结产物')).toBeInTheDocument()
  })

  it('allows admin to generate summary for selected notes', async () => {
    vi.mocked(notesApi.listNotes).mockResolvedValue(sampleNotes)
    vi.mocked(reviewApi.listSummaries).mockResolvedValue([])
    vi.mocked(reviewApi.generateSummary).mockResolvedValue({
      job_id: 910,
      artifact_id: 911,
      output_note_id: 102,
      relative_path: 'notes/summary.md',
      status: 'queued',
    })

    renderWithProviders(<ReviewSummariesPage />, { user: createUser({ role: 'admin' }) })

    const checkboxes = await screen.findAllByRole('checkbox')
    fireEvent.click(checkboxes[0])
    fireEvent.click(screen.getByRole('button', { name: '生成总结' }))

    await waitFor(() => {
      expect(reviewApi.generateSummary).toHaveBeenCalledWith({
        scope: 'manual',
        note_ids: [101],
        prompt_extra: null,
      })
    })
  })
})

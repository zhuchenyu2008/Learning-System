import { describe, expect, it, vi } from 'vitest'
import { fireEvent, screen, waitFor } from '@testing-library/react'
import { ReviewMindmapsPage } from '@/pages/review/review-mindmaps-page'
import { notesApi } from '@/lib/notes-api'
import { reviewApi } from '@/lib/review-api'
import { sampleNoteDetail, sampleNotes } from '@/test/fixtures'
import { createUser, renderWithProviders } from '@/test/test-utils'

vi.mock('@/components/mermaid-renderer', () => ({
  MermaidRenderer: ({ chart }: { chart: string }) => <div data-testid="mindmap-mermaid">{chart}</div>,
}))

vi.mock('@/lib/notes-api', () => ({
  notesApi: {
    listNotes: vi.fn(),
    getNoteDetail: vi.fn(),
  },
}))

vi.mock('@/lib/review-api', () => ({
  reviewApi: {
    listMindmaps: vi.fn(),
    generateMindmap: vi.fn(),
  },
}))

describe('ReviewMindmapsPage', () => {
  it('renders existing mindmap artifact and previews mermaid output', async () => {
    vi.mocked(notesApi.listNotes).mockResolvedValue(sampleNotes)
    vi.mocked(notesApi.getNoteDetail).mockResolvedValue(sampleNoteDetail)
    vi.mocked(reviewApi.listMindmaps).mockResolvedValue([
      {
        id: 801,
        artifact_type: 'mindmap',
        scope_type: 'manual',
        note_ids_json: [101],
        prompt_extra: null,
        output_note_id: 101,
        status: 'completed',
        created_at: '2026-04-18T11:00:00Z',
        updated_at: '2026-04-18T11:10:00Z',
      },
    ])

    renderWithProviders(<ReviewMindmapsPage />, { user: createUser({ role: 'admin' }) })

    expect(await screen.findByText('产物 #801')).toBeInTheDocument()
    const previews = await screen.findAllByTestId('mindmap-mermaid')
    expect(previews[0]).toHaveTextContent('graph TD')
    expect(screen.getByText('allowed html')).toBeInTheDocument()
  })

  it('blocks generation button for viewer role', async () => {
    vi.mocked(notesApi.listNotes).mockResolvedValue(sampleNotes)
    vi.mocked(reviewApi.listMindmaps).mockResolvedValue([])

    renderWithProviders(<ReviewMindmapsPage />, { user: createUser({ role: 'viewer' }) })

    const button = screen.getByRole('button', { name: '生成导图' })
    expect(button).toBeDisabled()
  })

  it('allows admin to generate mindmaps for selected notes', async () => {
    vi.mocked(notesApi.listNotes).mockResolvedValue(sampleNotes)
    vi.mocked(notesApi.getNoteDetail).mockResolvedValue(sampleNoteDetail)
    vi.mocked(reviewApi.listMindmaps).mockResolvedValue([])
    vi.mocked(reviewApi.generateMindmap).mockResolvedValue({
      job_id: 901,
      artifact_id: 902,
      output_note_id: 101,
      relative_path: 'notes/mindmap.md',
      status: 'queued',
      celery_task_id: 'task-1',
    })

    renderWithProviders(<ReviewMindmapsPage />, { user: createUser({ role: 'admin' }) })

    const noteCheckbox = await screen.findByRole('checkbox', { name: /Mermaid Note/i })
    fireEvent.click(noteCheckbox)
    fireEvent.click(screen.getByRole('button', { name: '生成导图' }))

    await waitFor(() => {
      expect(reviewApi.generateMindmap).toHaveBeenCalledWith({
        scope: 'manual',
        note_ids: [101],
        prompt_extra: null,
      })
    })
  })
})

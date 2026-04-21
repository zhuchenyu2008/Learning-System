import { describe, expect, it, vi } from 'vitest'
import { fireEvent, screen, waitFor } from '@testing-library/react'
import { ReviewSummariesPage } from '@/pages/review/review-summaries-page'
import { notesApi } from '@/lib/notes-api'
import { reviewApi } from '@/lib/review-api'
import { sampleArtifactNotes, sampleNoteDetail, sampleNotes } from '@/test/fixtures'
import { createUser, renderWithProviders } from '@/test/test-utils'

vi.mock('@/lib/notes-api', () => ({
  notesApi: {
    listNotes: vi.fn(),
    getNoteDetail: vi.fn(),
  },
}))

vi.mock('@/lib/review-api', () => ({
  reviewApi: {
    listSummaries: vi.fn(),
    generateSummary: vi.fn(),
    deleteSummary: vi.fn(),
    getJob: vi.fn(),
  },
}))

describe('ReviewSummariesPage', () => {
  it('blocks generation for viewer and still renders artifacts area', async () => {
    vi.mocked(notesApi.listNotes).mockResolvedValue([...sampleNotes, ...sampleArtifactNotes])
    vi.mocked(reviewApi.listSummaries).mockResolvedValue([])

    renderWithProviders(<ReviewSummariesPage />, { user: createUser({ role: 'viewer' }) })

    expect(screen.getByRole('button', { name: '生成总结' })).toBeDisabled()
    expect(await screen.findByText('暂无总结产物')).toBeInTheDocument()
  })

  it('renders existing summary artifact and previews note detail', async () => {
    vi.mocked(notesApi.listNotes).mockResolvedValue([...sampleNotes, ...sampleArtifactNotes])
    vi.mocked(notesApi.getNoteDetail).mockResolvedValue({
      ...sampleNoteDetail,
      ...sampleArtifactNotes[1],
      title: 'Summary Note',
      content: '# Summary Heading\n\n- key point\n\n<div class="safe-html">summary html</div>',
    })
    vi.mocked(reviewApi.listSummaries).mockResolvedValue([
      {
        id: 811,
        artifact_type: 'summary',
        scope_type: 'manual',
        note_ids_json: [101],
        prompt_extra: '突出重点',
        output_note_id: 202,
        status: 'completed',
        created_at: '2026-04-18T11:00:00Z',
        updated_at: '2026-04-18T11:10:00Z',
      },
    ])

    renderWithProviders(<ReviewSummariesPage />, { user: createUser({ role: 'admin' }) })

    expect(await screen.findByText('产物 #811')).toBeInTheDocument()
    expect(await screen.findByText('Summary Heading')).toBeInTheDocument()
    expect(screen.getByText('summary html')).toBeInTheDocument()
    expect(notesApi.getNoteDetail).toHaveBeenCalledWith(202)
  })

  it('keeps card visual selection in sync with checkbox state', async () => {
    vi.mocked(notesApi.listNotes).mockResolvedValue([...sampleNotes, ...sampleArtifactNotes])
    vi.mocked(reviewApi.listSummaries).mockResolvedValue([])

    renderWithProviders(<ReviewSummariesPage />, { user: createUser({ role: 'admin' }) })

    const checkbox = (await screen.findAllByRole('checkbox'))[0]
    fireEvent.click(checkbox)

    expect(checkbox).toBeChecked()
    expect(checkbox.closest('label')).toHaveAttribute('data-selected', 'true')
  })

  it('allows admin to delete summary artifact', async () => {
    vi.stubGlobal('confirm', vi.fn(() => true))
    vi.mocked(notesApi.listNotes).mockResolvedValue([...sampleNotes, ...sampleArtifactNotes])
    vi.mocked(notesApi.getNoteDetail).mockResolvedValue({
      ...sampleNoteDetail,
      ...sampleArtifactNotes[1],
      title: 'Summary Note',
      content: '# Summary Heading',
    })
    vi.mocked(reviewApi.listSummaries).mockResolvedValue([
      {
        id: 811,
        artifact_type: 'summary',
        scope_type: 'manual',
        note_ids_json: [101],
        prompt_extra: null,
        output_note_id: 202,
        status: 'completed',
        created_at: '2026-04-18T11:00:00Z',
        updated_at: '2026-04-18T11:10:00Z',
      },
    ])
    vi.mocked(reviewApi.deleteSummary).mockResolvedValue({
      id: 811,
      artifact_id: 811,
      output_note_id: 202,
      deleted_note_id: 202,
      deleted_relative_paths: ['artifacts/summary/summary-note.md'],
    })

    renderWithProviders(<ReviewSummariesPage />, { user: createUser({ role: 'admin' }) })

    await screen.findByText('产物 #811')
    fireEvent.click(screen.getByRole('button', { name: '删除总结产物 811' }))

    await waitFor(() => {
      expect(reviewApi.deleteSummary).toHaveBeenCalledWith(811)
    })
  })

  it('allows admin to generate summary for selected notes', async () => {
    vi.mocked(notesApi.listNotes).mockResolvedValue([...sampleNotes, ...sampleArtifactNotes])
    vi.mocked(reviewApi.listSummaries).mockResolvedValue([])
    vi.mocked(reviewApi.generateSummary).mockResolvedValue({
      job_id: 910,
      artifact_id: null,
      output_note_id: null,
      relative_path: null,
      status: 'queued',
    })
    vi.mocked(reviewApi.getJob).mockResolvedValue({
      id: 910,
      job_type: 'summary_generation',
      status: 'pending',
      payload_json: {},
      result_json: {},
      logs_json: [],
      celery_task_id: 'task-summary-910',
      error_message: null,
      started_at: null,
      finished_at: null,
      created_at: '2026-04-18T11:00:00Z',
      updated_at: '2026-04-18T11:00:00Z',
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

    expect(screen.getByText('任务 #910 已创建，正在排队生成总结…')).toBeInTheDocument()
    expect(screen.queryByText(/输出笔记 #0/)).not.toBeInTheDocument()
  })
})

import { describe, expect, it, vi } from 'vitest'
import { fireEvent, screen, waitFor } from '@testing-library/react'
import { ReviewMindmapsPage } from '@/pages/review/review-mindmaps-page'
import { notesApi } from '@/lib/notes-api'
import { reviewApi } from '@/lib/review-api'
import { sampleArtifactNotes, sampleNoteDetail, sampleNotes } from '@/test/fixtures'
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
    deleteMindmap: vi.fn(),
    getJob: vi.fn(),
  },
}))

describe('ReviewMindmapsPage', () => {
  it('renders existing mindmap artifact and previews mermaid output', async () => {
    vi.mocked(notesApi.listNotes).mockResolvedValue([...sampleNotes, ...sampleArtifactNotes])
    vi.mocked(notesApi.getNoteDetail).mockResolvedValue(sampleNoteDetail)
    vi.mocked(reviewApi.listMindmaps).mockResolvedValue([
      {
        id: 801,
        artifact_type: 'mindmap',
        scope_type: 'manual',
        note_ids_json: [101],
        prompt_extra: null,
        output_note_id: 201,
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

  it('shows a local warning when a mindmap note contains an invalid mermaid fence', async () => {
    vi.mocked(notesApi.listNotes).mockResolvedValue([...sampleNotes, ...sampleArtifactNotes])
    vi.mocked(notesApi.getNoteDetail).mockResolvedValue({
      ...sampleNoteDetail,
      content: '# Broken\n\n```mermaid\n```',
    })
    vi.mocked(reviewApi.listMindmaps).mockResolvedValue([
      {
        id: 801,
        artifact_type: 'mindmap',
        scope_type: 'manual',
        note_ids_json: [101],
        prompt_extra: null,
        output_note_id: 201,
        status: 'completed',
        created_at: '2026-04-18T11:00:00Z',
        updated_at: '2026-04-18T11:10:00Z',
      },
    ])

    renderWithProviders(<ReviewMindmapsPage />, { user: createUser({ role: 'admin' }) })

    expect(await screen.findByText('当前 Mermaid 代码块格式异常，无法提取预览；你仍可在右侧查看原始 Markdown 输出。')).toBeInTheDocument()
    expect(screen.getByText('输出详情')).toBeInTheDocument()
  })

  it('blocks generation button for viewer role', async () => {
    vi.mocked(notesApi.listNotes).mockResolvedValue([...sampleNotes, ...sampleArtifactNotes])
    vi.mocked(reviewApi.listMindmaps).mockResolvedValue([])

    renderWithProviders(<ReviewMindmapsPage />, { user: createUser({ role: 'viewer' }) })

    const button = screen.getByRole('button', { name: '生成导图' })
    expect(button).toBeDisabled()
  })

  it('keeps card visual selection in sync with checkbox state', async () => {
    vi.mocked(notesApi.listNotes).mockResolvedValue([...sampleNotes, ...sampleArtifactNotes])
    vi.mocked(reviewApi.listMindmaps).mockResolvedValue([])

    renderWithProviders(<ReviewMindmapsPage />, { user: createUser({ role: 'admin' }) })

    const checkbox = await screen.findByRole('checkbox', { name: /Source Note/i })
    fireEvent.click(checkbox)

    expect(checkbox).toBeChecked()
    expect(checkbox.closest('label')).toHaveAttribute('data-selected', 'true')
  })

  it('allows admin to delete mindmap artifact', async () => {
    vi.stubGlobal('confirm', vi.fn(() => true))
    vi.mocked(notesApi.listNotes).mockResolvedValue([...sampleNotes, ...sampleArtifactNotes])
    vi.mocked(notesApi.getNoteDetail).mockResolvedValue(sampleNoteDetail)
    vi.mocked(reviewApi.listMindmaps).mockResolvedValue([
      {
        id: 801,
        artifact_type: 'mindmap',
        scope_type: 'manual',
        note_ids_json: [101],
        prompt_extra: null,
        output_note_id: 201,
        status: 'completed',
        created_at: '2026-04-18T11:00:00Z',
        updated_at: '2026-04-18T11:10:00Z',
      },
    ])
    vi.mocked(reviewApi.deleteMindmap).mockResolvedValue({
      id: 801,
      artifact_id: 801,
      output_note_id: 201,
      deleted_note_id: 201,
      deleted_relative_paths: ['artifacts/mindmap/mermaid-note.md'],
    })

    renderWithProviders(<ReviewMindmapsPage />, { user: createUser({ role: 'admin' }) })

    await screen.findByText('产物 #801')
    fireEvent.click(screen.getByRole('button', { name: '删除思维导图产物 801' }))

    await waitFor(() => {
      expect(reviewApi.deleteMindmap).toHaveBeenCalledWith(801)
    })
  })

  it('allows admin to generate mindmaps for selected notes', async () => {
    vi.mocked(notesApi.listNotes).mockResolvedValue([...sampleNotes, ...sampleArtifactNotes])
    vi.mocked(notesApi.getNoteDetail).mockResolvedValue(sampleNoteDetail)
    vi.mocked(reviewApi.listMindmaps).mockResolvedValue([])
    vi.mocked(reviewApi.generateMindmap).mockResolvedValue({
      job_id: 901,
      artifact_id: null,
      output_note_id: null,
      relative_path: null,
      status: 'queued',
      celery_task_id: 'task-1',
    })
    vi.mocked(reviewApi.getJob).mockResolvedValue({
      id: 901,
      job_type: 'mindmap_generation',
      status: 'pending',
      payload_json: {},
      result_json: {},
      logs_json: [],
      celery_task_id: 'task-1',
      error_message: null,
      started_at: null,
      finished_at: null,
      created_at: '2026-04-18T11:00:00Z',
      updated_at: '2026-04-18T11:00:00Z',
    })

    renderWithProviders(<ReviewMindmapsPage />, { user: createUser({ role: 'admin' }) })

    const noteCheckbox = await screen.findByRole('checkbox', { name: /Source Note/i })
    fireEvent.click(noteCheckbox)
    fireEvent.click(screen.getByRole('button', { name: '生成导图' }))

    await waitFor(() => {
      expect(reviewApi.generateMindmap).toHaveBeenCalledWith({
        scope: 'manual',
        note_ids: [101],
        prompt_extra: null,
      })
    })

    expect(screen.getByText('任务 #901 已创建，正在排队生成思维导图…')).toBeInTheDocument()
    expect(screen.queryByText(/输出笔记 #0/)).not.toBeInTheDocument()
  })
})

import { describe, expect, it, vi } from 'vitest'
import { fireEvent, screen, waitFor } from '@testing-library/react'
import type { Mock } from 'vitest'
import { NotesGeneratePage } from '@/pages/notes/notes-generate-page'
import { notesApi } from '@/lib/notes-api'
import { sampleSources } from '@/test/fixtures'
import { createUser, renderWithProviders } from '@/test/test-utils'

vi.mock('@/lib/notes-api', () => ({
  notesApi: {
    listSources: vi.fn(),
    uploadSource: vi.fn(),
    scanSources: vi.fn(),
    generateNotes: vi.fn(),
    deleteSource: vi.fn(),
    listJobs: vi.fn(),
  },
}))

describe('NotesGeneratePage', () => {
  const mockListSources = vi.mocked(notesApi.listSources)
  const mockListJobs = vi.mocked(notesApi.listJobs)

  it('disables admin-only generation controls for viewer', async () => {
    vi.mocked(notesApi.listSources).mockResolvedValue(sampleSources)
    mockListJobs.mockResolvedValue([])

    renderWithProviders(<NotesGeneratePage />, { user: createUser({ role: 'viewer' }) })

    expect(await screen.findByText('普通用户可访问此页，但生成能力保持禁用。')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: '扫描工作目录' })).toBeDisabled()
    expect(screen.getByRole('button', { name: '开始生成' })).toBeDisabled()
    expect(screen.getByLabelText('上传来源文件')).toBeDisabled()
  })

  it('allows admin to upload a source and auto-select it', async () => {
    vi.mocked(notesApi.listSources).mockResolvedValue([])
    mockListJobs.mockResolvedValue([])
    vi.mocked(notesApi.uploadSource).mockResolvedValue({
      id: 21,
      file_path: 'uploads/sources/lesson-abc123.pdf',
      file_type: 'pdf',
      checksum: 'abcdef1234567890',
      imported_at: '2026-04-18T09:10:00Z',
      metadata_json: {},
    })

    renderWithProviders(<NotesGeneratePage />, { user: createUser({ role: 'admin' }) })

    const input = await screen.findByLabelText('上传来源文件')
    const file = new File(['pdf-content'], 'lesson.pdf', { type: 'application/pdf' })
    fireEvent.change(input, { target: { files: [file] } })

    await waitFor(() => {
      expect(notesApi.uploadSource).toHaveBeenCalledWith({
        file,
        uploadDir: 'uploads/sources',
      })
    })

    expect(await screen.findByText('上传成功：资产 #21')).toBeInTheDocument()
  })

  it('shows queued status copy after creating job instead of misleading generated count', async () => {
    vi.mocked(notesApi.listSources).mockResolvedValue(sampleSources)
    mockListJobs.mockResolvedValue([
      {
        id: 99,
        job_type: 'note_generation',
        status: 'pending',
        payload_json: {},
        result_json: {},
        logs_json: [],
        celery_task_id: 'celery-99',
        error_message: null,
        started_at: null,
        finished_at: null,
        created_at: '2026-04-20T13:00:00Z',
        updated_at: '2026-04-20T13:00:01Z',
      },
    ])
    vi.mocked(notesApi.generateNotes).mockResolvedValue({
      job: 99,
      generated_note_ids: [],
      written_paths: [],
      status: 'pending',
    })

    renderWithProviders(<NotesGeneratePage />, { user: createUser({ role: 'admin' }) })

    const assetCheckbox = await screen.findByRole('checkbox', { name: /assets\/chapter-1\.pdf/i })
    fireEvent.click(assetCheckbox)
    fireEvent.click(screen.getByRole('button', { name: '开始生成' }))

    await waitFor(() => {
      expect(notesApi.generateNotes).toHaveBeenCalledWith({
        source_asset_ids: [11],
        note_directory: 'notes/generated',
        force_regenerate: false,
        sync_to_obsidian: false,
      })
    })

    expect(await screen.findByText('任务 #99 已创建，正在排队生成笔记…')).toBeInTheDocument()
    expect(screen.queryByText(/生成 0 篇笔记/)).not.toBeInTheDocument()
  })

  it('shows running status copy when job is in progress', async () => {
    vi.mocked(notesApi.listSources).mockResolvedValue(sampleSources)
    mockListJobs.mockResolvedValue([
      {
        id: 109,
        job_type: 'note_generation',
        status: 'running',
        payload_json: {},
        result_json: {},
        logs_json: [{ message: 'running' }],
        celery_task_id: 'celery-109',
        error_message: null,
        started_at: '2026-04-20T13:00:02Z',
        finished_at: null,
        created_at: '2026-04-20T13:00:00Z',
        updated_at: '2026-04-20T13:00:03Z',
      },
    ])
    vi.mocked(notesApi.generateNotes).mockResolvedValue({
      job: 109,
      generated_note_ids: [],
      written_paths: [],
      status: 'running',
    })

    renderWithProviders(<NotesGeneratePage />, { user: createUser({ role: 'admin' }) })

    const assetCheckbox = await screen.findByRole('checkbox', { name: /assets\/chapter-1\.pdf/i })
    fireEvent.click(assetCheckbox)
    fireEvent.click(screen.getByRole('button', { name: '开始生成' }))

    expect(await screen.findByText('任务 #109 正在生成笔记，请稍候…')).toBeInTheDocument()
  })

  it('shows completed status copy using job result count', async () => {
    vi.mocked(notesApi.listSources).mockResolvedValue(sampleSources)
    mockListJobs.mockResolvedValue([
      {
        id: 110,
        job_type: 'note_generation',
        status: 'completed',
        payload_json: {},
        result_json: { generated_note_ids: [201, 202] },
        logs_json: [{ message: 'completed' }],
        celery_task_id: 'celery-110',
        error_message: null,
        started_at: '2026-04-20T13:00:02Z',
        finished_at: '2026-04-20T13:00:05Z',
        created_at: '2026-04-20T13:00:00Z',
        updated_at: '2026-04-20T13:00:05Z',
      },
    ])
    vi.mocked(notesApi.generateNotes).mockResolvedValue({
      job: 110,
      generated_note_ids: [],
      written_paths: [],
      status: 'pending',
    })

    renderWithProviders(<NotesGeneratePage />, { user: createUser({ role: 'admin' }) })

    const assetCheckbox = await screen.findByRole('checkbox', { name: /assets\/chapter-1\.pdf/i })
    fireEvent.click(assetCheckbox)
    fireEvent.click(screen.getByRole('button', { name: '开始生成' }))

    expect(await screen.findByText('任务 #110 已完成，生成 2 篇笔记。')).toBeInTheDocument()
  })

  it('shows failed status copy when job fails', async () => {
    vi.mocked(notesApi.listSources).mockResolvedValue(sampleSources)
    mockListJobs.mockResolvedValue([
      {
        id: 111,
        job_type: 'note_generation',
        status: 'failed',
        payload_json: {},
        result_json: {},
        logs_json: [{ message: 'failed' }],
        celery_task_id: 'celery-111',
        error_message: 'worker error',
        started_at: '2026-04-20T13:00:02Z',
        finished_at: '2026-04-20T13:00:04Z',
        created_at: '2026-04-20T13:00:00Z',
        updated_at: '2026-04-20T13:00:04Z',
      },
    ])
    vi.mocked(notesApi.generateNotes).mockResolvedValue({
      job: 111,
      generated_note_ids: [],
      written_paths: [],
      status: 'pending',
    })

    renderWithProviders(<NotesGeneratePage />, { user: createUser({ role: 'admin' }) })

    const assetCheckbox = await screen.findByRole('checkbox', { name: /assets\/chapter-1\.pdf/i })
    fireEvent.click(assetCheckbox)
    fireEvent.click(screen.getByRole('button', { name: '开始生成' }))

    expect(await screen.findByText('任务 #111 生成失败：worker error')).toBeInTheDocument()
  })

  it('keeps checkbox controlled state stable after refetch with reordered assets', async () => {
    mockListJobs.mockResolvedValue([])
    const refetchedSources = [
      {
        id: 12,
        file_path: 'assets/chapter-2.pdf',
        file_type: 'pdf' as const,
        checksum: 'bbbbbb1234567890',
        imported_at: '2026-04-18T09:05:00Z',
        metadata_json: {},
      },
      sampleSources[0],
    ]

    mockListSources.mockImplementation(() => Promise.resolve(refetchedSources))
    vi.mocked(notesApi.generateNotes).mockResolvedValue({
      job: 108,
      generated_note_ids: [301],
      written_paths: ['notes/generated/chapter-1.md'],
    })

    renderWithProviders(<NotesGeneratePage />, { user: createUser({ role: 'admin' }) })

    const assetCheckbox = await screen.findByRole('checkbox', { name: /assets\/chapter-1\.pdf/i })
    fireEvent.click(assetCheckbox)

    await waitFor(() => {
      expect(assetCheckbox).toBeChecked()
    })

    fireEvent.click(screen.getByRole('button', { name: '开始生成' }))

    await waitFor(() => {
      expect(notesApi.generateNotes).toHaveBeenCalledWith({
        source_asset_ids: [11],
        note_directory: 'notes/generated',
        force_regenerate: false,
        sync_to_obsidian: false,
      })
    })
  })

  it('drops stale selected ids after sources refetch removes the asset', async () => {
    mockListJobs.mockResolvedValue([])
    const listSourcesMock = mockListSources as unknown as Mock
    listSourcesMock.mockImplementationOnce(() => Promise.resolve(sampleSources))
    listSourcesMock.mockImplementation(() => Promise.resolve([]))
    vi.mocked(notesApi.deleteSource).mockResolvedValue({ id: 11 })

    renderWithProviders(<NotesGeneratePage />, { user: createUser({ role: 'admin' }) })

    const assetCheckbox = await screen.findByRole('checkbox', { name: /assets\/chapter-1\.pdf/i })
    fireEvent.click(assetCheckbox)
    expect(assetCheckbox).toBeChecked()

    const deleteButton = screen.getByRole('button', { name: '删除' })
    fireEvent.click(deleteButton)

    await waitFor(() => {
      expect(notesApi.deleteSource).toHaveBeenCalledWith(11)
    })

    await waitFor(() => {
      expect(screen.getByRole('button', { name: '开始生成' })).toBeDisabled()
    })
  })

  it('keeps asset card visual selection in sync with checkbox state', async () => {
    vi.mocked(notesApi.listSources).mockResolvedValue(sampleSources)
    mockListJobs.mockResolvedValue([])

    renderWithProviders(<NotesGeneratePage />, { user: createUser({ role: 'admin' }) })

    const assetCheckbox = await screen.findByRole('checkbox', { name: /assets\/chapter-1\.pdf/i })
    fireEvent.click(assetCheckbox)

    expect(assetCheckbox).toBeChecked()
    expect(assetCheckbox.closest('div.rounded-xl')).toHaveAttribute('data-selected', 'true')
  })

  it('allows admin to delete a source asset without changing checkbox selection accidentally', async () => {
    vi.mocked(notesApi.listSources).mockResolvedValue(sampleSources)
    mockListJobs.mockResolvedValue([])
    vi.mocked(notesApi.deleteSource).mockResolvedValue({ id: 11 })

    renderWithProviders(<NotesGeneratePage />, { user: createUser({ role: 'admin' }) })

    const assetCheckbox = await screen.findByRole('checkbox', { name: /assets\/chapter-1\.pdf/i })
    expect(assetCheckbox).not.toBeChecked()

    const deleteButton = screen.getByRole('button', { name: '删除' })
    fireEvent.click(deleteButton)

    await waitFor(() => {
      expect(notesApi.deleteSource).toHaveBeenCalledWith(11)
    })

    expect(assetCheckbox).not.toBeChecked()
  })
})

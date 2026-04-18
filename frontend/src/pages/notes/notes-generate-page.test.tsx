import { describe, expect, it, vi } from 'vitest'
import { fireEvent, screen, waitFor } from '@testing-library/react'
import { NotesGeneratePage } from '@/pages/notes/notes-generate-page'
import { notesApi } from '@/lib/notes-api'
import { sampleSources } from '@/test/fixtures'
import { createUser, renderWithProviders } from '@/test/test-utils'

vi.mock('@/lib/notes-api', () => ({
  notesApi: {
    listSources: vi.fn(),
    scanSources: vi.fn(),
    generateNotes: vi.fn(),
  },
}))

describe('NotesGeneratePage', () => {
  it('disables admin-only generation controls for viewer', async () => {
    vi.mocked(notesApi.listSources).mockResolvedValue(sampleSources)

    renderWithProviders(<NotesGeneratePage />, { user: createUser({ role: 'viewer' }) })

    expect(await screen.findByText('普通用户可访问此页但所有生成能力保持禁用。')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: '扫描工作目录' })).toBeDisabled()
    expect(screen.getByRole('button', { name: '触发笔记生成' })).toBeDisabled()
  })

  it('allows admin to select sources and trigger generation', async () => {
    vi.mocked(notesApi.listSources).mockResolvedValue(sampleSources)
    vi.mocked(notesApi.generateNotes).mockResolvedValue({
      job: 99,
      generated_note_ids: [101],
      written_paths: ['notes/generated/mermaid-note.md'],
    })

    renderWithProviders(<NotesGeneratePage />, { user: createUser({ role: 'admin' }) })

    const assetCheckbox = await screen.findByRole('checkbox', { name: /assets\/chapter-1\.pdf/i })
    fireEvent.click(assetCheckbox)
    fireEvent.click(screen.getByRole('button', { name: '触发笔记生成' }))

    await waitFor(() => {
      expect(notesApi.generateNotes).toHaveBeenCalledWith({
        source_asset_ids: [11],
        note_directory: 'notes/generated',
        force_regenerate: false,
        sync_to_obsidian: false,
      })
    })

    expect(await screen.findByText('已创建任务 #99，生成 1 篇笔记。')).toBeInTheDocument()
  })
})

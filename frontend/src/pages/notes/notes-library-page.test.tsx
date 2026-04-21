import { afterEach, describe, expect, it, vi } from 'vitest'
import { fireEvent, screen, waitFor } from '@testing-library/react'
import { NotesLibraryPage } from '@/pages/notes/notes-library-page'
import { notesApi } from '@/lib/notes-api'
import { sampleArtifactNotes, sampleNoteDetail, sampleNotes, sampleTree } from '@/test/fixtures'
import { createUser, renderWithProviders } from '@/test/test-utils'

vi.mock('@/lib/notes-api', () => ({
  notesApi: {
    listNotes: vi.fn(),
    getNotesTree: vi.fn(),
    getNoteDetail: vi.fn(),
    reportWatchSeconds: vi.fn(),
    deleteNote: vi.fn(),
  },
}))

describe('NotesLibraryPage', () => {
  afterEach(() => {
    vi.useRealTimers()
  })

  it('renders main-library notes and detail content without mixing artifact notes', async () => {
    vi.mocked(notesApi.listNotes).mockResolvedValue(sampleNotes)
    vi.mocked(notesApi.getNotesTree).mockResolvedValue(sampleTree)
    vi.mocked(notesApi.getNoteDetail).mockResolvedValue({
      ...sampleNoteDetail,
      id: 101,
      title: 'Source Note',
      relative_path: 'notes/source-note.md',
      note_type: 'source_note',
    })

    renderWithProviders(<NotesLibraryPage />, { user: createUser() })

    expect(await screen.findAllByText('Source Note')).not.toHaveLength(0)
    expect(screen.queryByText('Mermaid Note')).not.toBeInTheDocument()
    expect(await screen.findByText('allowed html')).toBeInTheDocument()
  })

  it('keeps note detail query wired to the selected note', async () => {
    vi.mocked(notesApi.listNotes).mockResolvedValue(sampleNotes)
    vi.mocked(notesApi.getNotesTree).mockResolvedValue(sampleTree)
    vi.mocked(notesApi.getNoteDetail).mockResolvedValue(sampleNoteDetail)

    renderWithProviders(<NotesLibraryPage />, { user: createUser() })

    expect(await screen.findByText('allowed html')).toBeInTheDocument()
    expect(notesApi.getNoteDetail).toHaveBeenCalledWith(101)
  })

  it('keeps artifact note types out of the main note_type filter options', async () => {
    vi.mocked(notesApi.listNotes).mockResolvedValue(sampleNotes)
    vi.mocked(notesApi.getNotesTree).mockResolvedValue(sampleTree)
    vi.mocked(notesApi.getNoteDetail).mockResolvedValue({
      ...sampleNoteDetail,
      id: 101,
      title: 'Source Note',
      relative_path: 'notes/source-note.md',
      note_type: 'source_note',
    })

    renderWithProviders(<NotesLibraryPage />, { user: createUser() })

    await screen.findByText('Source Note')
    expect(screen.getByRole('option', { name: '主笔记（默认）' })).toBeInTheDocument()
    expect(screen.queryByRole('option', { name: 'summary' })).not.toBeInTheDocument()
    expect(screen.queryByRole('option', { name: 'mindmap' })).not.toBeInTheDocument()
    expect(sampleArtifactNotes).toHaveLength(2)
  })

  it('allows deleting a note from library', async () => {
    vi.stubGlobal('confirm', vi.fn(() => true))
    vi.mocked(notesApi.listNotes).mockResolvedValue(sampleNotes)
    vi.mocked(notesApi.getNotesTree).mockResolvedValue(sampleTree)
    vi.mocked(notesApi.getNoteDetail).mockResolvedValue(sampleNoteDetail)
    vi.mocked(notesApi.deleteNote).mockResolvedValue({ id: 101, deleted_note_id: 101, deleted_artifact_id: null, deleted_relative_paths: ['notes/source-note.md'] })

    renderWithProviders(<NotesLibraryPage />, { user: createUser({ role: 'admin' }) })

    await screen.findByText('Source Note')
    fireEvent.click(screen.getByRole('button', { name: '删除 Source Note' }))

    await waitFor(() => {
      expect(notesApi.deleteNote).toHaveBeenCalledWith(101)
    })
  })

  it('reports watch_seconds through the dedicated watch endpoint flow on pagehide', async () => {
    const baseNow = Date.now()
    const nowSpy = vi.spyOn(Date, 'now').mockReturnValue(baseNow)
    vi.mocked(notesApi.reportWatchSeconds).mockReset()

    vi.mocked(notesApi.listNotes).mockResolvedValue(sampleNotes)
    vi.mocked(notesApi.getNotesTree).mockResolvedValue(sampleTree)
    vi.mocked(notesApi.getNoteDetail).mockResolvedValue(sampleNoteDetail)

    renderWithProviders(<NotesLibraryPage />, { user: createUser() })

    expect(await screen.findByText('allowed html')).toBeInTheDocument()

    nowSpy.mockReturnValue(baseNow + 4000)
    window.dispatchEvent(new Event('pagehide'))

    await waitFor(() => {
      expect(notesApi.reportWatchSeconds).toHaveBeenCalledWith(101, 4)
    })
  })
})

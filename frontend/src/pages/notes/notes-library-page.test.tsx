import { afterEach, describe, expect, it, vi } from 'vitest'
import { screen, waitFor } from '@testing-library/react'
import { NotesLibraryPage } from '@/pages/notes/notes-library-page'
import { notesApi } from '@/lib/notes-api'
import { sampleNoteDetail, sampleNotes, sampleTree } from '@/test/fixtures'
import { createUser, renderWithProviders } from '@/test/test-utils'

vi.mock('@/lib/notes-api', () => ({
  notesApi: {
    listNotes: vi.fn(),
    getNotesTree: vi.fn(),
    getNoteDetail: vi.fn(),
    reportWatchSeconds: vi.fn(),
  },
}))

describe('NotesLibraryPage', () => {
  afterEach(() => {
    vi.useRealTimers()
  })

  it('renders note list and detail content', async () => {
    vi.mocked(notesApi.listNotes).mockResolvedValue(sampleNotes)
    vi.mocked(notesApi.getNotesTree).mockResolvedValue(sampleTree)
    vi.mocked(notesApi.getNoteDetail).mockResolvedValue(sampleNoteDetail)

    renderWithProviders(<NotesLibraryPage />, { user: createUser() })

    expect(await screen.findAllByText('Mermaid Note')).not.toHaveLength(0)
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

import { describe, expect, it, vi } from 'vitest'
import { screen } from '@testing-library/react'
import { NoteDetailRenderer } from '@/components/note-detail-renderer'
import { sampleNoteDetail } from '@/test/fixtures'
import { renderWithProviders } from '@/test/test-utils'

vi.mock('@/components/mermaid-renderer', () => ({
  MermaidRenderer: ({ chart }: { chart: string }) => <div data-testid="mermaid-renderer">{chart}</div>,
}))

describe('NoteDetailRenderer', () => {
  it('renders markdown, sanitized html, and mermaid content', async () => {
    renderWithProviders(<NoteDetailRenderer note={sampleNoteDetail} />)

    expect(screen.getByRole('heading', { name: 'Mermaid Note' })).toBeInTheDocument()
    expect(screen.getByText('item 1')).toBeInTheDocument()
    expect(screen.getByText('allowed html')).toBeInTheDocument()
    expect(screen.queryByText("alert('blocked')")).not.toBeInTheDocument()
    expect(screen.getByTestId('mermaid-renderer')).toHaveTextContent('graph TD')
  })

  it('opens markdown links in a new tab safely', () => {
    const note = {
      ...sampleNoteDetail,
      content: '[open docs](https://example.com)',
    }

    renderWithProviders(<NoteDetailRenderer note={note} />)

    const link = screen.getByRole('link', { name: 'open docs' })
    expect(link).toHaveAttribute('target', '_blank')
    expect(link).toHaveAttribute('rel', 'noreferrer')
  })
})

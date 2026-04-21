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

  it('passes nested mermaid fences through the local renderer fallback boundary', () => {
    const note = {
      ...sampleNoteDetail,
      content: '# Nested Mermaid\n\n```mermaid\n```mermaid\ngraph TD\nA-->B\n```\n```',
    }

    renderWithProviders(<NoteDetailRenderer note={note} />)

    expect(screen.getByTestId('mermaid-renderer')).toHaveTextContent('```mermaid')
    expect(screen.getByTestId('mermaid-renderer')).toHaveTextContent('graph TD')
    expect(screen.getByTestId('mermaid-renderer')).toHaveTextContent('A-->B')
  })

  it('renders LaTeX expressions in core markdown content', () => {
    const note = {
      ...sampleNoteDetail,
      content: '# Math\n\nInline $E = mc^2$ and block:\n\n$$\\int_0^1 x^2 \\, dx$$',
    }

    const { container } = renderWithProviders(<NoteDetailRenderer note={note} />)

    expect(container.querySelectorAll('.katex').length).toBeGreaterThan(0)
    const mathAnnotations = Array.from(container.querySelectorAll('annotation[encoding="application/x-tex"]')).map((node) => node.textContent ?? '')
    expect(mathAnnotations).toContain('E = mc^2')
    expect(mathAnnotations).toContain('\\int_0^1 x^2 \\, dx')
    expect(screen.getByText('Math')).toBeInTheDocument()
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

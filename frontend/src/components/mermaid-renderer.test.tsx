import { beforeEach, describe, expect, it, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { MermaidRenderer } from '@/components/mermaid-renderer'

const initialize = vi.fn()
const renderMermaid = vi.fn()

vi.mock('mermaid', () => ({
  default: {
    initialize,
    render: renderMermaid,
  },
}))

describe('MermaidRenderer', () => {
  beforeEach(() => {
    initialize.mockReset()
    renderMermaid.mockReset()
  })

  it('renders svg output for valid mermaid charts', async () => {
    renderMermaid.mockResolvedValue({ svg: '<svg><text>diagram</text></svg>' })

    const { container } = render(<MermaidRenderer chart={'graph TD\nA-->B'} />)

    expect(screen.getByText('正在渲染 Mermaid 图表...')).toBeInTheDocument()

    await waitFor(() => {
      expect(container.querySelector('svg')).toBeInTheDocument()
    })

    expect(initialize).toHaveBeenCalledTimes(1)
    expect(renderMermaid).toHaveBeenCalled()
  })

  it('falls back to an error panel when rendering fails', async () => {
    renderMermaid.mockRejectedValue(new Error('syntax error'))

    render(<MermaidRenderer chart={'graph TD\nA-?B'} />)

    await waitFor(() => {
      expect(screen.getByText('Mermaid 渲染失败')).toBeInTheDocument()
    })

    expect(screen.getByText('syntax error')).toBeInTheDocument()
    expect(screen.getByText(/A-\?B/)).toBeInTheDocument()
  })
})

import { useEffect, useId, useMemo, useState } from 'react'

interface MermaidRendererProps {
  chart: string
  title?: string
}

type MermaidModule = typeof import('mermaid')

let mermaidModulePromise: Promise<MermaidModule> | null = null
let initialized = false

async function getMermaid() {
  if (!mermaidModulePromise) {
    mermaidModulePromise = import('mermaid')
  }

  const module = await mermaidModulePromise
  const mermaid = module.default

  if (!initialized) {
    mermaid.initialize({
      startOnLoad: false,
      securityLevel: 'strict',
      theme: 'neutral',
      fontFamily: 'Inter, ui-sans-serif, system-ui, sans-serif',
      suppressErrorRendering: true,
    })
    initialized = true
  }

  return mermaid
}

function sanitizeMermaidChart(chart: string) {
  const normalized = chart.replace(/\r\n/g, '\n').trim()
  if (!normalized) {
    return ''
  }

  const fencedMatch = normalized.match(/^```(?:\s*mermaid)?\s*\n?([\s\S]*?)\n?```$/i)
  let sanitized = fencedMatch?.[1]?.trim() ?? normalized

  sanitized = sanitized.replace(/^```\s*mermaid\s*$/gim, '').replace(/^```\s*$/gm, '').trim()

  if (/^mermaid\s*$/i.test(sanitized)) {
    return ''
  }

  if (/^mermaid\s*\n/i.test(sanitized)) {
    sanitized = sanitized.replace(/^mermaid\s*\n/i, '').trim()
  }

  return sanitized
}

export function MermaidRenderer({ chart, title = 'Mermaid 图表' }: MermaidRendererProps) {
  const reactId = useId()
  const sanitizedChart = useMemo(() => sanitizeMermaidChart(chart), [chart])
  const [svg, setSvg] = useState<string>('')
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false

    if (!sanitizedChart) {
      setSvg('')
      setError('Mermaid 内容为空或格式无效')
      return () => {
        cancelled = true
      }
    }

    async function render() {
      try {
        const mermaid = await getMermaid()
        const elementId = `mermaid-${reactId.replace(/:/g, '-')}`
        const result = await mermaid.render(elementId, sanitizedChart)
        if (!cancelled) {
          setSvg(result.svg)
          setError(null)
        }
      } catch (renderError) {
        if (!cancelled) {
          setSvg('')
          setError(renderError instanceof Error ? renderError.message : 'Mermaid render failed')
        }
      }
    }

    void render()
    return () => {
      cancelled = true
    }
  }, [sanitizedChart, reactId])

  if (error) {
    return (
      <figure className="rounded-xl border border-cloth-warn/40 bg-cloth-warn/10 p-4 text-sm text-cloth-ink">
        <figcaption className="font-semibold">{title} 渲染失败</figcaption>
        <p className="mt-2 text-cloth-muted">{error}</p>
        <details className="mt-3 rounded-lg bg-white/50 p-3">
          <summary className="cursor-pointer text-xs font-medium text-cloth-muted">查看 Mermaid 源码</summary>
          <pre className="mt-3 overflow-x-auto rounded-lg bg-white/60 p-3 text-xs">{sanitizedChart || chart}</pre>
        </details>
      </figure>
    )
  }

  if (!svg) {
    return <div className="rounded-xl border border-cloth-line/70 bg-white/40 p-4 text-sm text-cloth-muted">正在渲染 Mermaid 图表...</div>
  }

  return <div className="mermaid-diagram overflow-x-auto rounded-xl border border-cloth-line/70 bg-white/65 p-4" dangerouslySetInnerHTML={{ __html: svg }} />
}

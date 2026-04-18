import { useEffect, useId, useState } from 'react'

interface MermaidRendererProps {
  chart: string
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
    })
    initialized = true
  }

  return mermaid
}

export function MermaidRenderer({ chart }: MermaidRendererProps) {
  const reactId = useId()
  const [svg, setSvg] = useState<string>('')
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false

    async function render() {
      try {
        const mermaid = await getMermaid()
        const elementId = `mermaid-${reactId.replace(/:/g, '-')}`
        const result = await mermaid.render(elementId, chart)
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
  }, [chart, reactId])

  if (error) {
    return (
      <div className="rounded-xl border border-cloth-warn/40 bg-cloth-warn/10 p-4 text-sm text-cloth-ink">
        <p className="font-semibold">Mermaid 渲染失败</p>
        <p className="mt-2 text-cloth-muted">{error}</p>
        <pre className="mt-3 overflow-x-auto rounded-lg bg-white/60 p-3 text-xs">{chart}</pre>
      </div>
    )
  }

  if (!svg) {
    return <div className="rounded-xl border border-cloth-line/70 bg-white/40 p-4 text-sm text-cloth-muted">正在渲染 Mermaid 图表...</div>
  }

  return <div className="mermaid-diagram overflow-x-auto rounded-xl border border-cloth-line/70 bg-white/65 p-4" dangerouslySetInnerHTML={{ __html: svg }} />
}

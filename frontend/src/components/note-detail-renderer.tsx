import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import rehypeRaw from 'rehype-raw'
import rehypeSanitize, { defaultSchema } from 'rehype-sanitize'
import { FileText } from 'lucide-react'
import type { Components } from 'react-markdown'
import { MermaidRenderer } from '@/components/mermaid-renderer'
import type { NoteDetail } from '@/types/notes'

interface NoteDetailRendererProps {
  note: NoteDetail
}

const sanitizeSchema = {
  ...defaultSchema,
  tagNames: [
    ...(defaultSchema.tagNames ?? []),
    'section',
    'article',
    'header',
    'footer',
    'figure',
    'figcaption',
    'mark',
    'details',
    'summary',
    'kbd',
  ],
  attributes: {
    ...defaultSchema.attributes,
    '*': [...(defaultSchema.attributes?.['*'] ?? []), 'className', 'class'],
    a: [...(defaultSchema.attributes?.a ?? []), 'target', 'rel'],
    code: [...(defaultSchema.attributes?.code ?? []), 'className', 'class'],
    div: [...(defaultSchema.attributes?.div ?? []), 'className', 'class'],
    img: [...(defaultSchema.attributes?.img ?? []), 'src', 'alt', 'title', 'width', 'height', 'loading'],
    span: [...(defaultSchema.attributes?.span ?? []), 'className', 'class'],
  },
}

const markdownComponents: Components = {
  code(props) {
    const { className, children, ...rest } = props
    const match = /language-(\w+)/.exec(className ?? '')
    const code = String(children).replace(/\n$/, '')

    if (match?.[1] === 'mermaid') {
      return <MermaidRenderer chart={code} />
    }

    return (
      <code className={className} {...rest}>
        {children}
      </code>
    )
  },
  a(props) {
    return <a {...props} target="_blank" rel="noreferrer" />
  },
}

function formatDate(value: string) {
  return new Intl.DateTimeFormat('zh-CN', {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(new Date(value))
}

export function NoteDetailRenderer({ note }: NoteDetailRendererProps) {
  return (
    <article className="space-y-4">
      <header className="rounded-2xl border border-cloth-line/80 bg-white/55 p-5 shadow-panel fabric-glow">
        <div className="flex flex-wrap items-center gap-2">
          <span className="rounded-full bg-cloth-panel px-3 py-1 text-xs uppercase tracking-[0.18em] text-cloth-muted">
            {note.note_type}
          </span>
          {note.source_asset_id ? (
            <span className="rounded-full bg-cloth-panel px-3 py-1 text-xs text-cloth-muted">来源资产 #{note.source_asset_id}</span>
          ) : null}
          <span className="inline-flex items-center gap-1 rounded-full border border-cloth-line/70 bg-white/70 px-3 py-1 text-xs text-cloth-muted">
            <FileText className="h-3.5 w-3.5" />
            Markdown 阅读视图
          </span>
        </div>
        <h2 className="mt-3 font-serif text-3xl text-cloth-ink">{note.title}</h2>
        <div className="mt-3 grid gap-2 text-sm text-cloth-muted md:grid-cols-2">
          <div>
            <span className="font-medium text-cloth-ink">路径：</span>
            <span className="break-all">{note.relative_path}</span>
          </div>
          <div>
            <span className="font-medium text-cloth-ink">更新时间：</span>
            {formatDate(note.updated_at)}
          </div>
        </div>
      </header>

      <div className="note-prose rounded-2xl border border-cloth-line/80 bg-white/80 p-5 shadow-panel fabric-glow lg:p-7">
        <ReactMarkdown
          remarkPlugins={[remarkGfm]}
          rehypePlugins={[rehypeRaw, [rehypeSanitize, sanitizeSchema]]}
          components={markdownComponents}
        >
          {note.content}
        </ReactMarkdown>
      </div>
    </article>
  )
}

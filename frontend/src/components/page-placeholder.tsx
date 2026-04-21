import clsx from 'clsx'
import type { PropsWithChildren } from 'react'

interface PagePlaceholderProps extends PropsWithChildren {
  title: string
  description: string
  className?: string
  actions?: React.ReactNode
}

export function PagePlaceholder({ title, description, actions, className, children }: PagePlaceholderProps) {
  return (
    <section className={clsx('fabric-panel flex min-h-[320px] flex-col gap-4', className)}>
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-cloth-line/45 pb-3">
        <div className="min-w-0">
          <p className="truncate text-xs font-semibold uppercase tracking-[0.2em] text-cloth-muted">{title}</p>
          <p className="sr-only">{description}</p>
        </div>
        {actions ? <div className="flex flex-wrap gap-3">{actions}</div> : null}
      </div>
      {children ? <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">{children}</div> : null}
    </section>
  )
}

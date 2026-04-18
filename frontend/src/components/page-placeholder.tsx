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
    <section className={clsx('fabric-panel flex min-h-[320px] flex-col gap-5', className)}>
      <div className="space-y-2">
        <p className="text-xs font-semibold uppercase tracking-[0.24em] text-cloth-accent">Module Scaffold</p>
        <h1 className="font-serif text-3xl text-cloth-ink">{title}</h1>
        <p className="max-w-3xl text-sm text-cloth-muted">{description}</p>
      </div>
      {actions ? <div className="flex flex-wrap gap-3">{actions}</div> : null}
      {children ? <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">{children}</div> : null}
    </section>
  )
}

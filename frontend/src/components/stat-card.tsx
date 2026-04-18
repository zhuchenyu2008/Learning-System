import clsx from 'clsx'
import type { PropsWithChildren } from 'react'

interface StatCardProps extends PropsWithChildren {
  title: string
  value: string
  tone?: 'default' | 'accent' | 'success' | 'warn'
}

export function StatCard({ title, value, tone = 'default', children }: StatCardProps) {
  return (
    <article
      className={clsx(
        'fabric-card flex min-h-[132px] flex-col justify-between gap-4',
        tone === 'accent' && 'border-cloth-accent/40',
        tone === 'success' && 'border-cloth-success/40',
        tone === 'warn' && 'border-cloth-warn/40',
      )}
    >
      <div>
        <p className="text-xs uppercase tracking-[0.2em] text-cloth-muted">{title}</p>
        <p className="mt-3 text-3xl font-semibold text-cloth-ink">{value}</p>
      </div>
      {children ? <div className="text-sm text-cloth-muted">{children}</div> : null}
    </article>
  )
}

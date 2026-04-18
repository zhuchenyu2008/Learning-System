import clsx from 'clsx'
import { AlertCircle, Inbox, LoaderCircle } from 'lucide-react'
import type { ReactNode } from 'react'

interface SettingsFieldProps {
  label: string
  hint?: string
  children: ReactNode
}

export function SettingsField({ label, hint, children }: SettingsFieldProps) {
  return (
    <label className="block space-y-2">
      <span className="text-sm font-medium text-cloth-ink">{label}</span>
      {children}
      {hint ? <span className="block text-xs text-cloth-muted">{hint}</span> : null}
    </label>
  )
}

interface SettingsSectionProps {
  title: string
  description: string
  actions?: ReactNode
  children: ReactNode
  className?: string
}

export function SettingsSection({ title, description, actions, children, className }: SettingsSectionProps) {
  return (
    <section className={clsx('fabric-card space-y-4', className)}>
      <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
        <div className="space-y-1">
          <h3 className="text-lg font-semibold text-cloth-ink">{title}</h3>
          <p className="max-w-2xl text-sm text-cloth-muted">{description}</p>
        </div>
        {actions ? <div className="flex flex-wrap gap-2">{actions}</div> : null}
      </div>
      {children}
    </section>
  )
}

export function SectionStatus({ status, tone = 'default' }: { status: string; tone?: 'default' | 'success' | 'warning' | 'danger' }) {
  const toneClassName =
    tone === 'success'
      ? 'border-emerald-200 bg-emerald-50 text-emerald-700'
      : tone === 'warning'
        ? 'border-amber-200 bg-amber-50 text-amber-700'
        : tone === 'danger'
          ? 'border-red-200 bg-red-50 text-red-700'
          : 'border-cloth-line/80 bg-white/60 text-cloth-muted'

  return <span className={clsx('inline-flex rounded-full border px-2.5 py-1 text-xs', toneClassName)}>{status}</span>
}

export function EmptyStateCard({ title, description }: { title: string; description: string }) {
  return (
    <div className="rounded-xl border border-dashed border-cloth-line/80 bg-white/35 p-4">
      <div className="flex items-start gap-3">
        <div className="mt-0.5 rounded-full border border-cloth-line/70 bg-white/70 p-2 text-cloth-muted">
          <Inbox className="h-4 w-4" />
        </div>
        <div>
          <p className="text-sm font-medium text-cloth-ink">{title}</p>
          <p className="mt-2 text-sm text-cloth-muted">{description}</p>
        </div>
      </div>
    </div>
  )
}

export function LoadingStateCard({ title = '加载中', description = '正在获取最新内容，请稍候。' }: { title?: string; description?: string }) {
  return (
    <div className="rounded-xl border border-cloth-line/70 bg-white/45 p-4">
      <div className="flex items-start gap-3">
        <div className="mt-0.5 rounded-full border border-cloth-line/70 bg-white/80 p-2 text-cloth-accent">
          <LoaderCircle className="h-4 w-4 animate-spin" />
        </div>
        <div className="min-w-0 flex-1">
          <p className="text-sm font-medium text-cloth-ink">{title}</p>
          <p className="mt-2 text-sm text-cloth-muted">{description}</p>
          <div className="mt-3 space-y-2">
            <div className="h-2.5 w-3/4 rounded-full bg-cloth-line/30 shimmer" />
            <div className="h-2.5 w-full rounded-full bg-cloth-line/25 shimmer" />
            <div className="h-2.5 w-2/3 rounded-full bg-cloth-line/20 shimmer" />
          </div>
        </div>
      </div>
    </div>
  )
}

export function ErrorStateCard({ title = '加载失败', description }: { title?: string; description: string }) {
  return (
    <div className="rounded-xl border border-red-200 bg-red-50/85 p-4 text-red-800">
      <div className="flex items-start gap-3">
        <div className="mt-0.5 rounded-full border border-red-200 bg-white/80 p-2 text-red-500">
          <AlertCircle className="h-4 w-4" />
        </div>
        <div>
          <p className="text-sm font-semibold">{title}</p>
          <p className="mt-2 text-sm leading-6 text-red-700">{description}</p>
        </div>
      </div>
    </div>
  )
}

export function ReadonlyNotice({ isAdmin, reason }: { isAdmin: boolean; reason: string }) {
  if (isAdmin) return null
  return <div className="rounded-xl border border-amber-200 bg-amber-50/90 px-4 py-3 text-sm text-amber-800">{reason}</div>
}

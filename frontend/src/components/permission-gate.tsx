import clsx from 'clsx'
import type { ButtonHTMLAttributes, PropsWithChildren } from 'react'

interface PermissionGateProps extends PropsWithChildren {
  allowed: boolean
  reason?: string
  className?: string
}

export function PermissionGate({ allowed, reason, className, children }: PermissionGateProps) {
  return (
    <div
      className={clsx('relative', !allowed && 'cursor-not-allowed opacity-60 grayscale-[0.15]', className)}
      aria-disabled={!allowed}
      title={!allowed ? reason : undefined}
    >
      {children}
      {!allowed ? (
        <span className="pointer-events-none absolute inset-0 rounded-xl border border-dashed border-cloth-line/80 bg-cloth-panel/20" />
      ) : null}
    </div>
  )
}

interface PermissionButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  allowed: boolean
  reason?: string
}

export function PermissionButton({ allowed, reason, className, children, disabled, ...props }: PermissionButtonProps) {
  const finalDisabled = disabled || !allowed

  return (
    <button
      {...props}
      disabled={finalDisabled}
      title={!allowed ? reason : props.title}
      className={clsx('fabric-btn', className)}
      aria-disabled={finalDisabled}
    >
      {children}
    </button>
  )
}

import { useMutation, useQuery } from '@tanstack/react-query'
import { FormEvent, useState } from 'react'
import { Link, Navigate, useNavigate } from 'react-router-dom'
import { apiClient, ApiError } from '@/lib/api-client'
import { settingsApi } from '@/lib/settings-api'
import { useAuthStore } from '@/stores/auth-store'

interface FieldErrors {
  username?: string
  email?: string
  password?: string
}

function validateRegisterForm(username: string, email: string, password: string): FieldErrors {
  const errors: FieldErrors = {}
  const trimmedUsername = username.trim()
  const trimmedEmail = email.trim()

  if (!trimmedUsername) {
    errors.username = '请输入用户名。'
  } else if (trimmedUsername.length < 3) {
    errors.username = '用户名至少 3 个字符。'
  } else if (trimmedUsername.length > 50) {
    errors.username = '用户名不能超过 50 个字符。'
  }

  if (!trimmedEmail) {
    errors.email = '请输入邮箱地址。'
  } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(trimmedEmail)) {
    errors.email = '请输入有效的邮箱地址。'
  }

  if (!password) {
    errors.password = '请输入密码。'
  } else if (password.length < 8) {
    errors.password = '密码至少 8 个字符。'
  } else if (password.length > 255) {
    errors.password = '密码不能超过 255 个字符。'
  }

  return errors
}

export function RegisterPage() {
  const navigate = useNavigate()
  const user = useAuthStore((state) => state.user)
  const setSession = useAuthStore((state) => state.setSession)
  const [username, setUsername] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({})

  const systemQuery = useQuery({
    queryKey: ['public-register-system-settings'],
    queryFn: () => settingsApi.getSystemSettings(),
    retry: false,
  })

  const registerMutation = useMutation({
    mutationFn: async () => {
      const result = await apiClient.auth.register({ username: username.trim(), email: email.trim(), password })
      setSession(result.tokens, result.user)
      return result
    },
    onSuccess: () => {
      navigate('/notes/overview', { replace: true })
    },
  })

  if (user) {
    return <Navigate to="/notes/overview" replace />
  }

  const allowRegistration = systemQuery.data?.allow_registration === true

  const onSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (!allowRegistration) return

    const errors = validateRegisterForm(username, email, password)
    setFieldErrors(errors)
    if (Object.keys(errors).length > 0) return

    registerMutation.mutate()
  }

  const backendError = registerMutation.error instanceof ApiError ? registerMutation.error.message : null

  return (
    <div className="flex min-h-screen items-center justify-center p-4 md:p-6">
      <section className="fabric-panel fabric-panel-stitched w-full max-w-lg p-6 lg:p-8">
        <div>
          <p className="text-xs uppercase tracking-[0.24em] text-cloth-accent">Register</p>
          <h1 className="mt-2 font-serif text-3xl text-cloth-ink">创建账户</h1>
          <p className="mt-2 text-sm text-cloth-muted">填写必要信息后即可注册。</p>
        </div>

        {!allowRegistration ? (
          <div className="mt-5 rounded-xl border border-cloth-line/80 bg-white/50 px-4 py-3 text-sm text-cloth-muted">
            当前未开放注册。
          </div>
        ) : null}

        <form onSubmit={onSubmit} className="mt-5 space-y-4" noValidate>
          <label className="block space-y-2">
            <span className="text-sm font-medium text-cloth-ink">用户名</span>
            <input
              className="fabric-input"
              value={username}
              onChange={(e) => {
                setUsername(e.target.value)
                if (fieldErrors.username) setFieldErrors((current) => ({ ...current, username: undefined }))
              }}
              disabled={!allowRegistration}
              aria-invalid={fieldErrors.username ? 'true' : 'false'}
              aria-describedby={fieldErrors.username ? 'register-username-error' : undefined}
            />
            {fieldErrors.username ? <p id="register-username-error" className="text-sm text-cloth-danger">{fieldErrors.username}</p> : null}
          </label>

          <label className="block space-y-2">
            <span className="text-sm font-medium text-cloth-ink">邮箱</span>
            <input
              className="fabric-input"
              type="email"
              value={email}
              onChange={(e) => {
                setEmail(e.target.value)
                if (fieldErrors.email) setFieldErrors((current) => ({ ...current, email: undefined }))
              }}
              disabled={!allowRegistration}
              aria-invalid={fieldErrors.email ? 'true' : 'false'}
              aria-describedby={fieldErrors.email ? 'register-email-error' : undefined}
            />
            {fieldErrors.email ? <p id="register-email-error" className="text-sm text-cloth-danger">{fieldErrors.email}</p> : null}
          </label>

          <label className="block space-y-2">
            <span className="text-sm font-medium text-cloth-ink">密码</span>
            <input
              className="fabric-input"
              type="password"
              value={password}
              onChange={(e) => {
                setPassword(e.target.value)
                if (fieldErrors.password) setFieldErrors((current) => ({ ...current, password: undefined }))
              }}
              disabled={!allowRegistration}
              aria-invalid={fieldErrors.password ? 'true' : 'false'}
              aria-describedby={fieldErrors.password ? 'register-password-error' : undefined}
            />
            {fieldErrors.password ? <p id="register-password-error" className="text-sm text-cloth-danger">{fieldErrors.password}</p> : null}
          </label>

          {backendError ? (
            <div className="rounded-xl border border-cloth-danger/40 bg-red-50/60 px-4 py-3 text-sm text-cloth-danger">
              {backendError}
            </div>
          ) : null}

          <button
            type="submit"
            className="fabric-btn fabric-btn-primary w-full"
            disabled={!allowRegistration || registerMutation.isPending}
          >
            {registerMutation.isPending ? '注册中…' : '注册并进入系统'}
          </button>
        </form>

        <div className="mt-5 text-center text-sm text-cloth-muted">
          已有账户？{' '}
          <Link to="/login" className="font-medium text-cloth-accent hover:underline">
            返回登录
          </Link>
        </div>
      </section>
    </div>
  )
}

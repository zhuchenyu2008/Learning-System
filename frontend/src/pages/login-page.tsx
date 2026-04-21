import { useMutation, useQuery } from '@tanstack/react-query'
import { FormEvent, useState } from 'react'
import { Link, Navigate, useLocation, useNavigate } from 'react-router-dom'
import { apiClient, ApiError } from '@/lib/api-client'
import { settingsApi } from '@/lib/settings-api'
import { useAuthStore } from '@/stores/auth-store'

export function LoginPage() {
  const navigate = useNavigate()
  const location = useLocation()
  const user = useAuthStore((state) => state.user)
  const setSession = useAuthStore((state) => state.setSession)
  const [username, setUsername] = useState('admin')
  const [password, setPassword] = useState('ChangeMe123!')

  const systemQuery = useQuery({
    queryKey: ['public-login-system-settings'],
    queryFn: () => settingsApi.getSystemSettings(),
    retry: false,
  })

  const loginMutation = useMutation({
    mutationFn: async () => {
      const tokens = await apiClient.auth.login({ username, password })
      const me = await apiClient.auth.me(tokens.accessToken)
      setSession(tokens, me)
      return me
    },
    onSuccess: () => {
      const target = (location.state as { from?: string } | null)?.from ?? '/notes/overview'
      navigate(target, { replace: true })
    },
  })

  if (user) {
    return <Navigate to="/notes/overview" replace />
  }

  const onSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    loginMutation.mutate()
  }

  const allowRegistration = systemQuery.data?.allow_registration === true

  return (
    <div className="flex min-h-screen items-center justify-center p-4 md:p-6">
      <div className="grid w-full max-w-6xl gap-4 lg:grid-cols-[1.05fr_0.95fr] lg:gap-6">
        <section className="fabric-panel flex min-h-[320px] flex-col justify-between p-6 lg:min-h-[560px] lg:p-10">
          <div>
            <p className="text-xs uppercase tracking-[0.28em] text-cloth-accent">learning-system</p>
            <h1 className="mt-4 max-w-2xl font-serif text-3xl leading-tight text-cloth-ink md:text-4xl lg:text-5xl">
              把笔记、复习与本地资料整理到同一个学习工作台。
            </h1>
            <p className="mt-4 max-w-xl text-sm text-cloth-muted md:text-base">
              统一管理笔记生成、复习流程与系统配置。
            </p>
          </div>

          <div className="grid gap-3 md:grid-cols-3">
            {[
              ['笔记', '生成与整理学习笔记。'],
              ['复习', '查看待复习内容并完成复习。'],
              ['设置', '管理 AI、工作区与系统参数。'],
            ].map(([title, text]) => (
              <article key={title} className="rounded-2xl border border-cloth-line/80 bg-white/45 p-4">
                <p className="text-sm font-semibold text-cloth-ink">{title}</p>
                <p className="mt-2 text-sm text-cloth-muted">{text}</p>
              </article>
            ))}
          </div>
        </section>

        <section className="fabric-panel flex min-h-[420px] items-center justify-center p-6 lg:min-h-[560px] lg:p-10">
          <form onSubmit={onSubmit} className="w-full max-w-md space-y-5">
            <div>
              <p className="text-xs uppercase tracking-[0.24em] text-cloth-accent">Sign in</p>
              <h2 className="mt-2 font-serif text-3xl text-cloth-ink">登录系统</h2>
            </div>

            <div className="space-y-4">
              <label className="block space-y-2">
                <span className="text-sm font-medium text-cloth-ink">用户名</span>
                <input className="fabric-input" value={username} onChange={(e) => setUsername(e.target.value)} />
              </label>

              <label className="block space-y-2">
                <span className="text-sm font-medium text-cloth-ink">密码</span>
                <input
                  className="fabric-input"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                />
              </label>
            </div>

            {loginMutation.error ? (
              <div className="rounded-xl border border-cloth-danger/40 bg-red-50/60 px-4 py-3 text-sm text-cloth-danger">
                {loginMutation.error instanceof ApiError
                  ? loginMutation.error.message
                  : '登录失败，请检查用户名或密码。'}
              </div>
            ) : null}

            <button type="submit" className="fabric-btn fabric-btn-primary w-full" disabled={loginMutation.isPending}>
              {loginMutation.isPending ? '登录中…' : '进入系统'}
            </button>

            {allowRegistration ? (
              <div className="text-center text-sm text-cloth-muted">
                还没有账户？{' '}
                <Link to="/register" className="font-medium text-cloth-accent hover:underline">
                  立即注册
                </Link>
              </div>
            ) : null}
          </form>
        </section>
      </div>
    </div>
  )
}

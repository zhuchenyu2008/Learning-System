import { useMutation } from '@tanstack/react-query'
import { FormEvent, useState } from 'react'
import { Navigate, useLocation, useNavigate } from 'react-router-dom'
import { apiClient, ApiError } from '@/lib/api-client'
import { useAuthStore } from '@/stores/auth-store'

export function LoginPage() {
  const navigate = useNavigate()
  const location = useLocation()
  const user = useAuthStore((state) => state.user)
  const setSession = useAuthStore((state) => state.setSession)
  const [username, setUsername] = useState('admin')
  const [password, setPassword] = useState('ChangeMe123!')

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

  return (
    <div className="flex min-h-screen items-center justify-center p-6">
      <div className="grid w-full max-w-6xl gap-6 lg:grid-cols-[1.1fr_0.9fr]">
        <section className="fabric-panel flex min-h-[560px] flex-col justify-between p-8 lg:p-10">
          <div>
            <p className="text-xs uppercase tracking-[0.28em] text-cloth-accent">learning-system</p>
            <h1 className="mt-4 max-w-2xl font-serif text-5xl leading-tight text-cloth-ink">
              把笔记、复习与本地文件夹工作流，织成一张可追溯的学习布面。
            </h1>
            <p className="mt-5 max-w-xl text-base text-cloth-muted">
              SA-04 交付前端基础壳层：登录入口、路由守卫、三级侧边栏、角色禁用态和织物质感主题系统。
            </p>
          </div>

          <div className="grid gap-4 md:grid-cols-3">
            {[
              ['本地文件夹优先', 'Markdown 与原始资料保留为事实源之一。'],
              ['角色安全默认开启', '管理员可写，普通用户以只读/复习操作为主。'],
              ['API 优先壳层', '所有业务深逻辑留给后续模块与后端实现。'],
            ].map(([title, text]) => (
              <article key={title} className="rounded-2xl border border-cloth-line/80 bg-white/45 p-4">
                <p className="text-sm font-semibold text-cloth-ink">{title}</p>
                <p className="mt-2 text-sm text-cloth-muted">{text}</p>
              </article>
            ))}
          </div>
        </section>

        <section className="fabric-panel flex min-h-[560px] items-center justify-center p-8 lg:p-10">
          <form onSubmit={onSubmit} className="w-full max-w-md space-y-5">
            <div>
              <p className="text-xs uppercase tracking-[0.24em] text-cloth-accent">Sign in</p>
              <h2 className="mt-2 font-serif text-3xl text-cloth-ink">登录系统</h2>
              <p className="mt-2 text-sm text-cloth-muted">默认指向 `/api/v1`。后端尚未完全落地时，可先用于前端壳层演示。</p>
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
                  : '登录失败，请检查后端接口与凭据。'}
              </div>
            ) : null}

            <button type="submit" className="fabric-btn fabric-btn-primary w-full" disabled={loginMutation.isPending}>
              {loginMutation.isPending ? '登录中…' : '进入 learning-system'}
            </button>

            <div className="rounded-2xl border border-dashed border-cloth-line/90 bg-white/35 p-4 text-sm text-cloth-muted">
              <p>路由守卫策略：</p>
              <ul className="mt-2 list-disc space-y-1 pl-5">
                <li>未登录：跳转登录页。</li>
                <li>已登录：admin 与 viewer 均可进入壳层。</li>
                <li>viewer 在管理页面中看到灰态禁用，不隐藏结构。</li>
              </ul>
            </div>
          </form>
        </section>
      </div>
    </div>
  )
}

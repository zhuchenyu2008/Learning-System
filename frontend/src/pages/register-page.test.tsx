import { describe, expect, it, vi } from 'vitest'
import { fireEvent, screen, waitFor } from '@testing-library/react'
import { RegisterPage } from '@/pages/register-page'
import { apiClient } from '@/lib/api-client'
import { settingsApi } from '@/lib/settings-api'
import { renderWithProviders } from '@/test/test-utils'
import { sampleSystemSettings } from '@/test/fixtures'

vi.mock('@/lib/api-client', async () => {
  const actual = await vi.importActual<typeof import('@/lib/api-client')>('@/lib/api-client')
  return {
    ...actual,
    apiClient: {
      ...actual.apiClient,
      auth: {
        login: vi.fn(),
        register: vi.fn(),
        me: vi.fn(),
        logout: vi.fn(),
        refresh: vi.fn(),
      },
    },
  }
})

vi.mock('@/lib/settings-api', () => ({
  settingsApi: {
    getSystemSettings: vi.fn(),
  },
}))

describe('RegisterPage', () => {
  it('disables registration when allow_registration=false', async () => {
    vi.mocked(settingsApi.getSystemSettings).mockResolvedValue(sampleSystemSettings)

    renderWithProviders(<RegisterPage />, { route: '/register' })

    await waitFor(() => {
      expect(screen.getByText('当前未开放注册。')).toBeInTheDocument()
    })
    expect(screen.getByRole('button', { name: '注册并进入系统' })).toBeDisabled()
  })

  it('shows field-level validation errors before submitting', async () => {
    vi.mocked(settingsApi.getSystemSettings).mockResolvedValue({ ...sampleSystemSettings, allow_registration: true })

    renderWithProviders(<RegisterPage />, { route: '/register' })

    const submit = await screen.findByRole('button', { name: '注册并进入系统' })
    await waitFor(() => {
      expect(submit).toBeEnabled()
    })
    fireEvent.click(submit)

    expect(await screen.findByText('请输入用户名。')).toBeInTheDocument()
    expect(screen.getByText('请输入邮箱地址。')).toBeInTheDocument()
    expect(screen.getByText('请输入密码。')).toBeInTheDocument()
    expect(apiClient.auth.register).not.toHaveBeenCalled()
  })

  it('submits registration when allow_registration=true', async () => {
    vi.mocked(settingsApi.getSystemSettings).mockResolvedValue({ ...sampleSystemSettings, allow_registration: true })
    vi.mocked(apiClient.auth.register).mockResolvedValue({
      user: { id: 2, username: 'new-user', role: 'viewer', isActive: true, lastLoginAt: null },
      tokens: { accessToken: 'access', refreshToken: 'refresh' },
    })

    renderWithProviders(<RegisterPage />, { route: '/register' })

    fireEvent.change(await screen.findByLabelText('用户名'), { target: { value: 'new-user' } })
    fireEvent.change(screen.getByLabelText('邮箱'), { target: { value: 'new@example.com' } })
    fireEvent.change(screen.getByLabelText('密码'), { target: { value: 'ChangeMe123!' } })
    fireEvent.click(screen.getByRole('button', { name: '注册并进入系统' }))

    await waitFor(() => {
      expect(apiClient.auth.register).toHaveBeenCalledWith({
        username: 'new-user',
        email: 'new@example.com',
        password: 'ChangeMe123!',
      })
    })
  })

  it('links back to login', async () => {
    vi.mocked(settingsApi.getSystemSettings).mockResolvedValue({ ...sampleSystemSettings, allow_registration: true })

    renderWithProviders(<RegisterPage />, { route: '/register' })

    expect(await screen.findByRole('link', { name: '返回登录' })).toHaveAttribute('href', '/login')
  })
})

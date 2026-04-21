import { describe, expect, it, vi } from 'vitest'
import { fireEvent, screen, waitFor } from '@testing-library/react'
import { LoginPage } from '@/pages/login-page'
import { apiClient, ApiError } from '@/lib/api-client'
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

describe('LoginPage', () => {
  it('renders fields and submits successfully', async () => {
    vi.mocked(settingsApi.getSystemSettings).mockResolvedValue(sampleSystemSettings)
    vi.mocked(apiClient.auth.login).mockResolvedValue({ accessToken: 'access', refreshToken: 'refresh' })
    vi.mocked(apiClient.auth.me).mockResolvedValue({ id: 1, username: 'admin', role: 'admin', isActive: true, lastLoginAt: null })

    renderWithProviders(<LoginPage />, { route: '/login' })

    expect(screen.getByText('登录系统')).toBeInTheDocument()
    expect(screen.getByText('进入系统')).toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: '进入系统' }))

    await waitFor(() => {
      expect(apiClient.auth.login).toHaveBeenCalledWith({ username: 'admin', password: 'ChangeMe123!' })
    })
    expect(apiClient.auth.me).toHaveBeenCalledWith('access')
  })

  it('shows backend errors on failed login', async () => {
    vi.mocked(settingsApi.getSystemSettings).mockResolvedValue(sampleSystemSettings)
    vi.mocked(apiClient.auth.login).mockRejectedValue(new ApiError('invalid credentials', 401))

    renderWithProviders(<LoginPage />, { route: '/login' })

    fireEvent.click(screen.getByRole('button', { name: '进入系统' }))

    await waitFor(() => {
      expect(screen.getByText('invalid credentials')).toBeInTheDocument()
    })
  })

  it('shows register entry when allow_registration=true', async () => {
    vi.mocked(settingsApi.getSystemSettings).mockResolvedValue({ ...sampleSystemSettings, allow_registration: true })

    renderWithProviders(<LoginPage />, { route: '/login' })

    await waitFor(() => {
      expect(screen.getByRole('link', { name: '立即注册' })).toBeInTheDocument()
    })
  })
})

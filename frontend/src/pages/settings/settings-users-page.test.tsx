import { describe, expect, it, vi } from 'vitest'
import { fireEvent, screen, waitFor } from '@testing-library/react'
import { SettingsUsersPage } from '@/pages/settings/settings-users-page'
import { settingsApi } from '@/lib/settings-api'
import { sampleAdminUsers, sampleLoginEvents, sampleUserActivity } from '@/test/fixtures'
import { createUser, renderWithProviders } from '@/test/test-utils'

vi.mock('@/lib/settings-api', () => ({
  settingsApi: {
    listUsers: vi.fn(),
    listUserActivity: vi.fn(),
    listLoginEvents: vi.fn(),
  },
}))

describe('SettingsUsersPage', () => {
  it('disables refresh for viewer role', async () => {
    renderWithProviders(<SettingsUsersPage />, { user: createUser({ role: 'viewer' }) })

    expect(screen.getByText('普通用户可查看后台信息结构，但用户管理与审计能力保持禁用。')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: '刷新列表' })).toBeDisabled()
  })

  it('renders admin data and refreshes all sections', async () => {
    vi.mocked(settingsApi.listUsers).mockResolvedValue(sampleAdminUsers)
    vi.mocked(settingsApi.listUserActivity).mockResolvedValue(sampleUserActivity)
    vi.mocked(settingsApi.listLoginEvents).mockResolvedValue(sampleLoginEvents)

    renderWithProviders(<SettingsUsersPage />, { user: createUser({ role: 'admin' }) })

    expect(await screen.findByText('admin@example.com')).toBeInTheDocument()
    expect(screen.getByText('viewer-a')).toBeInTheDocument()
    expect(screen.getByText('IP：127.0.0.1')).toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: '刷新列表' }))

    await waitFor(() => {
      expect(settingsApi.listUsers).toHaveBeenCalledTimes(2)
      expect(settingsApi.listUserActivity).toHaveBeenCalledTimes(2)
      expect(settingsApi.listLoginEvents).toHaveBeenCalledTimes(2)
    })
  })
})

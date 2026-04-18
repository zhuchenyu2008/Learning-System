import { describe, expect, it, vi } from 'vitest'
import { fireEvent, screen, waitFor } from '@testing-library/react'
import { SettingsWorkspacePage } from '@/pages/settings/settings-workspace-page'
import { settingsApi } from '@/lib/settings-api'
import { sampleSystemSettings } from '@/test/fixtures'
import { createUser, renderWithProviders } from '@/test/test-utils'

vi.mock('@/lib/settings-api', () => ({
  settingsApi: {
    getSystemSettings: vi.fn(),
    getObsidianSettings: vi.fn(),
    updateSystemSettings: vi.fn(),
    updateObsidianSettings: vi.fn(),
    triggerObsidianSync: vi.fn(),
  },
}))

describe('SettingsWorkspacePage', () => {
  it('shows readonly notice and disabled actions for viewer', () => {
    renderWithProviders(<SettingsWorkspacePage />, { user: createUser({ role: 'viewer' }) })

    expect(screen.getByText('普通用户可查看工作区与同步结构，但所有写操作均为禁用态。')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: '保存系统设置' })).toBeDisabled()
    expect(screen.getByRole('button', { name: '保存 Obsidian 配置' })).toBeDisabled()
    expect(screen.getByRole('button', { name: '立即同步' })).toBeDisabled()
  })

  it('lets admin save settings and trigger sync', async () => {
    vi.mocked(settingsApi.getSystemSettings).mockResolvedValue(sampleSystemSettings)
    vi.mocked(settingsApi.getObsidianSettings).mockResolvedValue({
      enabled: true,
      vault_path: '/vault',
      vault_name: 'Learning Vault',
      vault_id: 'vault-1',
      obsidian_headless_path: '/usr/bin/obsidian-headless',
      config_dir: '/config',
      device_name: 'device-a',
      sync_command: 'ob sync',
    })
    vi.mocked(settingsApi.updateSystemSettings).mockResolvedValue(sampleSystemSettings)
    vi.mocked(settingsApi.updateObsidianSettings).mockResolvedValue({
      enabled: true,
      vault_path: '/vault',
      vault_name: 'Learning Vault',
      vault_id: 'vault-1',
      obsidian_headless_path: '/usr/bin/obsidian-headless',
      config_dir: '/config',
      device_name: 'device-a',
      sync_command: 'ob sync',
    })
    vi.mocked(settingsApi.triggerObsidianSync).mockResolvedValue({ ok: true })

    renderWithProviders(<SettingsWorkspacePage />, { user: createUser({ role: 'admin' }) })

    expect(await screen.findByDisplayValue('/data/workspace')).toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: '保存系统设置' }))
    await waitFor(() => {
      expect(settingsApi.updateSystemSettings).toHaveBeenCalled()
    })

    fireEvent.click(screen.getByRole('button', { name: '保存 Obsidian 配置' }))
    await waitFor(() => {
      expect(settingsApi.updateObsidianSettings).toHaveBeenCalled()
    })

    fireEvent.click(screen.getByRole('button', { name: '立即同步' }))
    await waitFor(() => {
      expect(settingsApi.triggerObsidianSync).toHaveBeenCalled()
    })
  })
})

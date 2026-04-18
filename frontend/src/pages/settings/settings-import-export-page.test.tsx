import { describe, expect, it, vi } from 'vitest'
import { fireEvent, screen, waitFor } from '@testing-library/react'
import { SettingsImportExportPage } from '@/pages/settings/settings-import-export-page'
import { settingsApi } from '@/lib/settings-api'
import { createUser, renderWithProviders } from '@/test/test-utils'

vi.mock('@/lib/settings-api', () => ({
  settingsApi: {
    exportDatabase: vi.fn(),
    importDatabase: vi.fn(),
  },
}))

describe('SettingsImportExportPage', () => {
  it('keeps import/export buttons disabled for viewer', () => {
    renderWithProviders(<SettingsImportExportPage />, { user: createUser({ role: 'viewer' }) })

    expect(screen.getByText('普通用户仅可查看导入导出说明与表单结构，导入/导出操作保持禁用。')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: '导出数据库' })).toBeDisabled()
    expect(screen.getByRole('button', { name: '导入数据库' })).toBeDisabled()
  })

  it('allows admin to export and import database snapshots', async () => {
    vi.mocked(settingsApi.exportDatabase).mockResolvedValue({ path: '/tmp/export.zip' })
    vi.mocked(settingsApi.importDatabase).mockResolvedValue({ message: 'import queued' })

    renderWithProviders(<SettingsImportExportPage />, { user: createUser({ role: 'admin' }) })

    fireEvent.click(screen.getByRole('button', { name: '导出数据库' }))

    await waitFor(() => {
      expect(settingsApi.exportDatabase).toHaveBeenCalled()
    })
    expect(await screen.findByText('/tmp/export.zip')).toBeInTheDocument()

    const file = new File(['dump'], 'db.zip', { type: 'application/zip' })
    const input = screen.getByLabelText('导入文件') as HTMLInputElement
    fireEvent.change(input, { target: { files: [file] } })
    fireEvent.click(screen.getByRole('button', { name: '导入数据库' }))

    await waitFor(() => {
      expect(settingsApi.importDatabase).toHaveBeenCalled()
    })
    expect(await screen.findByText('import queued')).toBeInTheDocument()
  })
})

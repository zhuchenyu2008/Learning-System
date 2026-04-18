import { describe, expect, it, vi } from 'vitest'
import { fireEvent, screen, waitFor } from '@testing-library/react'
import { SettingsJobsPage } from '@/pages/settings/settings-jobs-page'
import { settingsApi } from '@/lib/settings-api'
import { sampleJobs, sampleSchedulerTasks, sampleSystemSettings } from '@/test/fixtures'
import { createUser, renderWithProviders } from '@/test/test-utils'

vi.mock('@/lib/settings-api', () => ({
  settingsApi: {
    listSchedulerTasks: vi.fn(),
    listJobs: vi.fn(),
    getSystemSettings: vi.fn(),
  },
}))

describe('SettingsJobsPage', () => {
  it('shows readonly disabled state for viewer', () => {
    renderWithProviders(<SettingsJobsPage />, { user: createUser({ role: 'viewer' }) })

    expect(screen.getByText('普通用户仅可查看任务和调度信息，不可修改任何调度策略。')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: '刷新任务状态' })).toBeDisabled()
  })

  it('renders scheduler and job details for admin and refreshes data', async () => {
    vi.mocked(settingsApi.listSchedulerTasks).mockResolvedValue(sampleSchedulerTasks)
    vi.mocked(settingsApi.listJobs).mockResolvedValue(sampleJobs)
    vi.mocked(settingsApi.getSystemSettings).mockResolvedValue(sampleSystemSettings)

    renderWithProviders(<SettingsJobsPage />, { user: createUser({ role: 'admin' }) })

    expect(await screen.findByText('review-maintenance')).toBeInTheDocument()
    expect(screen.getByText('#301 · note_generation')).toBeInTheDocument()
    expect(screen.getByText('task celery-301')).toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: '刷新任务状态' }))

    await waitFor(() => {
      expect(settingsApi.listSchedulerTasks).toHaveBeenCalledTimes(2)
      expect(settingsApi.listJobs).toHaveBeenCalledTimes(2)
      expect(settingsApi.getSystemSettings).toHaveBeenCalledTimes(2)
    })
  })
})

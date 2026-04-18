import { describe, expect, it, vi } from 'vitest'
import { fireEvent, screen, waitFor, within } from '@testing-library/react'
import { SettingsAiPage } from '@/pages/settings/settings-ai-page'
import { settingsApi } from '@/lib/settings-api'
import { sampleAiSettings } from '@/test/fixtures'
import { createUser, renderWithProviders } from '@/test/test-utils'

vi.mock('@/lib/settings-api', () => ({
  settingsApi: {
    getAiSettings: vi.fn(),
    updateAiSettings: vi.fn(),
    testProvider: vi.fn(),
  },
}))

describe('SettingsAiPage', () => {
  it('shows viewer readonly state and disables save action', async () => {
    renderWithProviders(<SettingsAiPage />, { user: createUser({ role: 'viewer' }) })

    expect(screen.getByText('普通用户可查看配置结构，但所有管理操作保持禁用态。')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: '保存 AI 配置' })).toBeDisabled()
  })

  it('loads admin provider config and supports save/test actions', async () => {
    vi.mocked(settingsApi.getAiSettings).mockResolvedValue(sampleAiSettings)
    vi.mocked(settingsApi.updateAiSettings).mockResolvedValue(sampleAiSettings)
    vi.mocked(settingsApi.testProvider).mockResolvedValue({ status: 'ok', message: 'provider healthy' })

    renderWithProviders(<SettingsAiPage />, { user: createUser({ role: 'admin' }) })

    expect(await screen.findByDisplayValue('https://api.example.com/v1')).toBeInTheDocument()

    const llmHeading = screen.getByRole('heading', { name: 'LLM' })
    const llmSection = llmHeading.closest('section')
    if (!llmSection) throw new Error('LLM section not found')

    fireEvent.click(within(llmSection).getByRole('button', { name: '测试连接' }))
    await waitFor(() => {
      expect(settingsApi.testProvider).toHaveBeenCalledWith({
        provider_type: 'llm',
        base_url: 'https://api.example.com/v1',
        api_key: 'secret',
        model_name: 'gpt-4o-mini',
      })
    })

    fireEvent.click(screen.getByRole('button', { name: '保存 AI 配置' }))
    await waitFor(() => {
      expect(settingsApi.updateAiSettings).toHaveBeenCalledWith(expect.objectContaining({ providers: expect.any(Array) }))
    })
    expect(await screen.findByText('AI 配置已提交。')).toBeInTheDocument()
  })
})

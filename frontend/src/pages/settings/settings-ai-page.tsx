import { useMutation, useQuery } from '@tanstack/react-query'
import { useEffect, useState } from 'react'
import { ApiError } from '@/lib/api-client'
import { settingsApi } from '@/lib/settings-api'
import { PermissionButton, PermissionGate } from '@/components/permission-gate'
import { PagePlaceholder } from '@/components/page-placeholder'
import { EmptyStateCard, ReadonlyNotice, SectionStatus, SettingsField, SettingsSection } from '@/components/settings-section'
import { useAuthStore } from '@/stores/auth-store'
import type { ProviderConfig, ProviderType, SettingsAiPayload } from '@/types/settings'

const providerLabels: Record<ProviderType, string> = {
  llm: 'LLM',
  embedding: 'Embedding',
  stt: 'STT / 语音转文字',
  ocr: 'OCR / 多模态',
}

const defaultProviders: ProviderConfig[] = [
  { provider_type: 'llm', base_url: '', api_key: '', api_key_masked: '', has_api_key: false, model_name: '', extra_json: '', is_enabled: false },
  { provider_type: 'embedding', base_url: '', api_key: '', api_key_masked: '', has_api_key: false, model_name: '', extra_json: '', is_enabled: false },
  { provider_type: 'stt', base_url: '', api_key: '', api_key_masked: '', has_api_key: false, model_name: '', extra_json: '', is_enabled: false },
  { provider_type: 'ocr', base_url: '', api_key: '', api_key_masked: '', has_api_key: false, model_name: '', extra_json: '', is_enabled: false },
]

function normalizeProviders(payload: SettingsAiPayload | null | undefined) {
  const current = payload?.providers ?? []
  return defaultProviders.map((fallback) => {
    const matched = current.find((item) => item.provider_type === fallback.provider_type)
    if (!matched) return fallback
    return {
      ...fallback,
      ...matched,
      api_key: '',
      api_key_masked: matched.api_key_masked ?? '',
      has_api_key: matched.has_api_key ?? Boolean(matched.api_key_masked),
    }
  })
}

export function SettingsAiPage() {
  const isAdmin = useAuthStore((state) => state.user?.role === 'admin')
  const [providers, setProviders] = useState<ProviderConfig[]>(defaultProviders)
  const [message, setMessage] = useState<string | null>(null)
  const [messageTone, setMessageTone] = useState<'default' | 'success' | 'warning' | 'danger'>('default')
  const [testingType, setTestingType] = useState<ProviderType | null>(null)

  const aiQuery = useQuery({
    queryKey: ['settings', 'ai'],
    queryFn: () => settingsApi.getAiSettings(),
    enabled: isAdmin,
  })

  useEffect(() => {
    if (aiQuery.data) {
      setProviders(normalizeProviders(aiQuery.data))
    }
  }, [aiQuery.data])

  const saveMutation = useMutation({
    mutationFn: (payload: SettingsAiPayload) => settingsApi.updateAiSettings(payload),
    onSuccess: () => {
      setMessage('AI 配置已提交。')
      setMessageTone('success')
    },
    onError: (error) => {
      setMessage(error instanceof ApiError ? error.message : 'AI 配置保存失败。')
      setMessageTone('danger')
    },
  })

  const testMutation = useMutation({
    mutationFn: async (provider: ProviderConfig) => {
      setTestingType(provider.provider_type)
      return settingsApi.testProvider({
        provider_type: provider.provider_type,
        base_url: provider.base_url,
        api_key: provider.api_key,
        model_name: provider.model_name,
      })
    },
    onSuccess: (result) => {
      setMessage(result.message || '测试请求已完成。')
      setMessageTone(result.status === 'ok' ? 'success' : 'warning')
    },
    onError: (error) => {
      setMessage(error instanceof ApiError ? error.message : '测试连接失败。')
      setMessageTone('danger')
    },
    onSettled: () => {
      setTestingType(null)
    },
  })

  const backendUnavailable = isAdmin && aiQuery.data == null && !aiQuery.isLoading && !aiQuery.error

  const updateProvider = (type: ProviderType, patch: Partial<ProviderConfig>) => {
    setProviders((current) => current.map((item) => (item.provider_type === type ? { ...item, ...patch } : item)))
  }

  return (
    <PagePlaceholder
      title="AI 配置"
      description="配置 LLM、Embedding、STT、OCR 四类 OpenAI 兼容 Provider。后端未实现时保留结构化表单与失败可见状态，不伪造保存成功。"
      className="space-y-4"
      actions={
        <>
          <SectionStatus
            status={backendUnavailable ? '后端设置接口未就绪' : '配置表单已接入'}
            tone={backendUnavailable ? 'warning' : 'success'}
          />
          <PermissionButton
            allowed={isAdmin}
            reason="仅管理员可保存 AI 配置"
            className="fabric-btn-primary"
            onClick={() => saveMutation.mutate({ providers })}
            disabled={saveMutation.isPending}
          >
            {saveMutation.isPending ? '保存中…' : '保存 AI 配置'}
          </PermissionButton>
        </>
      }
    >
      <ReadonlyNotice isAdmin={isAdmin} reason="普通用户可查看配置结构，但所有管理操作保持禁用态。" />

      {message ? <div className="md:col-span-2 xl:col-span-3"><SectionStatus status={message} tone={messageTone} /></div> : null}
      {aiQuery.error ? (
        <div className="md:col-span-2 xl:col-span-3 rounded-xl border border-red-200 bg-red-50/80 p-4 text-sm text-red-700">
          {aiQuery.error instanceof ApiError ? aiQuery.error.message : 'AI 配置加载失败。'}
        </div>
      ) : null}

      {providers.map((provider) => (
        <PermissionGate key={provider.provider_type} allowed={isAdmin} reason="仅管理员可修改 AI Provider 配置">
          <SettingsSection
            title={providerLabels[provider.provider_type]}
            description="OpenAI 兼容接口；支持 base URL、模型、密钥与额外 JSON 参数。"
            actions={
              <>
                <label className="fabric-switch-row inline-flex text-sm text-cloth-muted">
                  <span>启用</span>
                  <input
                    type="checkbox"
                    role="switch"
                    className="fabric-switch"
                    checked={provider.is_enabled}
                    disabled={!isAdmin}
                    onChange={(event) => updateProvider(provider.provider_type, { is_enabled: event.target.checked })}
                  />
                </label>
                <PermissionButton
                  allowed={isAdmin}
                  reason="仅管理员可测试 Provider"
                  onClick={() => testMutation.mutate(provider)}
                  disabled={testingType === provider.provider_type}
                >
                  {testingType === provider.provider_type ? '测试中…' : '测试连接'}
                </PermissionButton>
              </>
            }
            className="md:col-span-2 xl:col-span-3"
          >
            <div className="grid gap-4 md:grid-cols-2">
              <SettingsField label="Base URL">
                <input
                  className="fabric-input"
                  value={provider.base_url}
                  onChange={(event) => updateProvider(provider.provider_type, { base_url: event.target.value })}
                  placeholder="https://api.example.com/v1"
                  disabled={!isAdmin}
                />
              </SettingsField>
              <SettingsField label="Model Name">
                <input
                  className="fabric-input"
                  value={provider.model_name}
                  onChange={(event) => updateProvider(provider.provider_type, { model_name: event.target.value })}
                  placeholder="gpt-4o-mini / text-embedding-3-large"
                  disabled={!isAdmin}
                />
              </SettingsField>
              <SettingsField label="API Key" hint={provider.has_api_key ? `已保存密钥：${provider.api_key_masked || '已脱敏'}` : '未设置密钥'}>
                <input
                  className="fabric-input"
                  type="password"
                  value={provider.api_key ?? ''}
                  onChange={(event) => updateProvider(provider.provider_type, { api_key: event.target.value })}
                  placeholder={provider.has_api_key ? '留空则保留现有密钥；输入新值则覆盖' : 'sk-...'}
                  disabled={!isAdmin}
                />
              </SettingsField>
              <SettingsField label="extra_json" hint="填写 JSON 字符串；后端未就绪时仅本地编辑，不会伪造校验通过。">
                <textarea
                  className="fabric-input min-h-28"
                  value={typeof provider.extra_json === 'string' ? provider.extra_json : JSON.stringify(provider.extra_json ?? {}, null, 2)}
                  onChange={(event) => updateProvider(provider.provider_type, { extra_json: event.target.value })}
                  placeholder='{"temperature":0.2}'
                  disabled={!isAdmin}
                />
              </SettingsField>
            </div>
          </SettingsSection>
        </PermissionGate>
      ))}

      {backendUnavailable ? (
        <div className="md:col-span-2 xl:col-span-3">
          <EmptyStateCard title="接口降级提示" description="`/settings/ai` 当前不可用时，页面仍保留完整字段结构与禁用态，但不会显示虚假的后端成功结果。" />
        </div>
      ) : null}
    </PagePlaceholder>
  )
}

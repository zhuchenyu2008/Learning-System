import { useMutation, useQuery } from '@tanstack/react-query'
import { useEffect, useState } from 'react'
import { ApiError } from '@/lib/api-client'
import { settingsApi } from '@/lib/settings-api'
import { PermissionButton, PermissionGate } from '@/components/permission-gate'
import { PagePlaceholder } from '@/components/page-placeholder'
import { EmptyStateCard, ReadonlyNotice, SectionStatus, SettingsField, SettingsSection } from '@/components/settings-section'
import { useAuthStore } from '@/stores/auth-store'
import type { ObsidianSettings, SystemSettings } from '@/types/settings'

const defaultSystemSettings: SystemSettings = {
  allow_registration: false,
  workspace_root: '',
  timezone: 'UTC',
  review_retention_target: '90d',
}

const defaultObsidianSettings: ObsidianSettings = {
  enabled: false,
  vault_path: '',
  vault_name: '',
  vault_id: '',
  obsidian_headless_path: '',
  config_dir: '',
  device_name: '',
  sync_command: 'ob sync',
}

export function SettingsWorkspacePage() {
  const isAdmin = useAuthStore((state) => state.user?.role === 'admin')
  const [systemSettings, setSystemSettings] = useState<SystemSettings>(defaultSystemSettings)
  const [obsidianSettings, setObsidianSettings] = useState<ObsidianSettings>(defaultObsidianSettings)
  const [message, setMessage] = useState<string | null>(null)
  const [messageTone, setMessageTone] = useState<'default' | 'success' | 'warning' | 'danger'>('default')

  const systemQuery = useQuery({ queryKey: ['settings', 'system'], queryFn: () => settingsApi.getSystemSettings(), enabled: isAdmin })
  const obsidianQuery = useQuery({ queryKey: ['settings', 'obsidian'], queryFn: () => settingsApi.getObsidianSettings(), enabled: isAdmin })

  useEffect(() => {
    if (systemQuery.data) {
      setSystemSettings(systemQuery.data)
    }
  }, [systemQuery.data])

  useEffect(() => {
    if (obsidianQuery.data) {
      setObsidianSettings({ ...defaultObsidianSettings, ...obsidianQuery.data })
    }
  }, [obsidianQuery.data])

  const saveSystemMutation = useMutation({
    mutationFn: (payload: SystemSettings) => settingsApi.updateSystemSettings(payload),
    onSuccess: () => {
      setMessage('系统设置已提交。')
      setMessageTone('success')
    },
    onError: (error) => {
      setMessage(error instanceof ApiError ? error.message : '系统设置保存失败。')
      setMessageTone('danger')
    },
  })

  const saveObsidianMutation = useMutation({
    mutationFn: (payload: ObsidianSettings) => settingsApi.updateObsidianSettings(payload),
    onSuccess: () => {
      setMessage('Obsidian 配置已提交。')
      setMessageTone('success')
    },
    onError: (error) => {
      setMessage(error instanceof ApiError ? error.message : 'Obsidian 配置保存失败。')
      setMessageTone('danger')
    },
  })

  const syncMutation = useMutation({
    mutationFn: () => settingsApi.triggerObsidianSync(),
    onSuccess: () => {
      setMessage('已触发 Obsidian 同步任务。')
      setMessageTone('success')
    },
    onError: (error) => {
      setMessage(error instanceof ApiError ? error.message : '同步触发失败。')
      setMessageTone('danger')
    },
  })

  const backendUnavailable = {
    system: isAdmin && systemQuery.data == null && !systemQuery.isLoading && !systemQuery.error,
    obsidian: isAdmin && obsidianQuery.data == null && !obsidianQuery.isLoading && !obsidianQuery.error,
  }

  return (
    <PagePlaceholder
      title="工作区与 Obsidian"
      description="管理员可配置工作目录、注册策略与增强版 Obsidian 同步入口。若后端接口尚未完成，页面仅做安全降级展示。"
      className="space-y-4"
      actions={<SectionStatus status="本地 Vault 直写 + obsidian-headless" tone="success" />}
    >
      <ReadonlyNotice isAdmin={isAdmin} reason="普通用户可查看工作区与同步结构，但所有写操作均为禁用态。" />
      {message ? <div className="md:col-span-2 xl:col-span-3"><SectionStatus status={message} tone={messageTone} /></div> : null}

      <PermissionGate allowed={isAdmin} reason="仅管理员可修改系统设置">
        <SettingsSection
          title="系统设置"
          description="工作区根目录、时区、复习保留目标与注册开关。"
          className="md:col-span-2 xl:col-span-3"
          actions={
            <PermissionButton
              allowed={isAdmin}
              reason="仅管理员可保存系统设置"
              className="fabric-btn-primary"
              onClick={() => saveSystemMutation.mutate(systemSettings)}
              disabled={saveSystemMutation.isPending}
            >
              {saveSystemMutation.isPending ? '保存中…' : '保存系统设置'}
            </PermissionButton>
          }
        >
          <div className="grid gap-4 md:grid-cols-2">
            <SettingsField label="workspace_root" hint="建议直接指向 Markdown / Obsidian Vault 根目录或子目录。">
              <input
                className="fabric-input"
                value={systemSettings.workspace_root}
                onChange={(event) => setSystemSettings((current) => ({ ...current, workspace_root: event.target.value }))}
                placeholder="/data/vaults/my-learning-vault"
                disabled={!isAdmin}
              />
            </SettingsField>
            <SettingsField label="timezone">
              <input
                className="fabric-input"
                value={systemSettings.timezone}
                onChange={(event) => setSystemSettings((current) => ({ ...current, timezone: event.target.value }))}
                placeholder="UTC"
                disabled={!isAdmin}
              />
            </SettingsField>
            <SettingsField label="review_retention_target" hint="例如 30d / 90d / 180d。">
              <input
                className="fabric-input"
                value={systemSettings.review_retention_target}
                onChange={(event) => setSystemSettings((current) => ({ ...current, review_retention_target: event.target.value }))}
                placeholder="90d"
                disabled={!isAdmin}
              />
            </SettingsField>
            <SettingsField label="allow_registration" hint="注册开关属于管理员级策略，普通用户仅可查看。">
              <label className="inline-flex h-11 items-center gap-3 rounded-xl border border-cloth-line bg-white/60 px-3">
                <input
                  type="checkbox"
                  checked={systemSettings.allow_registration}
                  onChange={(event) => setSystemSettings((current) => ({ ...current, allow_registration: event.target.checked }))}
                  disabled={!isAdmin}
                />
                <span className="text-sm text-cloth-ink">允许新用户注册</span>
              </label>
            </SettingsField>
          </div>
          {backendUnavailable.system ? (
            <EmptyStateCard title="系统设置接口未就绪" description="页面字段已齐全，但不会假装完成后端保存。" />
          ) : null}
        </SettingsSection>
      </PermissionGate>

      <PermissionGate allowed={isAdmin} reason="仅管理员可修改 Obsidian 设置与触发同步">
        <SettingsSection
          title="Obsidian 增强同步"
          description="支持本地 Vault 直写，并提供 obsidian-headless 配置入口、Vault 标识与设备名。"
          className="md:col-span-2 xl:col-span-3"
          actions={
            <>
              <label className="inline-flex items-center gap-2 text-sm text-cloth-muted">
                <input
                  type="checkbox"
                  checked={obsidianSettings.enabled}
                  onChange={(event) => setObsidianSettings((current) => ({ ...current, enabled: event.target.checked }))}
                  disabled={!isAdmin}
                />
                启用 Obsidian 增强同步
              </label>
              <PermissionButton
                allowed={isAdmin}
                reason="仅管理员可保存 Obsidian 配置"
                className="fabric-btn-primary"
                onClick={() => saveObsidianMutation.mutate(obsidianSettings)}
                disabled={saveObsidianMutation.isPending}
              >
                {saveObsidianMutation.isPending ? '保存中…' : '保存 Obsidian 配置'}
              </PermissionButton>
              <PermissionButton
                allowed={isAdmin}
                reason="仅管理员可触发同步"
                onClick={() => syncMutation.mutate()}
                disabled={syncMutation.isPending}
              >
                {syncMutation.isPending ? '同步中…' : '立即同步'}
              </PermissionButton>
            </>
          }
        >
          <div className="grid gap-4 md:grid-cols-2">
            <SettingsField label="vault_path">
              <input className="fabric-input" value={obsidianSettings.vault_path} onChange={(event) => setObsidianSettings((current) => ({ ...current, vault_path: event.target.value }))} placeholder="/data/vaults/my-learning-vault" disabled={!isAdmin} />
            </SettingsField>
            <SettingsField label="vault_name / vault_id" hint="支持名称或 ID；取决于后端执行方式。">
              <div className="grid gap-3 md:grid-cols-2">
                <input className="fabric-input" value={obsidianSettings.vault_name} onChange={(event) => setObsidianSettings((current) => ({ ...current, vault_name: event.target.value }))} placeholder="Learning Vault" disabled={!isAdmin} />
                <input className="fabric-input" value={obsidianSettings.vault_id} onChange={(event) => setObsidianSettings((current) => ({ ...current, vault_id: event.target.value }))} placeholder="vault-id" disabled={!isAdmin} />
              </div>
            </SettingsField>
            <SettingsField label="obsidian_headless_path">
              <input className="fabric-input" value={obsidianSettings.obsidian_headless_path} onChange={(event) => setObsidianSettings((current) => ({ ...current, obsidian_headless_path: event.target.value }))} placeholder="/usr/local/bin/obsidian-headless" disabled={!isAdmin} />
            </SettingsField>
            <SettingsField label="config_dir / device_name">
              <div className="grid gap-3 md:grid-cols-2">
                <input className="fabric-input" value={obsidianSettings.config_dir} onChange={(event) => setObsidianSettings((current) => ({ ...current, config_dir: event.target.value }))} placeholder="~/.config/obsidian-headless" disabled={!isAdmin} />
                <input className="fabric-input" value={obsidianSettings.device_name} onChange={(event) => setObsidianSettings((current) => ({ ...current, device_name: event.target.value }))} placeholder="woven-recall-server" disabled={!isAdmin} />
              </div>
            </SettingsField>
            <div className="md:col-span-2">
              <SettingsField label="sync_command" hint="例如 `ob sync`；若后端未实现，仅作展示，不会伪造执行成功。">
                <input className="fabric-input" value={obsidianSettings.sync_command ?? ''} onChange={(event) => setObsidianSettings((current) => ({ ...current, sync_command: event.target.value }))} placeholder="ob sync" disabled={!isAdmin} />
              </SettingsField>
            </div>
          </div>
          {backendUnavailable.obsidian ? (
            <EmptyStateCard title="Obsidian 设置接口未就绪" description="仍展示增强方案所需配置字段：本地 Vault 直写、obsidian-headless 路径、Vault 标识、config dir、device name。" />
          ) : null}
        </SettingsSection>
      </PermissionGate>
    </PagePlaceholder>
  )
}

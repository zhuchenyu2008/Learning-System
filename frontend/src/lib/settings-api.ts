import { apiClient, ApiError, getApiBaseUrl } from '@/lib/api-client'
import { useAuthStore } from '@/stores/auth-store'
import type {
  AdminUserRecord,
  DatabaseExportResult,
  DatabaseImportResult,
  JobRecord,
  LoginEventRecord,
  ObsidianSettings,
  ProviderTestPayload,
  ProviderTestResult,
  SchedulerTaskRecord,
  SettingsAiPayload,
  SystemSettings,
  UserActivityRecord,
} from '@/types/settings'

function getToken() {
  return useAuthStore.getState().accessToken
}

async function safeGet<T>(path: string): Promise<T | null> {
  try {
    return await apiClient.get<T>(path, { token: getToken() })
  } catch (error) {
    if (error instanceof ApiError && (error.status === 404 || error.status === 403 || error.status === 405 || error.status === 501)) {
      return null
    }
    throw error
  }
}

export const settingsApi = {
  getSystemSettings: () => safeGet<SystemSettings>('/settings/system'),
  updateSystemSettings: (payload: SystemSettings) => apiClient.put<SystemSettings>('/settings/system', payload, { token: getToken() }),

  getAiSettings: () => safeGet<SettingsAiPayload>('/settings/ai'),
  updateAiSettings: (payload: SettingsAiPayload) => apiClient.put<SettingsAiPayload>('/settings/ai', payload, { token: getToken() }),
  testProvider: (payload: ProviderTestPayload) =>
    apiClient.post<ProviderTestResult>('/settings/test-provider', payload, { token: getToken() }),

  getObsidianSettings: () => safeGet<ObsidianSettings>('/settings/obsidian'),
  updateObsidianSettings: (payload: ObsidianSettings) =>
    apiClient.put<ObsidianSettings>('/settings/obsidian', payload, { token: getToken() }),
  triggerObsidianSync: () => apiClient.post<Record<string, unknown>>('/admin/obsidian/sync', undefined, { token: getToken() }),

  listUsers: () => safeGet<AdminUserRecord[]>('/admin/users'),
  listUserActivity: () => safeGet<UserActivityRecord[]>('/admin/user-activity'),
  listLoginEvents: () => safeGet<LoginEventRecord[]>('/admin/login-events'),

  exportDatabase: () => apiClient.post<DatabaseExportResult>('/admin/database/export', undefined, { token: getToken() }),
  importDatabase: (payload: FormData) =>
    fetch(`${getApiBaseUrl()}/admin/database/import`, {
      method: 'POST',
      headers: {
        ...(getToken() ? { Authorization: `Bearer ${getToken()}` } : {}),
      },
      body: payload,
    }).then(async (response) => {
      const parsed = (await response.json().catch(() => null)) as
        | { success?: boolean; data?: DatabaseImportResult; error?: unknown }
        | null
      if (!response.ok || !parsed?.success) {
        throw new ApiError(
          typeof parsed?.error === 'string' ? parsed.error : `Request failed with status ${response.status}`,
          response.status,
          parsed?.error,
        )
      }
      return parsed.data ?? {}
    }),

  listJobs: () => apiClient.get<JobRecord[]>('/jobs', { token: getToken() }),
  listSchedulerTasks: () => safeGet<SchedulerTaskRecord[]>('/scheduler/tasks'),
}

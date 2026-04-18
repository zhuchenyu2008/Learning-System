export type ProviderType = 'llm' | 'embedding' | 'stt' | 'ocr'

export interface ProviderConfig {
  provider_type: ProviderType
  base_url: string
  api_key?: string
  model_name: string
  extra_json?: string | Record<string, unknown> | null
  is_enabled: boolean
}

export interface SettingsAiPayload {
  providers: ProviderConfig[]
}

export interface SystemSettings {
  allow_registration: boolean
  workspace_root: string
  timezone: string
  review_retention_target: string
}

export interface ObsidianSettings {
  enabled: boolean
  vault_path: string
  vault_name: string
  vault_id: string
  obsidian_headless_path: string
  config_dir: string
  device_name: string
  sync_command?: string
}

export interface ProviderTestPayload {
  provider_type: ProviderType
  base_url: string
  api_key?: string
  model_name: string
}

export interface ProviderTestResult {
  status: string
  message: string
}

export interface AdminUserRecord {
  id: number | string
  username: string
  email?: string
  role: 'admin' | 'viewer'
  is_active: boolean
  created_at?: string | null
  last_login_at?: string | null
}

export interface UserActivityRecord {
  id?: number | string
  username?: string
  user_id?: number | string
  total_watch_seconds?: number
  review_count?: number
  page_view_count?: number
  note_view_count?: number
  review_watch_seconds?: number
  last_seen_at?: string | null
  last_activity_at?: string | null
  last_event_type?: string | null
  [key: string]: unknown
}

export interface LoginEventRecord {
  id?: number | string
  username?: string
  user_id?: number | string
  event_type?: string
  ip_address?: string | null
  created_at?: string | null
  [key: string]: unknown
}

export interface DatabaseExportResult {
  message?: string
  path?: string
  filename?: string
  status?: string
  [key: string]: unknown
}

export interface DatabaseImportResult {
  message?: string
  status?: string
  imported?: boolean
  [key: string]: unknown
}

export interface SchedulerTaskRecord {
  name: string
  schedule?: string | null
  description?: string | null
  enabled?: boolean
  [key: string]: unknown
}

export interface JobRecord {
  id: number
  job_type: string
  status: string
  payload_json?: Record<string, unknown> | null
  result_json?: Record<string, unknown> | null
  logs_json?: Array<Record<string, unknown>> | null
  celery_task_id?: string | null
  error_message?: string | null
  started_at?: string | null
  finished_at?: string | null
  created_at?: string | null
  updated_at?: string | null
}

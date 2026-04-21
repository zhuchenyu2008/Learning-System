import { apiClient, getApiBaseUrl } from '@/lib/api-client'
import { useAuthStore } from '@/stores/auth-store'
import type {
  JobRecord,
  NoteDetail,
  NoteGeneratePayload,
  NoteGenerateResult,
  NotesListOptions,
  NoteSummary,
  NoteTreeNode,
  SourceAsset,
  SourceScanPayload,
  SourceScanResult,
  SourceUploadPayload,
} from '@/types/notes'

function getToken() {
  return useAuthStore.getState().accessToken
}

function buildNotesQuery(options?: NotesListOptions) {
  const params = new URLSearchParams()
  if (options?.includeArtifacts) {
    params.set('include_artifacts', 'true')
  }
  const query = params.toString()
  return query ? `?${query}` : ''
}

export const notesApi = {
  listSources: () => apiClient.get<SourceAsset[]>('/sources', { token: getToken() }),
  deleteSource: (sourceId: number) => apiClient.delete<{ id: number }>(`/sources/${sourceId}`, { token: getToken() }),
  deleteNote: (noteId: number) =>
    apiClient.delete<{ id: number; deleted_note_id: number; deleted_artifact_id: number | null; deleted_relative_paths: string[] }>(`/notes/${noteId}`, { token: getToken() }),
  uploadSource: async ({ file, uploadDir }: SourceUploadPayload) => {
    const token = getToken()
    const formData = new FormData()
    formData.append('file', file)
    if (uploadDir) {
      formData.append('upload_dir', uploadDir)
    }

    const response = await fetch(`${getApiBaseUrl()}/sources/upload`, {
      method: 'POST',
      headers: token ? { Authorization: `Bearer ${token}` } : undefined,
      body: formData,
    })

    const payload = await response.json().catch(() => null)
    if (!response.ok || !payload?.success) {
      throw new Error(typeof payload?.error === 'string' ? payload.error : `Upload failed with status ${response.status}`)
    }

    return payload.data as SourceAsset
  },
  scanSources: (payload: SourceScanPayload) =>
    apiClient.post<SourceScanResult>('/sources/scan', payload, { token: getToken() }),
  listNotes: (options?: NotesListOptions) => apiClient.get<NoteSummary[]>(`/notes${buildNotesQuery(options)}`, { token: getToken() }),
  getNotesTree: (options?: NotesListOptions) => apiClient.get<NoteTreeNode[]>(`/notes/tree${buildNotesQuery(options)}`, { token: getToken() }),
  getNoteDetail: (noteId: number) => apiClient.get<NoteDetail>(`/notes/${noteId}`, { token: getToken() }),
  reportWatchSeconds: async (noteId: number, watchSeconds: number) => {
    const normalizedSeconds = Math.max(0, Math.floor(watchSeconds))
    if (!normalizedSeconds) return

    const token = getToken()
    if (!token) return

    await fetch(`${getApiBaseUrl()}/notes/${noteId}/watch`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ watch_seconds: normalizedSeconds }),
      keepalive: true,
    }).catch(() => undefined)
  },
  generateNotes: (payload: NoteGeneratePayload) =>
    apiClient.post<NoteGenerateResult>('/notes/generate', payload, { token: getToken() }),
  listJobs: () => apiClient.get<JobRecord[]>('/jobs', { token: getToken() }),
}

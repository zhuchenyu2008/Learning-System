import { apiClient, getApiBaseUrl } from '@/lib/api-client'
import { useAuthStore } from '@/stores/auth-store'
import type {
  JobRecord,
  NoteDetail,
  NoteGeneratePayload,
  NoteGenerateResult,
  NoteSummary,
  NoteTreeNode,
  SourceAsset,
  SourceScanPayload,
  SourceScanResult,
} from '@/types/notes'

function getToken() {
  return useAuthStore.getState().accessToken
}

export const notesApi = {
  listSources: () => apiClient.get<SourceAsset[]>('/sources', { token: getToken() }),
  scanSources: (payload: SourceScanPayload) =>
    apiClient.post<SourceScanResult>('/sources/scan', payload, { token: getToken() }),
  listNotes: () => apiClient.get<NoteSummary[]>('/notes', { token: getToken() }),
  getNotesTree: () => apiClient.get<NoteTreeNode[]>('/notes/tree', { token: getToken() }),
  getNoteDetail: (noteId: number, watchSeconds = 0) =>
    apiClient.get<NoteDetail>(`/notes/${noteId}?watch_seconds=${Math.max(0, Math.floor(watchSeconds))}`, { token: getToken() }),
  reportWatchSeconds: async (noteId: number, watchSeconds: number) => {
    const normalizedSeconds = Math.max(0, Math.floor(watchSeconds))
    if (!normalizedSeconds) return

    const token = getToken()
    if (!token) return

    await fetch(`${getApiBaseUrl()}/notes/${noteId}?watch_seconds=${normalizedSeconds}`, {
      method: 'GET',
      headers: {
        Authorization: `Bearer ${token}`,
      },
      keepalive: true,
    }).catch(() => undefined)
  },
  generateNotes: (payload: NoteGeneratePayload) =>
    apiClient.post<NoteGenerateResult>('/notes/generate', payload, { token: getToken() }),
  listJobs: () => apiClient.get<JobRecord[]>('/jobs', { token: getToken() }),
}

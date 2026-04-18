import { apiClient } from '@/lib/api-client'
import { useAuthStore } from '@/stores/auth-store'
import type {
  ArtifactGeneratePayload,
  ArtifactGenerateResult,
  ArtifactListItem,
  ReviewBootstrapPayload,
  ReviewBootstrapResult,
  ReviewGradePayload,
  ReviewGradeResult,
  ReviewLogCreatePayload,
  ReviewLogRecord,
  ReviewOverview,
  ReviewQueueItem,
} from '@/types/notes'

function getToken() {
  return useAuthStore.getState().accessToken
}

export const reviewApi = {
  getOverview: () => apiClient.get<ReviewOverview>('/review/overview', { token: getToken() }),
  getQueue: (params?: { limit?: number; dueOnly?: boolean }) => {
    const searchParams = new URLSearchParams()
    if (params?.limit != null) searchParams.set('limit', String(params.limit))
    if (params?.dueOnly != null) searchParams.set('due_only', String(params.dueOnly))
    const suffix = searchParams.toString() ? `?${searchParams.toString()}` : ''
    return apiClient.get<ReviewQueueItem[]>(`/review/queue${suffix}`, { token: getToken() })
  },
  bootstrapCards: (payload: ReviewBootstrapPayload) =>
    apiClient.post<ReviewBootstrapResult>('/review/cards/bootstrap', payload, { token: getToken() }),
  gradeCard: (cardId: number, payload: ReviewGradePayload) =>
    apiClient.post<ReviewGradeResult>(`/review/session/${cardId}/grade`, payload, { token: getToken() }),
  listLogs: (limit = 50) => apiClient.get<ReviewLogRecord[]>(`/review/logs?limit=${limit}`, { token: getToken() }),
  createLog: (payload: ReviewLogCreatePayload) =>
    apiClient.post<ReviewLogRecord>('/review/logs', payload, { token: getToken() }),
  listSummaries: () => apiClient.get<ArtifactListItem[]>('/summaries', { token: getToken() }),
  generateSummary: (payload: ArtifactGeneratePayload) =>
    apiClient.post<ArtifactGenerateResult>('/summaries/generate', payload, { token: getToken() }),
  listMindmaps: () => apiClient.get<ArtifactListItem[]>('/mindmaps', { token: getToken() }),
  generateMindmap: (payload: ArtifactGeneratePayload) =>
    apiClient.post<ArtifactGenerateResult>('/mindmaps/generate', payload, { token: getToken() }),
}

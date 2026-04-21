import { apiClient } from '@/lib/api-client'
import { useAuthStore } from '@/stores/auth-store'
import type {
  ArtifactGeneratePayload,
  ArtifactGenerateResult,
  ArtifactListItem,
  JobRecord,
  ReviewBootstrapPayload,
  ReviewBootstrapResult,
  ReviewCardAdminDeleteResult,
  ReviewCardAdminItem,
  ReviewCardAdminPayload,
  ReviewCardAdminUpdatePayload,
  ReviewGradePayload,
  ReviewGradeResult,
  ReviewJudgePayload,
  ReviewJudgeResult,
  ReviewLogCreatePayload,
  ReviewLogRecord,
  ReviewOverview,
  ReviewQueueItem,
  ReviewSessionFinalizePayload,
  ReviewSessionFinalizeResult,
  ReviewSessionState,
  ReviewSubjectSummary,
} from '@/types/notes'

function getToken() {
  return useAuthStore.getState().accessToken
}

export const reviewApi = {
  getOverview: () => apiClient.get<ReviewOverview>('/review/overview', { token: getToken() }),
  getQueue: (params?: { limit?: number; dueOnly?: boolean; subject?: string | null }) => {
    const searchParams = new URLSearchParams()
    if (params?.limit != null) searchParams.set('limit', String(params.limit))
    if (params?.dueOnly != null) searchParams.set('due_only', String(params.dueOnly))
    if (params?.subject) searchParams.set('subject', String(params.subject))
    const suffix = searchParams.toString() ? `?${searchParams.toString()}` : ''
    return apiClient.get<ReviewQueueItem[]>(`/review/queue${suffix}`, { token: getToken() })
  },
  listSubjects: () => apiClient.get<ReviewSubjectSummary[]>('/review/subjects', { token: getToken() }),
  listAdminCards: (params?: { subject?: string | null; noteId?: number; query?: string; limit?: number; offset?: number }) => {
    const searchParams = new URLSearchParams()
    if (params?.subject) searchParams.set('subject', String(params.subject))
    if (params?.noteId != null) searchParams.set('note_id', String(params.noteId))
    if (params?.query) searchParams.set('query', params.query)
    if (params?.limit != null) searchParams.set('limit', String(params.limit))
    if (params?.offset != null) searchParams.set('offset', String(params.offset))
    const suffix = searchParams.toString() ? `?${searchParams.toString()}` : ''
    return apiClient.get<ReviewCardAdminItem[]>(`/review/cards/admin${suffix}`, { token: getToken() })
  },
  createAdminCard: (payload: ReviewCardAdminPayload) =>
    apiClient.post<ReviewCardAdminItem>('/review/cards/admin', payload, { token: getToken() }),
  updateAdminCard: (cardId: number, payload: ReviewCardAdminUpdatePayload) =>
    apiClient.patch<ReviewCardAdminItem>(`/review/cards/admin/${cardId}`, payload, { token: getToken() }),
  deleteAdminCard: (cardId: number) =>
    apiClient.delete<ReviewCardAdminDeleteResult>(`/review/cards/admin/${cardId}`, { token: getToken() }),
  bootstrapCards: (payload: ReviewBootstrapPayload) =>
    apiClient.post<ReviewBootstrapResult>('/review/cards/bootstrap', payload, { token: getToken() }),
  startSession: (cardId: number) =>
    apiClient.post<ReviewSessionState>(`/review/session/${cardId}/start`, undefined, { token: getToken() }),
  heartbeatSession: (cardId: number) =>
    apiClient.post<ReviewSessionState>(`/review/session/${cardId}/heartbeat`, undefined, { token: getToken() }),
  finalizeSession: (cardId: number, payload: ReviewSessionFinalizePayload) =>
    apiClient.post<ReviewSessionFinalizeResult>(`/review/session/${cardId}/finalize`, payload, { token: getToken() }),
  judgeAnswer: (cardId: number, payload: ReviewJudgePayload) =>
    apiClient.post<ReviewJudgeResult>(`/review/session/${cardId}/judge`, payload, { token: getToken() }),
  gradeCard: (cardId: number, payload: ReviewGradePayload) =>
    apiClient.post<ReviewGradeResult>(`/review/session/${cardId}/grade`, payload, { token: getToken() }),
  listLogs: (limit = 50) => apiClient.get<ReviewLogRecord[]>(`/review/logs?limit=${limit}`, { token: getToken() }),
  createLog: (payload: ReviewLogCreatePayload) =>
    apiClient.post<ReviewLogRecord>('/review/logs', payload, { token: getToken() }),
  listSummaries: () => apiClient.get<ArtifactListItem[]>('/summaries', { token: getToken() }),
  generateSummary: (payload: ArtifactGeneratePayload) =>
    apiClient.post<ArtifactGenerateResult>('/summaries/generate', payload, { token: getToken() }),
  deleteSummary: (artifactId: number) =>
    apiClient.delete<{ id: number; artifact_id: number; output_note_id: number | null; deleted_note_id: number | null; deleted_relative_paths: string[] }>(`/summaries/${artifactId}`, { token: getToken() }),
  listMindmaps: () => apiClient.get<ArtifactListItem[]>('/mindmaps', { token: getToken() }),
  generateMindmap: (payload: ArtifactGeneratePayload) =>
    apiClient.post<ArtifactGenerateResult>('/mindmaps/generate', payload, { token: getToken() }),
  deleteMindmap: (artifactId: number) =>
    apiClient.delete<{ id: number; artifact_id: number; output_note_id: number | null; deleted_note_id: number | null; deleted_relative_paths: string[] }>(`/mindmaps/${artifactId}`, { token: getToken() }),
  getJob: (jobId: number) => apiClient.get<JobRecord>(`/jobs/${jobId}`, { token: getToken() }),
}

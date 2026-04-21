import { beforeEach, describe, expect, it, vi } from 'vitest'
import { reviewApi } from '@/lib/review-api'
import { useAuthStore } from '@/stores/auth-store'

const fetchSpy = vi.fn()
vi.stubGlobal('fetch', fetchSpy)

describe('reviewApi delete endpoints', () => {
  beforeEach(() => {
    fetchSpy.mockReset()
    useAuthStore.setState({
      user: { id: 1, username: 'tester', role: 'admin', isActive: true, lastLoginAt: null },
      accessToken: 'token-123',
      refreshToken: 'refresh-123',
    })
  })

  it('sends delete summary request with auth token', async () => {
    fetchSpy.mockResolvedValue({
      ok: true,
      json: vi.fn().mockResolvedValue({ success: true, data: { id: 811, artifact_id: 811, output_note_id: 202, deleted_note_id: 202, deleted_relative_paths: ['artifacts/summary/summary-note.md'] }, meta: {}, error: null }),
    })

    await expect(reviewApi.deleteSummary(811)).resolves.toEqual({
      id: 811,
      artifact_id: 811,
      output_note_id: 202,
      deleted_note_id: 202,
      deleted_relative_paths: ['artifacts/summary/summary-note.md'],
    })

    expect(fetchSpy).toHaveBeenCalledWith('/api/v1/summaries/811', {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json',
        Authorization: 'Bearer token-123',
      },
    })
  })

  it('sends delete mindmap request with auth token', async () => {
    fetchSpy.mockResolvedValue({
      ok: true,
      json: vi.fn().mockResolvedValue({ success: true, data: { id: 801, artifact_id: 801, output_note_id: 201, deleted_note_id: 201, deleted_relative_paths: ['artifacts/mindmap/mermaid-note.md'] }, meta: {}, error: null }),
    })

    await expect(reviewApi.deleteMindmap(801)).resolves.toEqual({
      id: 801,
      artifact_id: 801,
      output_note_id: 201,
      deleted_note_id: 201,
      deleted_relative_paths: ['artifacts/mindmap/mermaid-note.md'],
    })

    expect(fetchSpy).toHaveBeenCalledWith('/api/v1/mindmaps/801', {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json',
        Authorization: 'Bearer token-123',
      },
    })
  })
})

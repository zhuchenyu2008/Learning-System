import { beforeEach, describe, expect, it, vi } from 'vitest'
import { notesApi } from '@/lib/notes-api'
import { useAuthStore } from '@/stores/auth-store'

const fetchSpy = vi.fn()
vi.stubGlobal('fetch', fetchSpy)

describe('notesApi.reportWatchSeconds', () => {
  beforeEach(() => {
    fetchSpy.mockReset()
    useAuthStore.setState({
      user: { id: 1, username: 'tester', role: 'admin', isActive: true, lastLoginAt: null },
      accessToken: 'token-123',
      refreshToken: 'refresh-123',
    })
  })

  it('sends keepalive request when watch_seconds is positive', async () => {
    fetchSpy.mockResolvedValue({ ok: true })

    await notesApi.reportWatchSeconds(101, 4)

    expect(fetchSpy).toHaveBeenCalledWith('/api/v1/notes/101/watch', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: 'Bearer token-123',
      },
      body: JSON.stringify({ watch_seconds: 4 }),
      keepalive: true,
    })
  })

  it('skips request when seconds are zero or token is missing', async () => {
    await notesApi.reportWatchSeconds(101, 0)
    expect(fetchSpy).not.toHaveBeenCalled()

    useAuthStore.setState({ accessToken: null, refreshToken: null, user: null })
    await notesApi.reportWatchSeconds(101, 4)
    expect(fetchSpy).not.toHaveBeenCalled()
  })
})

describe('notesApi.listNotes', () => {
  beforeEach(() => {
    fetchSpy.mockReset()
    useAuthStore.setState({
      user: { id: 1, username: 'tester', role: 'admin', isActive: true, lastLoginAt: null },
      accessToken: 'token-123',
      refreshToken: 'refresh-123',
    })
  })

  it('adds include_artifacts query only when explicitly requested', async () => {
    fetchSpy
      .mockResolvedValueOnce({
        ok: true,
        json: vi.fn().mockResolvedValue({ success: true, data: [], meta: {}, error: null }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: vi.fn().mockResolvedValue({ success: true, data: [], meta: {}, error: null }),
      })

    await notesApi.listNotes()
    await notesApi.listNotes({ includeArtifacts: true })

    expect(fetchSpy).toHaveBeenNthCalledWith(1, '/api/v1/notes', {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        Authorization: 'Bearer token-123',
      },
    })
    expect(fetchSpy).toHaveBeenNthCalledWith(2, '/api/v1/notes?include_artifacts=true', {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        Authorization: 'Bearer token-123',
      },
    })
  })
})

describe('notesApi.deleteSource', () => {
  beforeEach(() => {
    fetchSpy.mockReset()
    useAuthStore.setState({
      user: { id: 1, username: 'tester', role: 'admin', isActive: true, lastLoginAt: null },
      accessToken: 'token-123',
      refreshToken: 'refresh-123',
    })
  })

  it('sends delete request with auth token', async () => {
    fetchSpy.mockResolvedValue({
      ok: true,
      json: vi.fn().mockResolvedValue({ success: true, data: { id: 11 }, meta: {}, error: null }),
    })

    await expect(notesApi.deleteSource(11)).resolves.toEqual({ id: 11 })

    expect(fetchSpy).toHaveBeenCalledWith('/api/v1/sources/11', {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json',
        Authorization: 'Bearer token-123',
      },
    })
  })
})

describe('notesApi.deleteNote', () => {
  beforeEach(() => {
    fetchSpy.mockReset()
    useAuthStore.setState({
      user: { id: 1, username: 'tester', role: 'admin', isActive: true, lastLoginAt: null },
      accessToken: 'token-123',
      refreshToken: 'refresh-123',
    })
  })

  it('sends delete note request with auth token', async () => {
    fetchSpy.mockResolvedValue({
      ok: true,
      json: vi.fn().mockResolvedValue({ success: true, data: { id: 21, deleted_note_id: 21, deleted_artifact_id: null, deleted_relative_paths: ['notes/a.md'] }, meta: {}, error: null }),
    })

    await expect(notesApi.deleteNote(21)).resolves.toEqual({ id: 21, deleted_note_id: 21, deleted_artifact_id: null, deleted_relative_paths: ['notes/a.md'] })

    expect(fetchSpy).toHaveBeenCalledWith('/api/v1/notes/21', {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json',
        Authorization: 'Bearer token-123',
      },
    })
  })
})

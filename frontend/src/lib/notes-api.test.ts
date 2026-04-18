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

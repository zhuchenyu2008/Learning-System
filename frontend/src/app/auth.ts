import { apiClient, ApiError } from '@/lib/api-client'
import { useAuthStore } from '@/stores/auth-store'

export async function ensureCurrentUser() {
  const { accessToken, setUser, clearSession } = useAuthStore.getState()

  if (!accessToken) {
    return null
  }

  try {
    const user = await apiClient.auth.me(accessToken)
    setUser(user)
    return user
  } catch (error) {
    if (error instanceof ApiError && error.status === 401) {
      clearSession()
      return null
    }
    throw error
  }
}

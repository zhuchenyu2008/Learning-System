import { create } from 'zustand'
import type { AuthTokens, AuthUser } from '@/types/auth'

const ACCESS_TOKEN_KEY = 'learning_system_access_token'
const REFRESH_TOKEN_KEY = 'learning_system_refresh_token'
const USER_KEY = 'learning_system_user'

interface AuthState {
  user: AuthUser | null
  accessToken: string | null
  refreshToken: string | null
  setSession: (tokens: AuthTokens, user: AuthUser) => void
  setUser: (user: AuthUser | null) => void
  clearSession: () => void
}

const initialUser = (() => {
  const raw = localStorage.getItem(USER_KEY)
  if (!raw) return null
  try {
    return JSON.parse(raw) as AuthUser
  } catch {
    return null
  }
})()

export const useAuthStore = create<AuthState>((set) => ({
  user: initialUser,
  accessToken: localStorage.getItem(ACCESS_TOKEN_KEY),
  refreshToken: localStorage.getItem(REFRESH_TOKEN_KEY),
  setSession: (tokens, user) => {
    localStorage.setItem(ACCESS_TOKEN_KEY, tokens.accessToken)
    localStorage.setItem(REFRESH_TOKEN_KEY, tokens.refreshToken)
    localStorage.setItem(USER_KEY, JSON.stringify(user))
    set({ accessToken: tokens.accessToken, refreshToken: tokens.refreshToken, user })
  },
  setUser: (user) => {
    if (user) {
      localStorage.setItem(USER_KEY, JSON.stringify(user))
    } else {
      localStorage.removeItem(USER_KEY)
    }
    set({ user })
  },
  clearSession: () => {
    localStorage.removeItem(ACCESS_TOKEN_KEY)
    localStorage.removeItem(REFRESH_TOKEN_KEY)
    localStorage.removeItem(USER_KEY)
    set({ accessToken: null, refreshToken: null, user: null })
  },
}))

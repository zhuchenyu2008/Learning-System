export type UserRole = 'admin' | 'viewer'

export interface AuthTokens {
  accessToken: string
  refreshToken: string
}

export interface AuthUser {
  id: number | string
  username: string
  role: UserRole
  isActive: boolean
  lastLoginAt?: string | null
}

export interface ApiEnvelope<T> {
  success: boolean
  data: T
  meta: Record<string, unknown>
  error: unknown
}

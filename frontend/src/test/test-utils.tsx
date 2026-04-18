import { PropsWithChildren } from 'react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { useAuthStore } from '@/stores/auth-store'
import type { AuthUser } from '@/types/auth'

interface RenderWithProvidersOptions {
  route?: string
  user?: AuthUser | null
}

export function createTestQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
      mutations: {
        retry: false,
      },
    },
  })
}

export function setAuthState(user: AuthUser | null) {
  useAuthStore.setState({
    user,
    accessToken: user ? 'test-access-token' : null,
    refreshToken: user ? 'test-refresh-token' : null,
  })
}

export function renderWithProviders(ui: React.ReactElement, options: RenderWithProvidersOptions = {}) {
  const { route = '/', user = null } = options
  const queryClient = createTestQueryClient()

  setAuthState(user)

  function Wrapper({ children }: PropsWithChildren) {
    return (
      <QueryClientProvider client={queryClient}>
        <MemoryRouter initialEntries={[route]}>{children}</MemoryRouter>
      </QueryClientProvider>
    )
  }

  return {
    queryClient,
    ...render(ui, { wrapper: Wrapper }),
  }
}

export function createUser(overrides: Partial<AuthUser> = {}): AuthUser {
  return {
    id: 1,
    username: 'tester',
    role: 'admin',
    isActive: true,
    lastLoginAt: '2026-04-18T12:00:00Z',
    ...overrides,
  }
}

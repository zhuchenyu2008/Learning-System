import { Suspense, lazy } from 'react'
import { createBrowserRouter, Navigate, redirect } from 'react-router-dom'
import { ensureCurrentUser } from '@/app/auth'
import { ProtectedLayout, RequireAuthBoundary, RootRedirect, RoutePending } from '@/app/route-components'

const LoginPage = lazy(() => import('@/pages/login-page').then((module) => ({ default: module.LoginPage })))
const RegisterPage = lazy(() => import('@/pages/register-page').then((module) => ({ default: module.RegisterPage })))
const NotesOverviewPage = lazy(() =>
  import('@/pages/notes/notes-overview-page').then((module) => ({ default: module.NotesOverviewPage })),
)
const NotesGeneratePage = lazy(() =>
  import('@/pages/notes/notes-generate-page').then((module) => ({ default: module.NotesGeneratePage })),
)
const NotesLibraryPage = lazy(() =>
  import('@/pages/notes/notes-library-page').then((module) => ({ default: module.NotesLibraryPage })),
)
const ReviewOverviewPage = lazy(() =>
  import('@/pages/review/review-overview-page').then((module) => ({ default: module.ReviewOverviewPage })),
)
const ReviewSessionPage = lazy(() =>
  import('@/pages/review/review-session-page').then((module) => ({ default: module.ReviewSessionPage })),
)
const ReviewCardsAdminPage = lazy(() =>
  import('@/pages/review/review-cards-admin-page').then((module) => ({ default: module.ReviewCardsAdminPage })),
)
const ReviewSummariesPage = lazy(() =>
  import('@/pages/review/review-summaries-page').then((module) => ({ default: module.ReviewSummariesPage })),
)
const ReviewMindmapsPage = lazy(() =>
  import('@/pages/review/review-mindmaps-page').then((module) => ({ default: module.ReviewMindmapsPage })),
)
const SettingsAiPage = lazy(() =>
  import('@/pages/settings/settings-ai-page').then((module) => ({ default: module.SettingsAiPage })),
)
const SettingsWorkspacePage = lazy(() =>
  import('@/pages/settings/settings-workspace-page').then((module) => ({ default: module.SettingsWorkspacePage })),
)
const SettingsUsersPage = lazy(() =>
  import('@/pages/settings/settings-users-page').then((module) => ({ default: module.SettingsUsersPage })),
)
const SettingsImportExportPage = lazy(() =>
  import('@/pages/settings/settings-import-export-page').then((module) => ({ default: module.SettingsImportExportPage })),
)
const SettingsJobsPage = lazy(() =>
  import('@/pages/settings/settings-jobs-page').then((module) => ({ default: module.SettingsJobsPage })),
)

async function protectedLoader() {
  const user = await ensureCurrentUser()
  if (!user) {
    throw new Response('Unauthorized', { status: 401 })
  }
  return user
}

function withSuspense(node: React.ReactNode) {
  return <Suspense fallback={<RoutePending />}>{node}</Suspense>
}

async function settingsIndexLoader() {
  const user = await ensureCurrentUser()
  if (!user) {
    throw new Response('Unauthorized', { status: 401 })
  }
  return redirect(user.role === 'admin' ? '/settings/ai' : '/settings/jobs')
}

export const router = createBrowserRouter([
  {
    path: '/',
    element: <RootRedirect />,
  },
  {
    path: '/login',
    element: withSuspense(<LoginPage />),
  },
  {
    path: '/register',
    element: withSuspense(<RegisterPage />),
  },
  {
    element: <RequireAuthBoundary />,
    children: [
      {
        path: '/',
        loader: protectedLoader,
        element: <ProtectedLayout />,
        children: [
          { path: '/notes', element: <Navigate to="/notes/overview" replace /> },
          { path: '/notes/overview', element: withSuspense(<NotesOverviewPage />) },
          { path: '/notes/generate', element: withSuspense(<NotesGeneratePage />) },
          { path: '/notes/library', element: withSuspense(<NotesLibraryPage />) },
          { path: '/review', element: <Navigate to="/review/overview" replace /> },
          { path: '/review/overview', element: withSuspense(<ReviewOverviewPage />) },
          { path: '/review/session', element: withSuspense(<ReviewSessionPage />) },
          { path: '/review/cards-admin', element: withSuspense(<ReviewCardsAdminPage />) },
          { path: '/review/summaries', element: withSuspense(<ReviewSummariesPage />) },
          { path: '/review/mindmaps', element: withSuspense(<ReviewMindmapsPage />) },
          { path: '/settings', loader: settingsIndexLoader, element: null },
          { path: '/settings/ai', element: withSuspense(<SettingsAiPage />) },
          { path: '/settings/workspace', element: withSuspense(<SettingsWorkspacePage />) },
          { path: '/settings/users', element: withSuspense(<SettingsUsersPage />) },
          { path: '/settings/import-export', element: withSuspense(<SettingsImportExportPage />) },
          { path: '/settings/jobs', element: withSuspense(<SettingsJobsPage />) },
        ],
      },
    ],
  },
])


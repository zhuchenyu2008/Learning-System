import type { JobRecord, NoteDetail, NoteSummary, NoteTreeNode, ReviewLogRecord, ReviewOverview, ReviewQueueItem, SourceAsset } from '@/types/notes'
import type { AdminUserRecord, LoginEventRecord, SchedulerTaskRecord, SettingsAiPayload, SystemSettings, UserActivityRecord } from '@/types/settings'

export const sampleNotes: NoteSummary[] = [
  {
    id: 101,
    title: 'Mermaid Note',
    relative_path: 'notes/mermaid-note.md',
    note_type: 'mindmap',
    content_hash: 'hash-101',
    source_asset_id: 11,
    frontmatter_json: {},
    created_at: '2026-04-18T10:00:00Z',
    updated_at: '2026-04-18T12:00:00Z',
  },
  {
    id: 102,
    title: 'Summary Note',
    relative_path: 'notes/summary-note.md',
    note_type: 'summary',
    content_hash: 'hash-102',
    source_asset_id: null,
    frontmatter_json: {},
    created_at: '2026-04-17T10:00:00Z',
    updated_at: '2026-04-17T12:00:00Z',
  },
]

export const sampleNoteDetail: NoteDetail = {
  ...sampleNotes[0],
  content: `# Heading\n\n- item 1\n- item 2\n\n| col | value |\n| --- | --- |\n| a | 1 |\n\n<div class="safe-html">allowed html</div>\n<script>alert('blocked')</script>\n\n\`\`\`mermaid\ngraph TD\n  A[Start] --> B[Finish]\n\`\`\``,
}

export const sampleTree: NoteTreeNode[] = [
  {
    name: 'notes',
    path: 'notes',
    is_dir: true,
    note_id: null,
    children: [
      {
        name: 'mermaid-note.md',
        path: 'notes/mermaid-note.md',
        is_dir: false,
        note_id: 101,
        children: [],
      },
    ],
  },
]

export const sampleSources: SourceAsset[] = [
  {
    id: 11,
    file_path: 'assets/chapter-1.pdf',
    file_type: 'pdf',
    checksum: 'abcdef1234567890',
    imported_at: '2026-04-18T09:00:00Z',
    metadata_json: {},
  },
]

export const sampleJobs: JobRecord[] = [
  {
    id: 301,
    job_type: 'note_generation',
    status: 'running',
    payload_json: { note_ids: [101] },
    result_json: {},
    logs_json: [{ message: 'running' }],
    celery_task_id: 'celery-301',
    error_message: null,
    started_at: '2026-04-18T11:00:00Z',
    finished_at: null,
    created_at: '2026-04-18T10:59:00Z',
    updated_at: '2026-04-18T11:01:00Z',
  },
]

export const sampleReviewOverview: ReviewOverview = {
  due_today_count: 3,
  total_cards: 24,
  recent_review_count: 8,
  recent_review_seconds: 540,
}

export const sampleReviewQueue: ReviewQueueItem[] = [
  {
    card_id: 401,
    due_at: '2026-04-19T08:00:00Z',
    suspended: false,
    knowledge_point: {
      id: 501,
      note_id: 101,
      title: 'Event Loop',
      content_md: 'Explain how the event loop schedules macro and micro tasks.',
      embedding_vector: null,
      tags_json: { tags: ['javascript', 'runtime'] },
      created_at: '2026-04-18T07:00:00Z',
      updated_at: '2026-04-18T07:10:00Z',
    },
    note: {
      id: 101,
      title: 'Mermaid Note',
      relative_path: 'notes/mermaid-note.md',
    },
  },
]

export const sampleReviewLogs: ReviewLogRecord[] = [
  {
    id: 601,
    user_id: 1,
    review_card_id: 401,
    rating: 3,
    duration_seconds: 45,
    note: '理解更稳定了',
    created_at: '2026-04-18T11:20:00Z',
    updated_at: '2026-04-18T11:20:00Z',
  },
]

export const sampleAiSettings: SettingsAiPayload = {
  providers: [
    {
      provider_type: 'llm',
      base_url: 'https://api.example.com/v1',
      api_key: 'secret',
      model_name: 'gpt-4o-mini',
      extra_json: '{"temperature":0.2}',
      is_enabled: true,
    },
  ],
}

export const sampleSystemSettings: SystemSettings = {
  allow_registration: false,
  workspace_root: '/data/workspace',
  timezone: 'UTC',
  review_retention_target: '90d',
}

export const sampleAdminUsers: AdminUserRecord[] = [
  {
    id: 1,
    username: 'admin',
    email: 'admin@example.com',
    role: 'admin',
    is_active: true,
    last_login_at: '2026-04-18T08:00:00Z',
  },
]

export const sampleUserActivity: UserActivityRecord[] = [
  {
    id: 1,
    username: 'viewer-a',
    total_watch_seconds: 120,
    review_count: 2,
    page_view_count: 5,
    note_view_count: 3,
    review_watch_seconds: 50,
    last_seen_at: '2026-04-18T08:30:00Z',
    last_event_type: 'review',
  },
]

export const sampleLoginEvents: LoginEventRecord[] = [
  {
    id: 1,
    username: 'admin',
    event_type: 'login',
    ip_address: '127.0.0.1',
    created_at: '2026-04-18T08:00:00Z',
  },
]

export const sampleSchedulerTasks: SchedulerTaskRecord[] = [
  {
    name: 'review-maintenance',
    schedule: '0 * * * *',
    description: 'refresh review queue',
    enabled: true,
  },
]

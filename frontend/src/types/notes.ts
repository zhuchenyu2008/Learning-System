export type SourceFileType = 'audio' | 'video' | 'image' | 'text' | 'markdown' | 'pdf' | 'other'

export type NoteType = 'source_note' | 'summary' | 'mindmap' | 'review_note'

export interface NotesListOptions {
  includeArtifacts?: boolean
}

export type JobType = 'note_generation' | string
export type JobStatus = 'queued' | 'pending' | 'running' | 'completed' | 'failed' | string

export interface SourceAsset {
  id: number
  file_path: string
  file_type: SourceFileType
  checksum: string
  imported_at: string
  metadata_json: Record<string, unknown>
}

export interface SourceScanResult {
  created: number
  updated: number
  scanned_files: number
  assets: SourceAsset[]
}

export interface SourceUploadPayload {
  file: File
  uploadDir?: string | null
}

export interface NoteSummary {
  id: number
  title: string
  relative_path: string
  note_type: NoteType
  content_hash: string
  source_asset_id: number | null
  frontmatter_json: Record<string, unknown>
  created_at: string
  updated_at: string
}

export interface NoteDetail extends NoteSummary {
  content: string
}

export interface NoteTreeNode {
  name: string
  path: string
  is_dir: boolean
  children: NoteTreeNode[]
  note_id: number | null
}

export interface JobRecord {
  id: number
  job_type: JobType
  status: JobStatus
  payload_json: Record<string, unknown>
  result_json: Record<string, unknown>
  logs_json: Array<Record<string, unknown>>
  celery_task_id: string | null
  error_message: string | null
  started_at: string | null
  finished_at: string | null
  created_at: string
  updated_at: string
}

export interface NoteGeneratePayload {
  source_asset_ids: number[]
  note_directory?: string | null
  force_regenerate?: boolean
  sync_to_obsidian?: boolean
}

export interface NoteGenerateResult {
  job: number
  generated_note_ids: number[]
  written_paths: string[]
  status?: string
  celery_task_id?: string | null
}

export interface SourceScanPayload {
  root_path?: string | null
  recursive?: boolean
  include_hidden?: boolean
}

export interface ReviewOverview {
  due_today_count: number
  total_cards: number
  recent_review_count: number
  recent_review_seconds: number
}

export interface ReviewKnowledgePoint {
  id: number
  note_id: number
  title: string
  content_md: string
  embedding_vector: number[] | null
  tags_json: Record<string, unknown>
  summary_text?: string | null
  source_anchor?: string | null
  subject?: string | null
  created_at: string
  updated_at: string
}

export interface ReviewQueueItem {
  card_id: number
  due_at: string
  suspended: boolean
  subject?: string | null
  knowledge_point: ReviewKnowledgePoint
  note: {
    id: number
    title: string
    relative_path: string
  }
}

export interface ReviewSubjectSummary {
  subject: string
  total_cards: number
  due_cards: number
}

export interface ReviewCardAdminPayload {
  note_id: number
  title: string
  content_md: string
  summary_text?: string | null
  source_anchor?: string | null
  tags?: string[]
  subject?: string | null
  suspended?: boolean
}

export interface ReviewCardAdminUpdatePayload {
  title?: string
  content_md?: string
  summary_text?: string | null
  source_anchor?: string | null
  tags?: string[]
  subject?: string | null
  suspended?: boolean
}

export interface ReviewCardAdminItem extends ReviewQueueItem {}

export interface ReviewGradePayload {
  rating: 1 | 2 | 3 | 4
  duration_seconds?: number
  note?: string | null
  answer?: string | null
  ai_judge?: Record<string, unknown> | null
}

export interface ReviewJudgePayload {
  answer: string
  duration_seconds?: number
  note?: string | null
}

export interface ReviewJudgeResult {
  card_id: number
  answer: string
  expected_answer: string
  suggested_rating: 1 | 2 | 3 | 4
  correctness: 'correct' | 'partial' | 'incorrect' | 'unknown'
  explanation: string
  judge_status: 'ai' | 'fallback'
  judge_error: string | null
}

export interface ReviewSessionState {
  active_card_id: number | null
  accumulated_seconds: number
  increment_seconds?: number
  started_at: string | null
  last_heartbeat_at: string | null
}

export interface ReviewSessionFinalizePayload {
  duration_seconds?: number
}

export interface ReviewSessionFinalizeResult {
  card_id: number
  duration_seconds: number
  server_accumulated_seconds: number
  client_reported_seconds: number
  finalized_at: string
}

export interface ReviewLogRecord {
  id: number
  user_id: number
  review_card_id: number
  rating: number
  duration_seconds: number
  note: string | null
  created_at: string
  updated_at: string
}

export interface ReviewGradeResult {
  card: {
    id: number
    state_json: Record<string, unknown>
    due_at: string
    last_reviewed_at: string | null
  }
  review_log: ReviewLogRecord
}

export interface ReviewBootstrapPayload {
  note_ids: number[]
  all_notes?: boolean
}

export interface ReviewBootstrapResult {
  created_knowledge_points: number
  created_cards: number
  note_ids: number[]
}

export interface ReviewCardAdminDeleteResult {
  card_id: number
  deleted: boolean
  deleted_knowledge_point_id: number | null
}

export interface ReviewLogCreatePayload {
  review_card_id: number
  rating: 1 | 2 | 3 | 4
  duration_seconds?: number
  note?: string | null
}

export type ArtifactScopeType = 'manual' | 'scheduled'
export type ArtifactType = 'summary' | 'mindmap'

export interface ArtifactListItem {
  id: number
  artifact_type: ArtifactType
  scope_type: ArtifactScopeType
  note_ids_json: number[]
  prompt_extra: string | null
  output_note_id: number | null
  status: string
  created_at: string
  updated_at: string
}

export interface ArtifactGeneratePayload {
  scope: ArtifactScopeType
  note_ids: number[]
  prompt_extra?: string | null
}

export interface ArtifactGenerateResult {
  job_id: number
  artifact_id: number | null
  output_note_id: number | null
  relative_path: string | null
  status: string
  celery_task_id?: string | null
}

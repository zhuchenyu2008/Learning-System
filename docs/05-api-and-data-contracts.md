# 05-API 与数据契约主文档

## 1. API 规范
- Base URL: `/api/v1`
- 响应统一：
```json
{
  "success": true,
  "data": {},
  "meta": {},
  "error": null
}
```

## 2. 核心 API 分组
### 2.1 Auth
- `POST /auth/login`
- `POST /auth/refresh`
- `POST /auth/logout`
- `POST /auth/register`（仅开放注册时可用）
- `GET /auth/me`

### 2.2 Settings
- `GET /settings/system`
- `PUT /settings/system`
- `GET /settings/ai`
- `PUT /settings/ai`
- `GET /settings/obsidian`
- `PUT /settings/obsidian`
- `POST /settings/test-provider`

### 2.3 Files / Notes
- `POST /sources/scan`
- `POST /sources/upload-manifest`
- `GET /sources`
- `POST /notes/generate`
- `GET /notes`
- `GET /notes/{id}`
- `GET /notes/tree`
- `POST /notes/{id}/reindex`

### 2.4 Review
- `GET /review/overview`
- `GET /review/queue`
- `POST /review/cards/bootstrap`
- `POST /review/session/{cardId}/grade`
- `GET /review/logs`
- `POST /review/logs`

### 2.5 Summaries / Mindmaps
- `POST /summaries/generate`
- `GET /summaries`
- `POST /mindmaps/generate`
- `GET /mindmaps`

### 2.6 Jobs
- `GET /jobs`
- `GET /jobs/{id}`

### 2.7 Admin
- `GET /admin/users`
- `GET /admin/user-activity`
- `GET /admin/login-events`
- `POST /admin/database/export`
- `POST /admin/database/import`
- `POST /admin/obsidian/sync`

## 3. 核心数据实体
### 3.1 User
- id
- username
- password_hash
- role(admin|viewer)
- is_active
- created_at
- last_login_at

### 3.2 SystemSetting
- allow_registration
- workspace_root
- timezone
- review_retention_target

### 3.3 AIProviderConfig
- provider_type(llm|embedding|stt|ocr)
- base_url
- api_key_encrypted
- model_name
- extra_json
- is_enabled

### 3.4 SourceAsset
- id
- file_path
- file_type(audio|video|image|text|markdown|pdf|other)
- checksum
- imported_at
- metadata_json

### 3.5 Note
- id
- title
- relative_path
- note_type(source_note|summary|mindmap|review_note)
- content_hash
- source_asset_id
- frontmatter_json
- created_at
- updated_at

### 3.6 KnowledgePoint
- id
- note_id
- title
- content_md
- embedding_vector
- tags_json

### 3.7 ReviewCard
- id
- knowledge_point_id
- state_json(fsrs)
- due_at
- last_reviewed_at
- suspended

### 3.8 ReviewLog
- id
- user_id
- review_card_id
- rating
- duration_seconds
- note
- created_at

### 3.9 GeneratedArtifact
- id
- artifact_type(summary|mindmap)
- scope_type(manual|scheduled)
- note_ids_json
- prompt_extra
- output_note_id
- created_at

### 3.10 Job
- id
- job_type
- status
- payload_json
- result_json
- error_message
- created_at
- updated_at

## 4. 权限契约
- viewer: GET 内容 + POST review logs + POST review grading
- admin: 全部权限

## 5. Markdown 渲染契约
- 支持 GFM
- 支持白名单 HTML 标签
- 支持 ```mermaid 代码块

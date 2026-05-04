# 03 数据模型

## 原则

- PostgreSQL 是唯一主存储。
- Obsidian 导出文件是数据库内容的副本。
- 上传源文件只记录元数据和存储路径，不写入导出目录。
- 所有生成内容必须保留来源关系，支持追溯。
- 所有关键写入操作必须记录审计日志。

## 枚举

### Role

- `admin`
- `user`

### SourceType

- `audio`
- `video`
- `image`
- `pdf`
- `ppt`
- `docx`
- `markdown`
- `text`
- `other`

### JobStatus

- `queued`
- `running`
- `waiting_input`
- `succeeded`
- `failed`
- `cancelled`
- `retrying`

### ContentType

- `note`
- `knowledge_summary`
- `mind_map`

## 用户与认证

### users

- `id`
- `email`
- `name`
- `password_hash`
- `role`
- `status`
- `created_at`
- `updated_at`
- `last_login_at`

### sessions

- `id`
- `user_id`
- `token_hash`
- `ip`
- `user_agent`
- `created_at`
- `last_seen_at`
- `expires_at`
- `revoked_at`

### app_settings

- `id`
- `key`
- `value_json`
- `updated_by`
- `updated_at`

用于存储是否开放注册、导出策略、默认学科等低频配置。

## AI 配置

### ai_model_configs

- `id`
- `purpose`: `note_generation`、`embedding`、`speech_to_text`、`ocr`、`reranker`、`grading`
- `provider_label`
- `base_url`
- `api_key_encrypted`
- `model_name`
- `enabled`
- `required`
- `last_test_status`
- `last_test_message`
- `created_at`
- `updated_at`

必填项：

- `note_generation`
- `embedding`
- `speech_to_text`

OCR 可复用多模态模型配置，但如果启用图片/PDF 扫描工作流，则必须存在可用 OCR/视觉理解配置。

### prompt_settings

- `id`
- `purpose`
- `extra_prompt`
- `updated_by`
- `updated_at`

笔记总结额外提示词存储在这里。知识点总结和思维导图手动生成时的额外提示词记录在对应生成任务中。

## 来源文件与解析片段

### source_files

- `id`
- `uploader_id`
- `type`
- `original_name`
- `mime_type`
- `size_bytes`
- `storage_key`
- `sha256`
- `subject_guess`
- `status`
- `created_at`

### source_segments

- `id`
- `source_file_id`
- `segment_type`: `transcript`、`ocr`、`slide_text`、`page_text`、`manual_text`、`image_caption`
- `title`
- `content`
- `language`
- `start_time_ms`
- `end_time_ms`
- `page_number`
- `image_region_json`
- `confidence`
- `selected_by_default`
- `created_at`

解析片段是笔记生成时管理员勾选的最小来源单位。

## 笔记

### notes

- `id`
- `subject`
- `type`: `class_note`、`homework`、`mistake`、`review_note`
- `ai_title`
- `title`
- `markdown`
- `source_summary`
- `created_by`
- `updated_by`
- `created_at`
- `updated_at`
- `export_status`
- `export_path`
- `exported_at`

笔记本身不区分草稿、发布或已整理状态。编辑、索引、导出等进度由任务和导出/索引字段表达，避免在阅读界面制造额外状态。

### note_sources

- `note_id`
- `source_file_id`
- `source_segment_id`

### note_links

- `id`
- `note_id`
- `target_note_id`
- `relation`: `previous_class`、`same_topic`、`related_mistake`、`source_context`
- `description`

用于实现参考 `obsidian-study-notes` 的关联笔记规则。

## 复习

### review_cards

- `id`
- `note_id`
- `subject`
- `question`
- `answer`
- `card_type`: `qa`、`cloze`
- `quality_status`: `active`、`needs_fix`、`deleted`
- `created_by`
- `created_at`
- `updated_at`

### fsrs_states

- `card_id`
- `user_id`
- `due_at`
- `stability`
- `difficulty`
- `elapsed_days`
- `scheduled_days`
- `reps`
- `lapses`
- `state`
- `last_reviewed_at`

FSRS 状态按用户维度维护，因为普通用户允许独立复习并写入日志。

### review_logs

- `id`
- `card_id`
- `user_id`
- `answer_text`
- `ai_score`
- `manual_score`
- `rating`: `again`、`hard`、`good`、`easy`
- `feedback_markdown`
- `reviewed_at`
- `duration_ms`
- `fsrs_before_json`
- `fsrs_after_json`

管理员可以查看普通用户复习情况。

## RAG

### rag_chunks

- `id`
- `content_type`
- `content_id`
- `chunk_index`
- `subject`
- `title`
- `markdown_path`
- `content`
- `embedding`
- `token_count`
- `created_at`
- `updated_at`

`embedding` 使用 pgvector 类型。

### rag_queries

- `id`
- `user_id`
- `query`
- `answer_markdown`
- `citations_json`
- `created_at`

## 总结与思维导图

### knowledge_summaries

- `id`
- `subject`
- `ai_title`
- `title`
- `markdown`
- `source_scope_json`
- `extra_prompt`
- `generation_mode`: `manual`
- `created_by`
- `created_at`
- `export_status`
- `export_path`

### mind_maps

- `id`
- `subject`
- `ai_title`
- `title`
- `source_scope_json`
- `extra_prompt`
- `markmap_markdown`
- `mermaid_mindmap`
- `summary_markdown`
- `generation_mode`
- `created_by`
- `created_at`
- `export_status`
- `export_path`

主渲染使用 `markmap_markdown`。`mermaid_mindmap` 用于兼容导出和静态预览。

## 异步任务

### jobs

- `id`
- `queue`
- `name`
- `bullmq_job_id`
- `status`
- `progress`
- `input_json`
- `result_json`
- `error_message`
- `created_by`
- `created_at`
- `started_at`
- `finished_at`

### job_logs

- `id`
- `job_id`
- `level`
- `message`
- `metadata_json`
- `created_at`

## 审计与观看时长

### audit_logs

- `id`
- `actor_id`
- `action`
- `entity_type`
- `entity_id`
- `ip`
- `metadata_json`
- `created_at`

### view_events

- `id`
- `user_id`
- `entity_type`
- `entity_id`
- `event_type`: `open`、`heartbeat`、`close`
- `duration_ms`
- `created_at`

观看时长由前端定期 heartbeat 写入，后端按用户和内容聚合。


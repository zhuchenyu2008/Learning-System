# 68-笔记生成全流程API与数据契约

## 1. 配置契约
需要支持四类 provider：
- llm
- embedding
- ocr
- stt

每类至少包含：
- base_url
- api_key
- model_name
- extra_json
- is_enabled

## 2. 生成内部中间态契约
### Extraction Result
- text
- metadata

### Retrieval Result（新增目标）
- query_text
- matched_note_ids
- matched_paths
- snippets
- similarity_scores
- provider_model

### Generation Context（新增目标）
- current_datetime
- source_metadata
- normalized_text
- retrieval_context
- prompt_policy_version

### Generation Output（新增目标）
- title
- subject
- relative_path
- markdown_body
- summary
- confidence / warnings（可选）

## 3. Job 可观测性
日志阶段目标扩展为：
- ingest
- extract
- normalize
- retrieve
- generate
- write

result_json 目标包含：
- processed_assets
- retrieval_summary
- generated_note_ids
- written_paths
- obsidian_sync（如启用）

# 84-提交准备说明

## 1. 提交目标
本提交用于收口“学习笔记生成主链改造 + P0/P1/P2 修复 + 最终交接前端构建阻塞清理 + 新一轮后测问题修复”这一整轮工作，重点是：
- settings 密钥脱敏
- embedding runtime 接入
- retrieval service 接入
- 主链 retrieve + 结构化生成输出
- 学科分类/命名/路径写回
- image/pdf/audio 质量门禁
- P0：笔记内容污染清理、mermaid/思维导图渲染稳定性修复
- P1：生成状态文案、docx 链路、artifact/笔记分层、异步复习卡片、review session 时长统计
- P2：复习时 AI 判分与讲解
- SA-47：前端全量 build 阻塞修复
- SA-51：复习卡片从“异步规则切片”补成“优先 AI、失败回退”的生成链
- SA-52：summary 页面补齐产物详情/预览能力
- SA-53：mindmap prompt / 输入 / 输出约束收紧，改善导图混乱问题
- 测试与交付文档补齐

不包含：
- 新功能继续扩张
- git push
- 冒充用户完成最终人工验收

---

## 2. 建议提交标题

### 方案 A：单提交标题
`feat: finalize note generation retrieval pipeline and delivery prep`

### 方案 B：更偏中文说明
`feat: 完成笔记生成检索主链改造并补齐交付收口材料`

---

## 3. 建议提交说明正文
可直接参考下述结构整理 commit message / PR 描述：

### Summary
- mask `/settings/ai` api keys and keep provider config contract compatible
- add runtime embedding calls for openai-compatible providers
- add standalone note retrieval service with note chunk matching
- extend note generation pipeline to ingest/extract/normalize/retrieve/generate/write
- upgrade generation output from markdown string to structured JSON result
- add subject normalization, timestamp naming and subject-directory writeback
- add image/pdf/audio extraction quality gates and degraded/failed business statuses
- clean note body pollution and harden mermaid/mindmap rendering isolation
- improve generation status UX, docx diagnostics, artifact layering and async review card generation
- add review-session-based watch time tracking plus AI review judgement/explanation flow
- fix the frontend TypeScript build blocker and restore full frontend build
- make review card generation actually use AI first with fallback visibility in job logs/result payloads
- add summary artifact preview/detail flow on the review summaries page
- tighten mindmap prompt/input/output constraints to reduce noisy and chaotic diagrams
- add retrieval/generation/settings/review/frontend regression coverage and final delivery docs

### Details
- settings API now returns empty `api_key` plus `api_key_masked` and `has_api_key`
- embedding adapter now calls `/embeddings` and returns vectors/model/usage
- retrieval results now include matched note ids/paths/snippets/scores/context
- generated notes now persist retrieval summary in frontmatter and job result
- generated paths now follow `notes/subjects/<学科>/<标题>-YYYY-MM-DD-HHmm(.md)`
- low-quality OCR/STT/PDF placeholder inputs now fail fast or produce degraded warnings instead of pretending full success
- review card jobs now expose whether generation ran in `ai` / `mixed` / `fallback` mode and log AI-started/AI-completed/fallback events
- summary artifacts can now be previewed by loading the linked output note detail in the review UI
- mindmap generation now trims noisy sections and enforces a single-root, limited-branch Mermaid mindmap structure

### Risks / Follow-up
- rerun docker with latest code before user handoff
- recheck real retrieval hit evidence on preserved candidate notes
- validate review AI judge flow and artifact/note layering on the latest instance
- run final manual acceptance with user-owned test flow

---

## 4. 建议纳入提交的关键文件

### 后端实现
- `backend/app/api/v1/endpoints/settings.py`
- `backend/app/integrations/openai_compatible.py`
- `backend/app/schemas/integrations.py`
- `backend/app/schemas/settings_admin.py`
- `backend/app/services/settings_admin_service.py`
- `backend/app/services/note_generation_service.py`
- `backend/app/services/note_retrieval_service.py`
- `backend/app/services/note_naming_service.py`
- `backend/app/services/artifact_service.py`
- `backend/app/api/v1/endpoints/review.py`
- `backend/app/services/review_service.py`
- `backend/app/schemas/review.py`
- `backend/app/models/job.py`

### 测试
- `backend/tests/test_embedding_retrieval.py`
- `backend/tests/test_notes_ingestion.py`
- `backend/tests/test_settings_admin.py`
- `backend/tests/test_job_model.py`
- `backend/tests/test_source_upload_service.py`
- `frontend/src/pages/notes/notes-library-page.test.tsx`
- `frontend/src/pages/notes/notes-generate-page.test.tsx`
- `frontend/src/components/mermaid-renderer.test.tsx`
- `frontend/src/components/note-detail-renderer.test.tsx`
- `frontend/src/pages/review/review-session-page.test.tsx`
- `frontend/src/pages/review/review-mindmaps-page.test.tsx`
- `frontend/src/pages/review/review-summaries-page.test.tsx`
- `backend/tests/test_review_artifacts.py`

### 文档
- `docs/73-note-generation-detailed-solution.md`
- `docs/77-phased-implementation-and-task-breakdown.md`
- `docs/79-pre-implementation-control-freeze.md`
- `docs/81-final-delivery-and-release-prep-main.md`
- `docs/82-final-handoff-orchestration-plan.md`
- `docs/83-final-delivery-summary.md`
- `docs/84-commit-preparation-notes.md`
- `docs/92-p0-fixes-main.md`
- `docs/93-p1-fixes-main.md`
- `docs/94-p2-ai-review-judgement-main.md`
- `docs/95-final-pre-handoff-ts-fix-and-rerun-main.md`
- `docs/subagents/SA-33-settings-redaction-and-config-contract.md`
- `docs/subagents/SA-34-embedding-runtime-and-retrieval-service.md`
- `docs/subagents/SA-35-main-pipeline-retrieve-and-structured-output.md`
- `docs/subagents/SA-36-subject-naming-and-path-writeback.md`
- `docs/subagents/SA-37-quality-gates-and-final-real-regression.md`
- `docs/subagents/SA-39-retrieval-real-hit-validation.md`
- `docs/subagents/SA-40-final-delivery-summary-and-commit-prep.md`
- `docs/subagents/SA-47-frontend-ts-build-blocker-fix.md`
- `docs/subagents/SA-48-final-delivery-summary-refresh.md`
- `docs/subagents/SA-51-review-card-ai-generation.md`
- `docs/subagents/SA-52-summary-preview-fix.md`
- `docs/subagents/SA-53-mindmap-quality-constraints.md`
- `docs/subagents/SA-54-refresh-final-summary-after-latest-fixes.md`

---

## 5. 提交前建议核对清单

### 必查
- [ ] `/api/v1/settings/ai` GET/PUT 不返回明文 key
- [ ] note generation job log 包含 `retrieve`
- [ ] `result_json.processed_assets[*].retrieval_summary` 存在
- [ ] 生成结果不是纯字符串，而是结构化 `title/subject/markdown_body`
- [ ] 路径符合 `notes/subjects/<学科>/<标题>-YYYY-MM-DD-HHmm.md`
- [ ] image/audio/pdf 低质量输入不会伪装为完整业务成功
- [ ] 主笔记正文不再混入过程性检索/抽取污染内容
- [ ] summary / mindmap 不再默认混入主笔记库
- [ ] review session 时长统计可增长并落库
- [ ] review AI judge 失败时有可解释回退
- [ ] review card generation 可证明真实走过 AI 或给出明确 fallback 原因
- [ ] summary 页面可从产物列表进入详情预览
- [ ] mindmap 新产物结构明显收敛，无大段噪声或失控展开
- [ ] frontend `npm run build` 通过

### 运行环境交接前
- [ ] Docker 普通流程重启完成
- [ ] 前后端可访问
- [ ] 至少完成 1 次文本类生成验证
- [ ] 至少完成 1 次非空 retrieval 命中验证
- [ ] 至少完成 1 次低质量门禁验证
- [ ] 至少完成 1 次 review AI 判分与讲解验证
- [ ] 至少完成 1 次 review card AI 生成链验证（或明确 fallback）
- [ ] 至少完成 1 次 summary 产物详情预览验证
- [ ] 至少完成 1 次 mindmap 新约束质量验证
- [ ] 检查 notes library / artifact 分层与生成页状态文案

---

## 6. 测试摘要（提交描述可引用）

### 代码级覆盖
- settings 脱敏与 key 覆盖逻辑：已补测试
- embeddings endpoint 调用与 retrieval 排序：已补测试
- 主链 retrieve / retrieval_summary / frontmatter：已补测试
- image/audio/pdf 质量门禁：已补测试
- text/markdown/docx 生成链：已补测试
- 笔记污染清理与 mermaid 渲染隔离：已有实现与最小回归覆盖
- 生成状态、artifact 分层、review session / AI judge：已有实现与最小回归覆盖
- review card AI 生成 / fallback 分流：已补测试与 job 结果字段验证
- summary 产物预览详情：已补前端页面测试
- mindmap 输入清洗 / prompt 收紧 / 输出规范化：已补测试
- 前端 TS 构建阻塞：已修复并恢复全量 build

### 当前收口阶段说明
- SA-54 本次仅同步最终交付总结与提交准备文档，不改业务代码。
- SA-47 已先行清除前端 TypeScript 构建阻塞，前端全量 build 已恢复通过。
- SA-51 / SA-52 / SA-53 的最新实现与验证结论已纳入本次提交准备说明。
- 因此最终“环境可交付”结论，仍应以 Docker 标准重启后的统一实例验证与用户人工验收为准。

建议在 PR/提交说明中表述为：
> Code and targeted regression coverage are in place; final environment readiness and manual acceptance remain to be completed after Docker rerun and user-side verification.

---

## 7. 建议不要一起提交的内容
如果整理正式提交，建议额外审查并按需排除以下内容：
- 与本轮笔记主链目标无关的前端 UX 历史遗留改动
- 本地临时数据库文件：
  - `test_learning_system.db`
  - `tmp_docx_repro.db`
- 临时目录：
  - `tmp_sa27d/`
  - `tmp_sa27e/`
  - `tmp_sa27e_rerun/`
  - `tmp_sa31/`
  - `tmp_sa39/`
  - `workspace/`
- 编译缓存：
  - `frontend/src/**/*.tsbuildinfo` 相关产物（按仓库规范决定是否纳入）

---

## 8. 人工交接话术建议
提交后对用户/主 agent 的交接建议：
1. 本轮代码主链改造与交付文档已收口。
2. 尚未替用户完成最终人工测试。
3. 下一步先走 Docker 普通流程重启与健康确认。
4. 再由用户在最新实例上执行最终体验验收。

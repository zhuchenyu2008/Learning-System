# 83-最终交付总结

## 1. 交付范围
本轮交付已从“笔记生成主链改造收口”扩展为“主链改造 + 最后一轮 P0/P1/P2 修复 + 前端构建阻塞清理 + 新一轮后测问题修复”的最终交付总结。

当前总结基于既定分工汇总以下阶段成果：
- SA-33、SA-34、SA-35、SA-36、SA-37、SA-39：笔记生成主链改造、retrieval、结构化输出、命名写回、质量门禁、retrieval 专项验真
- SA-44A、SA-44B、SA-44C：P0 收口（笔记内容污染清理、mermaid/思维导图渲染稳定性）
- SA-45A、SA-45B、SA-45C、SA-45D、SA-45E：P1 收口（生成状态文案、docx 链路、artifact/笔记分层、异步复习卡片、review session 时长统计）
- SA-46：P2 收口（复习时 AI 判分与讲解）
- SA-47：前端既有 TypeScript 构建阻塞修复，恢复前端全量 build
- SA-51、SA-52、SA-53：新一轮后测问题修复（复习卡片真正走 AI、summary 预览恢复、mindmap 质量约束收紧）

不再扩张主链功能、不执行 git push、不替代用户完成最终人工测试。

对应冻结与后续收口目标来自：
- `docs/73-note-generation-detailed-solution.md`
- `docs/77-phased-implementation-and-task-breakdown.md`
- `docs/79-pre-implementation-control-freeze.md`
- `docs/81-final-delivery-and-release-prep-main.md`
- `docs/82-final-handoff-orchestration-plan.md`
- `docs/92-p0-fixes-main.md`
- `docs/93-p1-fixes-main.md`
- `docs/94-p2-ai-review-judgement-main.md`
- `docs/95-final-pre-handoff-ts-fix-and-rerun-main.md`

---

## 2. 最终达成能力摘要
当前代码基线已形成以下主能力：

### 2.1 笔记生成主链
1. `/api/v1/settings/ai` 已完成密钥脱敏，不再回显完整 API key。
2. embedding provider 已从“可配置”升级为“可在运行时发起 embeddings 请求”。
3. 已新增独立 `note_retrieval_service`，使用现有 Note 内容切片做初版检索。
4. note generation 主链已从五段扩展为六段：
   - ingest
   - extract
   - normalize
   - retrieve
   - generate
   - write
5. LLM 输入已显式注入：
   - 当前 UTC 时间
   - 来源元数据
   - normalized_text
   - retrieval_summary
   - retrieved_context
6. LLM 输出已升级为结构化结果，不再只接受纯 Markdown 字符串。
7. 已支持学科归一化、标题 `标题-YYYY-MM-DD-HHmm`、按学科目录写回。
8. Markdown/frontmatter/DB note 记录之间的标题、subject、relative_path 已做统一写回。
9. 已加入 image/pdf/audio 的业务质量门禁，区分技术成功与业务成功。
10. 已补充覆盖 embedding、retrieval、命名、质量门禁、设置脱敏、多来源生成的测试代码。

### 2.2 P0 / P1 / P2 收口能力
11. 最终主笔记正文已清理过程性污染内容，不再默认混入大段检索摘要/调试性文本。
12. 思维导图链路已补 mermaid sanitize 与前端隔离保护，单图渲染失败不再拖垮整页。
13. 生成页状态文案已与 job 状态联动，不再出现“已创建任务，生成0篇笔记”式误导反馈。
14. docx 链路已补日志定位与稳定性增强，失败时更容易给出精确根因。
15. artifact 与主笔记库已做分层展示，summary/mindmap 不再默认混入主笔记视图。
16. 主笔记生成完成后已具备异步派生 review card generation 任务能力。
17. review session 化方案已落地，复习时长统计不再长期卡 0。
18. 复习流程已支持 AI 判分建议与讲解，并保留用户确认/覆盖后落库的闭环。
19. 前端既有 TypeScript 构建阻塞已修复，前端全量 build 已恢复通过。
20. `review_card_generation` 已不再只是规则切片异步化，而是优先走 AI 生成卡片，并在失败/无可用结果时回退到规则切片。
21. 知识点总结页已补齐产物详情/预览链路，可从 summary 列表直接查看对应输出笔记内容。
22. 思维导图生成链已显著收紧 prompt、输入清洗与输出结构约束，导图内容混乱问题已针对性改善。

---

## 3. 分项交付汇总（SA-33 ~ SA-53）

### SA-33：settings 脱敏与配置契约修整
**目标**：修掉 `/settings/ai` 完整密钥回显，并保证 provider 契约兼容。

**已实现**：
- `backend/app/services/settings_admin_service.py`
  - 新增 `mask_api_key()`。
  - `upsert_ai_providers()` 支持：空字符串不覆盖旧 key；提供新 key 时覆盖旧值。
- `backend/app/api/v1/endpoints/settings.py`
  - GET/PUT `/api/v1/settings/ai` 返回 `api_key=""`、`api_key_masked`、`has_api_key`。
- `backend/app/schemas/settings_admin.py`
  - 新增 `api_key_masked`、`has_api_key` 读模型字段。
- `frontend/src/types/settings.ts`
- `frontend/src/pages/settings/settings-ai-page.tsx`
  - 前端读取脱敏结果时保留空编辑态，不把脱敏串误当真实 key 回传。

**代码证据**：
- `settings.py` 中序列化逻辑明确返回空 `api_key`，并单独暴露 `api_key_masked`、`has_api_key`。
- `test_ai_settings_update_preserves_old_key_and_replaces_when_new_key_provided` 覆盖保留旧 key / 新 key 替换场景。

**结论**：已达成。

---

### SA-34：embedding runtime + retrieval service
**目标**：接入 embedding 运行时调用，并新增独立 retrieval service。

**已实现**：
- `backend/app/integrations/openai_compatible.py`
  - 新增 `embed()`，调用 `/embeddings`。
  - 返回 `vectors`、`model_name`、`usage`。
- `backend/app/services/note_retrieval_service.py`
  - 独立检索服务，不把检索细节塞进 generation service。
  - 读取现有 Note，分块切片，计算相似度并排序。
  - 输出：`matched_note_ids`、`matched_paths`、`snippets`、`similarity_scores`、`provider_model`、`retrieval_context`。
- `backend/app/schemas/integrations.py`
  - 新增 `RetrievalMatch`、`NoteRetrievalResult`。

**测试/证据**：
- `backend/tests/test_embedding_retrieval.py`
  - 覆盖 embeddings endpoint 调用。
  - 覆盖 ranked matches、context 限长与 chunking。

**结论**：已达成。

---

### SA-35：主链 retrieve 接入 + 结构化生成输出
**目标**：把 retrieve 接到主链中，并把生成输出升级为结构化对象。

**已实现**：
- `backend/app/services/note_generation_service.py`
  - 在 normalize 后接入 `_retrieve_related_context()`。
  - job log 新增 `retrieve started` / `retrieve completed`。
  - `result_json.processed_assets[*].retrieval_summary` 已写回。
  - prompt 中显式注入时间、source metadata、retrieval_summary、retrieved_context。
  - `_parse_generation_result()` 强校验 JSON、`title`、`subject`、`markdown_body`。
- `backend/app/schemas/integrations.py`
  - 新增 `GeneratedNoteResult`。

**测试/证据**：
- `backend/tests/test_notes_ingestion.py::test_generate_note_and_query_apis`
  - 校验 job 阶段包含 `retrieve`。
  - 校验结果里带 `retrieval_summary`。
- 主链代码已明确从六段执行到 write。

**结论**：已达成。

---

### SA-36：学科分类、命名与路径写回
**目标**：落地 subject normalization、标题-日期-时间命名、学科目录落库。

**已实现**：
- `backend/app/services/note_naming_service.py`
  - 学科归一规则与别名映射。
  - 统一时间格式 `YYYY-MM-DD-HHmm`。
  - 路径清洗、非法字符处理、重名去重。
  - 默认目录：`notes/subjects/<学科>/...`。
- `backend/app/services/note_generation_service.py`
  - 使用 `NoteNamingService.resolve_note_naming()` 生成最终 title/subject/path。
  - Markdown frontmatter、DB `note.title`、`relative_path` 同步一致。

**测试/证据**：
- `backend/tests/test_notes_ingestion.py`
  - 校验 frontmatter 中存在 `subject_slug`、`relative_path`。
- 命名服务代码已明确拼接 `标题-YYYY-MM-DD-HHmm` 并处理重名。

**结论**：已达成。

---

### SA-37：质量门禁与真实回归
**目标**：纠正 image/pdf/audio 的低质量输入误判，并完成真实回归收口。

**已实现**：
- `backend/app/services/note_generation_service.py`
  - `_assess_extraction_quality()` 区分 `passed / warning / failed`。
  - 区分 `business_status = passed / degraded / failed`。
  - image/audio 低质量时 fail fast；audio 部分短文本可 degraded + warning；pdf placeholder 文本直接失败。
- `backend/tests/test_notes_ingestion.py`
  - `test_generate_note_image_low_quality_extraction_fails_quality_gate`
  - `test_generate_note_audio_low_quality_extraction_fails_quality_gate`
  - `test_generate_note_audio_quality_warning_is_carried_into_result`
  - `test_generate_note_pdf_placeholder_extraction_fails_quality_gate`
  - `test_assess_extraction_quality_distinguishes_business_statuses`

**当前可确认结论**：
- 质量门禁代码与单测已落地。
- `docs/81-final-delivery-and-release-prep-main.md` 明确记录“已加入 image/pdf/audio 质量门禁”。
- 最终运行环境下的多样本复核，仍应以最新 Docker 实例上的统一复测为准。

**结论**：
- 代码实现：已达成。
- 最终运行环境复核：待后续 Docker 重启与人工测试完成最终闭环。

---

### SA-39：retrieval 真实命中专项验真
**目标**：证明 retrieval 不只是空阶段执行，而是在已有候选笔记库上发生真实命中。

**当前已知情况**：
- `docs/80-retrieval-real-hit-validation-plan.md` 已定义验真口径：
  - `matched_count > 0`
  - `matched_paths` 非空
  - `retrieval_context_chars > 0`
  - 最终 note/frontmatter 含 retrieval 证据
- `docs/81-final-delivery-and-release-prep-main.md` 已将“已完成 retrieval 真命中专项验真”列为阶段摘要。
- 代码层面已具备产生上述证据的路径：
  - 检索服务返回 `matched_paths`、`matched_note_ids`、`retrieval_context`
  - note frontmatter 与 result_json 已写入 `retrieval_summary`

**本次收口视角说明**：
- 本轮文档更新未重新构造候选库并复跑 SA-39 专项样本。
- 因此本交付文档将 SA-39 视为“已有上游专项完成，当前代码承载能力存在，最终运行实例证据以专项验真与后续环境确认结果为准”。

**结论**：
- 代码承载能力：已具备。
- 本轮收口未追加复跑证据：保留为交接说明项。

---

### SA-44A / SA-44B / SA-44C：P0 收口
**目标**：清理笔记内容污染，并修复 mermaid / 思维导图渲染稳定性问题。

**已实现**：
- 最终主笔记正文不再默认混入大段 retrieval context、normalized_text、调试性过程文本。
- 思维导图产物链路已加入 mermaid sanitize，避免双重 fenced block。
- 前端 Mermaid 渲染失败已做组件级隔离，单图失败不再炸整页。
- 笔记生成页与笔记详情页不再被导图渲染异常连带拖垮。

**结论**：已达成。

---

### SA-45A / SA-45B / SA-45C / SA-45D / SA-45E：P1 收口
**目标**：完成生成状态反馈、docx 链路、artifact/笔记分层、异步复习卡片、复习时长统计修正。

**已实现**：
- 生成页 queued / running / completed / failed 文案已与任务状态联动。
- docx 失败链路已补日志定位与回归覆盖，复杂文档问题更易定界。
- 主笔记库与 summary / mindmap 等 artifact 已分层展示，不再默认混出。
- 主笔记生成完成后已支持异步派生 `review_card_generation` 任务。
- review session 相关模型与链路已补齐，`review_watch_seconds` 统计能力已修正。

**结论**：已达成。

---

### SA-46：P2 收口（复习时 AI 判分与讲解）
**目标**：在 review session 主流程中加入 AI judge / explanation，但不直接越过用户确认。

**已实现**：
- 用户可提交答案，而不是只点 Again/Hard/Good/Easy。
- 系统可返回 AI 评分建议与讲解。
- 用户可确认或覆盖评分，再写入 review log / 更新复习状态。
- AI judge 失败时保留可解释回退，不拖垮 review session 主流程。

**结论**：已达成。

---

### SA-47：前端既有 TS 构建阻塞修复
**目标**：清除最终交付前阻塞前端全量 build 的既有 TypeScript 错误。

**已实现**：
- 已修复 `frontend/src/pages/notes/notes-library-page.tsx` 中阻塞构建的类型错误。
- 前端全量 build 已恢复通过，为后续 Docker 重启与人工验收清除前置阻塞。

**结论**：已达成。

---

### SA-51：复习卡片生成链审计与修复
**目标**：确认并修复 `review_card_generation` 虽然有独立任务，但仍未真正使用 AI 生成卡片的问题。

**已实现**：
- `backend/app/services/review_service.py`
  - `execute_review_card_job()` 保持独立异步任务形态，并在 job log 中记录 review card generation 主链。
  - `bootstrap_cards()` 结果中新增 `generation_mode`、`ai_generated_knowledge_points`、`fallback_generated_knowledge_points`，可区分 AI 生成与规则回退。
  - `_extract_knowledge_points()` 已改为优先探测可用 LLM provider；可用时先走 AI 卡片生成，不可用、失败或返回空结果时再走规则回退。
  - job log 已补 `review card ai generation started/completed` 与 fallback 日志，便于证明是否真实走过 AI。

**测试/证据**：
- `backend/tests/test_review_artifacts.py`
  - `test_review_card_generation_uses_ai_when_llm_available`：校验 review job `result_json.generation_mode == "ai"`、AI 生成知识点数为 2，且 job log 包含 AI started/completed。
  - `test_review_card_generation_falls_back_without_llm`：校验无可用 LLM 时回落到 `fallback`。
  - `test_note_generation_creates_separate_review_card_job`：校验主笔记完成后仍保留独立 `review_card_generation` 派生任务链。

**结论**：已达成。当前可明确说明：复习卡片链路已不再只是异步包装的规则切片，而是“优先 AI、失败再回退”的最小可行实现。

---

### SA-52：知识点总结预览修复
**目标**：修复知识点总结没有预览的问题，使 summary 页面可以查看产物详情，而不只是列表。

**已实现**：
- `frontend/src/pages/review/review-summaries-page.tsx`
  - 新增 `selectedArtifactId` 选择态。
  - summary 列表点击后，可根据 `output_note_id` 触发 `notesApi.getNoteDetail()`。
  - 右侧详情区已接入 `NoteDetailRenderer`，可直接渲染 summary 输出笔记的 Markdown/安全 HTML。
- 生成成功后会自动选中新产物，列表与详情联动保持一致，不影响已有列表页能力。

**测试/证据**：
- `frontend/src/pages/review/review-summaries-page.test.tsx`
  - `renders existing summary artifact and previews note detail`：校验 summary 页面可展示产物、加载对应输出笔记详情并完成预览。
  - `blocks generation for viewer and still renders artifacts area`：校验只读用户下仍可查看产物区域。
  - `allows admin to generate summary for selected notes`：校验管理员生成总结的原有能力未回归损坏。

**结论**：已达成。

---

### SA-53：思维导图质量约束修复
**目标**：修复思维导图内容混乱问题，重点收紧 mindmap prompt、输入边界与输出结构，而不是只处理渲染。

**已实现**：
- `backend/app/services/artifact_service.py`
  - mindmap 生成 prompt 已显著加强：强制只输出 Mermaid `mindmap` 正文、单根节点、3-6 个一级分支、总节点数 12-24、节点文案简短、禁止元信息/附录/原始摘录/代码示例/序号大纲等噪声进入导图。
  - `_prepare_note_content_for_artifact()` 与 `_trim_for_mindmap_prompt()` 已用于裁剪输入，优先保留清洁正文，尽量剔除 frontmatter、代码块、原始摘录、引用噪声等干扰内容。
  - `_sanitize_mermaid_body()` 在既有 fence 清洗基础上继续规范第一行、缩进、编号节点等输出形态，减少模型散乱输出对最终导图的污染。

**测试/证据**：
- `backend/tests/test_review_artifacts.py`
  - `test_prepare_note_content_for_mindmap_removes_noise_sections`：校验 mindmap 输入预处理会去除 source_path、mermaid 代码块、原始提取摘录等噪声。
  - `test_trim_for_mindmap_prompt_prefers_clean_section_content`：校验 prompt 输入优先保留真正重点内容并忽略代码/元信息。
  - `test_sanitize_mermaid_body_removes_nested_fences`：校验输出清洗对嵌套 fence、解释性文本、编号节点具备修正能力。

**结论**：已达成。当前修复重点是“让导图更克制、更聚焦、更稳定”，剩余质量上限仍受真实 LLM 能力与原始笔记质量影响。

---

## 4. 当前关键文件清单

### 后端核心实现
- `backend/app/api/v1/endpoints/settings.py`
- `backend/app/integrations/openai_compatible.py`
- `backend/app/schemas/integrations.py`
- `backend/app/schemas/settings_admin.py`
- `backend/app/services/settings_admin_service.py`
- `backend/app/services/note_retrieval_service.py`
- `backend/app/services/note_generation_service.py`
- `backend/app/services/note_naming_service.py`

### 前端 / 复习 / 交互相关实现
- `frontend/src/pages/notes/notes-library-page.tsx`
- `frontend/src/pages/notes/notes-generate-page.tsx`
- `frontend/src/components/note-detail-renderer.tsx`
- `frontend/src/components/mermaid-renderer.tsx`
- `frontend/src/pages/review/review-session-page.tsx`
- `frontend/src/pages/review/review-summaries-page.tsx`
- `frontend/src/pages/review/review-mindmaps-page.tsx`
- `frontend/src/lib/review-api.ts`
- `frontend/src/lib/notes-api.ts`
- `backend/app/api/v1/endpoints/review.py`
- `backend/app/services/review_service.py`
- `backend/app/schemas/review.py`
- `backend/app/services/artifact_service.py`
- `backend/app/models/job.py`

### 测试文件
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

### 收口文档
- `docs/81-final-delivery-and-release-prep-main.md`
- `docs/82-final-handoff-orchestration-plan.md`
- `docs/83-final-delivery-summary.md`
- `docs/84-commit-preparation-notes.md`
- `docs/92-p0-fixes-main.md`
- `docs/93-p1-fixes-main.md`
- `docs/94-p2-ai-review-judgement-main.md`
- `docs/95-final-pre-handoff-ts-fix-and-rerun-main.md`

---

## 5. 测试与验真摘要

### 已有代码/测试覆盖可确认项
1. 设置页密钥脱敏与旧 key 保留/新 key 覆盖逻辑已具测试覆盖。
2. embeddings 运行时调用、返回向量、usage 字段已具测试覆盖。
3. retrieval service 排序、chunking、context 截断已具测试覆盖。
4. note generation 主链包含 retrieve 阶段已具测试覆盖。
5. result_json / frontmatter 包含 retrieval_summary 已具测试覆盖。
6. image/audio/pdf 质量门禁与 degraded/failed 区分已具测试覆盖。
7. text/markdown/docx 生成链已有测试覆盖。
8. P0 相关的笔记污染清理与 mermaid 渲染隔离已有实现与最小回归覆盖。
9. P1 相关的状态文案、artifact 分层、review session / review card 链路已有实现与最小回归覆盖。
10. P2 相关的 AI 判分建议与讲解主链已有实现与最小回归覆盖。
11. SA-47 所处理的前端 TypeScript 构建阻塞已清除，前端全量 build 已恢复通过。
12. SA-51 已补上 review card 真正走 AI 的测试与任务日志证据。
13. SA-52 已补上 summary 列表到详情预览链路的前端页面与测试覆盖。
14. SA-53 已补上 mindmap 输入清洗、prompt 收紧与输出规范化的测试覆盖。

### SA-54 收口阶段说明
本阶段文档收口以“当前最新代码状态与已记录验证结论同步”为主，不新增业务代码修改。

当前可确认的结论分层如下：
1. **代码能力已落地**：SA-33 ~ SA-53 覆盖的主链能力、P0/P1/P2 修复项与最新后测问题修复项均已进入当前代码基线。
2. **前端构建阻塞已解除**：`docs/95-final-pre-handoff-ts-fix-and-rerun-main.md` 对应的前置阻塞已由 SA-47 清除。
3. **最新三项后测问题已同步纳入交付结论**：包括 AI 复习卡片、summary 预览、mindmap 质量约束。
4. **最终运行实例健康确认仍待后续 Docker 重启**：本轮文档更新不替代后续标准运行流程下的最终环境复核。
5. **最终用户体验验收仍需人工完成**：不可由 agent 代替。

---

## 6. 已通过项 / 未通过项 / 阻塞项

### 已通过项
- `/settings/ai` 脱敏契约已落地。
- embedding runtime 已落地。
- 独立 retrieval service 已落地。
- 主链 retrieve 阶段已落地。
- LLM 结构化输出已落地。
- 学科归一化、标题时间命名、按学科目录写回已落地。
- retrieval_summary 已进入 result_json、frontmatter、Markdown 产物。
- image/pdf/audio 质量门禁已落地。
- P0：笔记内容污染清理已落地。
- P0：mermaid / 思维导图渲染稳定性修复已落地。
- P1：生成页状态文案与任务状态联动已落地。
- P1：docx 链路补强已落地。
- P1：artifact 与主笔记分层展示已落地。
- P1：异步复习卡片派生任务已落地。
- P1：review session 时长统计修正已落地。
- P2：复习时 AI 判分建议与讲解已落地。
- SA-47：前端全量 build 已恢复通过。
- SA-51：复习卡片生成链已具备“优先 AI、失败回退”能力，并可从 job log 与 result_json 明确辨识。
- SA-52：summary 页面产物预览/详情链路已恢复。
- SA-53：mindmap 生成约束已显著收紧，输入清洗与输出规范化已补齐。
- 交付收口文档与提交准备材料已同步到最新阶段。

### 未通过项
- 本轮文档更新未执行 Docker 标准流程重启后的整套环境复核。
- 本轮文档更新未替代用户完成最终人工验收。
- retrieval 真命中、低质量门禁、多来源生成等最终运行实例证据，仍应以最新 Docker 实例上的复核结果为准。

### 阻塞项
- 最终“可交给用户点击验证”的运行实例健康确认，依赖后续 Docker 普通流程重启完成。
- 最终人工验收仍依赖用户亲自完成，不可由 agent 代替。

---

## 7. 剩余风险
1. **运行环境一致性风险**
   - 当前文档已同步到最新代码状态，但最终实例级可交付结论仍依赖 Docker 重启后的统一环境复核。

2. **真实 provider 成本/稳定性风险**
   - embedding/LLM/OCR/STT/AI judge 均依赖真实 provider 时，速率限制、成本与返回格式波动仍需关注。

3. **学科分类与检索规模风险**
   - 当前 subject normalization 仍以别名映射为主；retrieval 仍是初版按 Note 切片检索，规模扩大后需继续关注准确率与性能。

4. **复杂 docx / 多模态质量波动风险**
   - docx、OCR、音频转写在复杂真实样本下仍可能受源文件质量与 provider 返回影响。

5. **最终验收闭环风险**
   - 虽然当前代码、文档、前端构建阻塞都已收口，但最终用户可见体验仍取决于后续 Docker 实例确认与用户人工测试。

---

## 8. 交接建议
1. 先按普通流程重启 Docker，并确认前后端可访问。
2. 在最新实例上执行最小交接验收：
   - 设置页检查 provider 配置脱敏是否正常
   - 文本类生成 1 次
   - 有历史候选笔记前提下执行 1 次 retrieval 真命中样本
   - image/pdf/audio 至少各抽 1 个样本验证质量门禁
   - review card generation 至少执行 1 次，并确认 job log 中存在 AI generation started/completed 或明确 fallback 原因
   - summary 页面至少选择 1 条产物，验证右侧详情预览正常渲染
   - mindmap 页面至少验证 1 条新产物，确认结构明显收敛、无大段噪声堆砌
   - review session 至少跑 1 次 AI 判分与讲解闭环
   - 检查 notes library / artifact 分层展示与生成页状态文案
3. 再由主 agent 向用户给出访问入口、测试清单和注意事项。
4. 最终提交前，按 `docs/84-commit-preparation-notes.md` 整理提交信息与文件范围。

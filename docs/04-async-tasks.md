# 04 异步任务架构

## 目标

上传解析、OCR、转写、笔记生成、向量化、RAG 索引、FSRS 排程、知识点总结、思维导图、数据库导入导出和 Obsidian 导出都必须走异步任务架构。

Web 请求只负责创建任务、查询任务和取消任务，不直接执行长耗时流程。

## 技术选型

- 队列：BullMQ。
- Broker：Redis。
- 任务状态主表：PostgreSQL `jobs`。
- 任务日志：PostgreSQL `job_logs`。
- Worker：独立 Node.js 进程。

BullMQ 负责分发、重试、并发和延迟任务。PostgreSQL 负责面向产品界面的可查询状态、审计和长期日志。

参考：<https://docs.bullmq.io/>

## 队列划分

### ingest

处理资料解析：

- 音频元数据读取。
- 视频音轨提取。
- PDF/PPT/DOCX 文本提取。
- 图片预处理。
- OCR/视觉理解任务拆分。
- 生成 `source_segments`。

### ai

处理 AI 生成：

- 语音转文字。
- OCR/多模态识别。
- 笔记生成。
- 标题生成。
- 复习卡片生成。
- AI 复习评分。
- 知识点总结。
- 思维导图生成。

### embedding

处理知识库：

- Markdown 清洗。
- 分块。
- Embedding 请求。
- pgvector 写入。
- 旧 chunk 清理。

### review

处理复习：

- 新卡初始化 FSRS。
- 到期统计。
- 复习评分写回。
- 用户复习报告。

### export

处理导出：

- Obsidian Markdown 导出。
- 单内容重新导出。
- 全量重新导出。
- 数据库导出。
- 数据库导入。

### maintenance

处理维护：

- 清理过期临时文件。
- 清理过期 session。
- 任务日志归档。

## 任务生命周期

```text
queued -> running -> succeeded
                  -> failed -> retrying -> running
                  -> cancelled
                  -> waiting_input
```

`waiting_input` 用于需要管理员选择来源、处理冲突、确认导入策略等场景。

## 统一任务字段

每个任务必须记录：

- 队列名。
- 任务名。
- 创建人。
- 输入参数摘要。
- 进度百分比。
- 当前阶段文案。
- 结果摘要。
- 错误信息。
- 重试次数。
- 开始与结束时间。

敏感数据不得写入任务日志，例如 API key、完整 Authorization header。

## 典型工作流

### 上传资料到笔记

1. 管理员上传文件。
2. Web 创建 `source_files`。
3. Web 创建 `ingest.parse_source` job。
4. Worker 解析文件并生成 `source_segments`。
5. 页面显示解析结果，管理员勾选来源片段。
6. Web 创建 `ai.generate_note` job。
7. Worker 调用笔记模型生成 Markdown。
8. Worker 写入 `notes` 和 `note_sources`。
9. Worker 创建后续任务：
   - `ai.generate_cards`
   - `embedding.index_note`
   - `export.export_note_to_obsidian`
10. 页面通过任务状态显示全链路完成情况。

### 笔记到复习

1. `ai.generate_cards` 读取新笔记。
2. 按最小记忆单元生成卡片。
3. 写入 `review_cards`。
4. 为每个用户或默认用户初始化 `fsrs_states`。
5. 创建 `review.recalculate_due_counts`。

### 手动知识点总结

1. 管理员选择笔记范围。
2. 输入可选额外提示词。
3. 创建 `ai.generate_knowledge_summary`。
4. Worker 检索并组装来源上下文。
5. 写入 `knowledge_summaries`。
6. 创建 `embedding.index_summary` 和 `export.export_summary_to_obsidian`。

### 手动思维导图

1. 管理员选择笔记范围。
2. 输入可选额外提示词。
3. 创建 `ai.generate_mind_map`。
4. Worker 生成 Markmap Markdown 和 Mermaid mindmap。
5. 写入 `mind_maps`。
6. 创建 `export.export_mind_map_to_obsidian`。

## 重试策略

- 网络类 AI 失败：指数退避，最多 3 次。
- 文件解析失败：不自动重试超过 1 次，避免重复消耗资源。
- Embedding 失败：按 chunk 粒度重试。
- Obsidian 导出失败：允许手动重试。
- 数据导入失败：默认不自动重试，必须人工确认。

## 取消策略

管理员可以取消：

- 等待中的任务。
- 正在运行但支持中断的任务。

取消后：

- job 标记为 `cancelled`。
- 已写入的中间结果保留，并标记状态。
- 不自动删除上传源文件。

## 进度事件

任务进度通过轮询或 Server-Sent Events 暴露：

- `GET /api/jobs/:id`
- `GET /api/jobs/:id/logs`
- `POST /api/jobs/:id/cancel`
- `POST /api/jobs/:id/retry`

## 并发建议

- `ingest`: 2-4。
- `ai`: 1-3，受 API 限速影响。
- `embedding`: 2-6，按批量请求。
- `review`: 4。
- `export`: 1-2，避免文件写冲突。
- `maintenance`: 1。

## 验收标准

- 任一长任务都可以在任务页看到状态。
- 任务失败时用户能看到可理解错误。
- 管理员能重试失败任务。
- 普通用户不能创建生成、导入、导出任务。
- 任务日志不包含 API key。


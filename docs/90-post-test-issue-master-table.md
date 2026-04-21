# 90-问题清单总表（总控定稿版）

| 编号 | 问题 | 现象确认 | 初步根因 | 涉及模块 | 参考仓库启发 | 建议迁移方案 | 优先级 | 是否需要现场日志 |
|---|---|---|---|---|---|---|---|---|
| 1 | 笔记内容不纯粹 | 已确认 | `_build_markdown()` 把 retrieval/extraction/warnings 等过程内容写进正文与 frontmatter | `backend/app/services/note_generation_service.py` | 成品笔记原则；内部过程不得进入正文 | 建立最终正文白名单，调试/检索信息移至 job/debug artifact | P0 | 否 |
| 2 | 生成页提示文案错误 | 已确认 | 前端把创建任务返回时的 `generated_note_ids.length` 当最终结果展示，未区分 queued/running/completed | `frontend/src/pages/notes/notes-generate-page.tsx`、jobs 相关 API | 状态推进应显式表达 | 建立 job status 到 UI 文案映射，并轮询任务状态 | P1 | 否 |
| 3 | docx 无法生成 | 部分确认 | 代码设计上支持，但真实样本可能复杂；也可能失败发生在 worker/provider/异步链 | `safe_file_service.py`、`file_types.py`、`note_generation_service.py`、worker | 输入先分类再稳定提取；原件保留、阶段清晰 | 增强 docx 提取与 extraction log；用真实失败样本补回归 | P1 | 是 |
| 4 | 思维导图预览失败 | 已确认 | mermaid 双重 fence；后端未 sanitize；前端失败隔离不足 | `artifact_service.py`、`review-mindmaps-page.tsx`、`mermaid-renderer.tsx` | artifact 应独立、可校验、失败不污染主链 | 后端生成后清洗/校验 mermaid，前端单图失败隔离 | P0 | 否 |
| 5 | 思维导图/知识点总结与笔记混放 | 已确认 | 存储部分分离，但展示层仍把多类型 note 混在一个库里 | `artifact_service.py`、`note_query_service.py`、`notes-library-page.tsx` | 资产分层原则 | 前端按 note_type 分区，summary/mindmap 走专页/专目录 | P1 | 否 |
| 6 | 复习卡片生成方式不对 | 已确认 | 当前是手工 bootstrap，不是“笔记完成后派生任务” | `review_service.py`、`review.py`、worker | 卡片是派生任务，独立落库并 scan | 增加 `review_card_generation` job，主笔记成功后异步触发 | P1 | 否 |
| 7 | 复习时长统计一直为 0 | 高可信确认 | 统计依赖页面事件或评分提交，缺 session/heartbeat，后台累计易长期不更新 | `review-session-page.tsx`、`notes-library-page.tsx`、`review_service.py` | 复习应 session 化，统计是一等能力 | 引入 review session start/heartbeat/finalize，统计以服务端事实源为准 | P1 | 是 |
| 8 | 复习时应有 AI 打分并讲解 | 已确认 | 当前只有人工 rating + FSRS，无 AI judge/explain 链 | `review-session-page.tsx`、`review.py`、`review_service.py` | 卡片需可短答、可判对错，再引入 AI judge | 新增 AI judge step：answer -> score suggestion -> explanation -> user confirm -> write log | P2 | 否 |

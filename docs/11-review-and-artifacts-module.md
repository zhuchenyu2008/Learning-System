# 11-后端复习与衍生产出模块实现细节文档

## 1. 模块目标
在现有 Note / SourceAsset / Job 基础上，实现：
- KnowledgePoint 抽取与存储
- FSRS ReviewCard 调度
- ReviewLog 写入与查询
- 知识点总结生成
- 思维导图生成
- 定时任务基础接口

## 2. 数据流
### 2.1 知识点抽取
Note -> 解析 Markdown 内容 -> 按标题/段落/AI 提炼生成 KnowledgePoint -> 可选 embedding 占位 -> 落库

### 2.2 复习卡生成
KnowledgePoint -> bootstrap ReviewCard -> 初始化 FSRS 状态 -> 计算 due_at

### 2.3 复习流程
review queue -> 用户评分 Again/Hard/Good/Easy -> 更新 FSRS 状态 -> 写入 ReviewLog -> 更新下一次 due_at

### 2.4 总结 / 思维导图
选择 note_ids / 全量范围 -> 聚合内容 -> 调用 LLM -> 输出 summary markdown 或 mermaid mindmap -> 写回 Note / GeneratedArtifact / Job

## 3. API 细节
### 3.1 Review
- `GET /api/v1/review/overview`
  - 返回今日到期数、总卡片数、最近复习统计
- `GET /api/v1/review/queue`
  - 参数：`limit`、`due_only`
- `POST /api/v1/review/cards/bootstrap`
  - 输入：`note_ids[]` 或 `all_notes=false/true`
- `POST /api/v1/review/session/{card_id}/grade`
  - 输入：`rating`, `duration_seconds`, `note`
- `GET /api/v1/review/logs`
- `POST /api/v1/review/logs`

### 3.2 Summaries
- `POST /api/v1/summaries/generate`
  - 输入：scope(manual|scheduled), note_ids, prompt_extra
- `GET /api/v1/summaries`

### 3.3 Mindmaps
- `POST /api/v1/mindmaps/generate`
  - 输入：scope(manual|scheduled), note_ids, prompt_extra
- `GET /api/v1/mindmaps`

## 4. 实现策略
- 首版 FSRS 使用稳定 Python 实现或轻量封装
- 若 embedding provider 未配置，则知识点仍可落库，只跳过向量化
- 总结与思维导图走 Job 主链；未接 Celery 时允许同步执行 + Job 状态流转
- Mermaid mindmap 输出以 markdown code fence 形式保存

## 5. 与前端约定
- review queue 返回足够展示卡片标题、原文摘要、来源 note
- summary/mindmap 列表返回生成时间、scope、关联 note 数、状态

## 6. 验收标准
- ReviewCard / ReviewLog / GeneratedArtifact 可落库
- review 主链可调用
- summary / mindmap 生成 job 可创建
- 基本测试覆盖主链

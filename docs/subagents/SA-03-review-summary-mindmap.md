# SA-03 复习/总结/思维导图任务单

## 目标
实现知识点、FSRS 复习卡、复习打分、复习日志、知识点总结、思维导图生成、定时任务基础。

## 必读文档
- docs/00-main-task.md
- docs/03-architecture.md
- docs/04-module-boundaries.md
- docs/05-api-and-data-contracts.md
- docs/06-implementation-plan.md
- docs/07-subagent-orchestration-plan.md

## 范围
- KnowledgePoint / ReviewCard / ReviewLog / GeneratedArtifact
- review overview / queue / grade / logs API
- summaries / mindmaps generate API
- Celery beat 定时任务基础
- FSRS 调度封装

## 不要做
- 不做前端

## 验收标准
- review 主链可调用
- summary / mindmap job 可创建
- review logs 可写入并查询

## 回传要求
- 改动文件列表
- 执行命令列表
- 通过项 / 未通过项 / 阻塞项

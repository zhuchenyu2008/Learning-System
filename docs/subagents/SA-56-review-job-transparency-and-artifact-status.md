# SA-56 Review jobs 透明度与 artifact 生成状态体验任务单

## 目标
1. 调查并修复 review card task `80b23505-e2fd-4837-80a7-85089e7c9e4f` 暴露出的日志透明度/执行链问题
2. 修复 summary / mindmap 生成时错误显示“输出笔记 #0（）”的问题，改为对齐 note generation 的状态体验

## 必读文档
- docs/101-post-manual-test-wave2-main.md
- docs/102-post-manual-test-wave2-requirements.md
- docs/103-post-manual-test-wave2-current-state.md
- docs/104-post-manual-test-wave2-architecture.md
- docs/105-post-manual-test-wave2-module-boundaries.md
- docs/106-post-manual-test-wave2-api-contracts.md
- docs/107-post-manual-test-wave2-implementation-plan.md
- docs/108-post-manual-test-wave2-subagent-orchestration-plan.md
- docs/109-post-manual-test-wave2-test-plan.md

## 重点范围
- backend review/job 相关服务与 endpoints
- frontend review summaries / mindmaps 生成状态展示
- 如有必要，调查指定任务日志/数据库记录

## 验收标准
- 能明确说明该 task 的现状与根因
- review card job 日志/result/status 透明度增强
- summary/mindmap 生成体验不再误报 `output_note_id=0`

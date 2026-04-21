# SA-52 知识点总结预览修复任务单

## 目标
修复知识点总结没有预览的问题，使 summary 页面能正常查看产物详情，而不只是列表。

## 必读文档
- docs/97-new-issues-wave-main.md
- docs/98-new-issues-breakdown.md
- docs/99-new-issues-orchestration.md

## 重点范围
- `frontend/src/pages/review/review-summaries-page.tsx`
- `frontend/src/lib/review-api.ts`
- `frontend/src/lib/notes-api.ts`
- 必要时关联 note detail 渲染组件

## 验收标准
- summary 页面可选中产物并看到预览/详情
- 不影响已有生成列表

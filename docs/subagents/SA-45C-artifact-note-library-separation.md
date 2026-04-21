# SA-45C artifact与笔记分组展示分离任务单

## 目标
让 summary / mindmap 不再默认混入主笔记库视图，建立更清晰的展示分层。

## 必读文档
- docs/90-post-test-issue-master-table.md
- docs/91-next-fix-wave-orchestration.md
- docs/93-p1-fixes-main.md

## 重点范围
- `backend/app/services/note_query_service.py`
- `frontend/src/pages/notes/notes-library-page.tsx`
- `frontend/src/types/notes.ts`
- 如有必要，相关过滤/分组接口最小范围

## 必做事项
1. 主笔记库默认不把 summary/mindmap 混出
2. 保持 summary/mindmap 可在其专页或专入口访问
3. 补最小前后端验证

## 不要做
- 不扩张到卡片任务和复习时长

## 验收标准
- 主笔记库分层清晰
- artifact 仍可访问

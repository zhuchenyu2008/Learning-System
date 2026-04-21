# SA-44B 思维导图mermaid渲染修复任务单

## 目标
修复思维导图生成后双重 mermaid fence 导致的渲染失败，并确保单图失败不会连带影响主页面。

## 必读文档
- docs/89-reference-benchmark-summary-and-fix-roadmap.md
- docs/90-post-test-issue-master-table.md
- docs/91-next-fix-wave-orchestration.md
- docs/92-p0-fixes-main.md

## 重点范围
- `backend/app/services/artifact_service.py`
- `frontend/src/pages/review/review-mindmaps-page.tsx`
- `frontend/src/components/mermaid-renderer.tsx`
- `frontend/src/components/note-detail-renderer.tsx`
- 与 mermaid 产物和渲染直接相关的最小测试范围

## 必做事项
1. 后端保存思维导图前做 mermaid sanitize，避免双重 fenced block
2. 前端渲染失败时只降级当前图块，不影响整页
3. 笔记页若含 mermaid 图块，失败时也应局部兜底
4. 补必要测试或最小验证证据

## 不要做
- 不扩张到 artifact 分组/目录策略
- 不扩张到 P1/P2 问题

## 验收标准
- 双重 ```mermaid 问题消失
- 思维导图页可正常预览或最小失败隔离
- 笔记生成页不再因 mindmap 渲染错误连带报错

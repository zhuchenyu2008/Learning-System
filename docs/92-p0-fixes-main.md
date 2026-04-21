# 92-P0修复主文档

## 1. 本轮范围
本轮只修 P0 两项：
1. 笔记内容污染清理
2. 思维导图双重 mermaid fence 与渲染失败修复

## 2. 修复目标
### 2.1 笔记内容污染清理
- 最终用户笔记不再包含大段检索上下文摘要、规范化文本摘录、调试性内容
- 最终 markdown 仅保留成品笔记所需结构
- 调试/检索/抽取信息保留在 job/result 或最小必要 metadata 中

### 2.2 思维导图渲染修复
- 后端对思维导图产物做 mermaid sanitize
- 避免双重 fenced block
- 前端 Mermaid 渲染失败时只影响当前图块
- 笔记生成页不再被 mindmap 渲染错误连带报错

## 3. 影响范围
- `backend/app/services/note_generation_service.py`
- `backend/app/services/artifact_service.py`
- `frontend/src/pages/review/review-mindmaps-page.tsx`
- `frontend/src/components/mermaid-renderer.tsx`
- `frontend/src/components/note-detail-renderer.tsx`
- 与上述直接相关的测试最小范围

## 4. 验收标准
1. 最终主笔记正文不再混入过程性检索/抽取内容
2. 思维导图产物不再出现双重 ```mermaid
3. 思维导图页面可预览，单图失败不炸全页
4. 笔记生成页不再因导图渲染错误连带报错

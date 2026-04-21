# SA-44A 笔记内容污染清理任务单

## 目标
清理最终主笔记中的过程性污染内容，确保用户看到的是成品笔记，而不是生成中间态与调试信息。

## 必读文档
- docs/89-reference-benchmark-summary-and-fix-roadmap.md
- docs/90-post-test-issue-master-table.md
- docs/91-next-fix-wave-orchestration.md
- docs/92-p0-fixes-main.md

## 重点范围
- `backend/app/services/note_generation_service.py`
- 与最终 markdown/frontmatter 组装直接相关的最小范围
- 必要时补对应后端测试

## 必做事项
1. 审核最终 markdown 组装逻辑，去除不应进入用户正文的部分
2. retrieval/extraction/normalized excerpt 等内部信息不得再作为正文主段落输出
3. 保留必要元数据，但控制为最小可接受范围
4. 补回归测试，验证污染内容不再进入最终主笔记

## 不要做
- 不改思维导图链路
- 不扩张到 P1/P2 问题

## 验收标准
- 最终用户笔记正文为成品内容
- 检索上下文摘要/规范化文本摘录等不再直接出现在正文中

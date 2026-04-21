# SA-29 PDF笔记生成质量排查任务单

## 目标
只针对 PDF 来源，排查为什么 AI 生成出来的笔记质量异常。

## 必读文档
- docs/60-note-generation-tail-fix.md
- docs/61-note-generation-pipeline-refactor.md
- docs/62-pdf-note-quality-investigation.md

## 范围
- 真实 Docker 环境下复现 PDF 上传 -> 生成 -> 查看 job/log/note
- 检查 PDF 提取文本、规范化文本、最终 Markdown
- 必要时做最小修复并回归

## 不要做
- 不扩展新功能
- 不顺手大改无关来源类型

## 验收标准
- 回传实际 PDF 链路证据
- 回传根因判断
- 如已修复，回传改动文件与验证结果

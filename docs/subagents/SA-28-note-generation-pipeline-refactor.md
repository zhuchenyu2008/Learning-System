# SA-28 AI笔记生成主链重构任务单

## 目标
按文档把 AI 生成笔记流程重构为“来源 -> 文本 -> 笔记”的统一主链。

## 必读文档
- docs/45-notes-upload-first.md
- docs/57-note-generation-500-followup.md
- docs/60-note-generation-tail-fix.md
- docs/61-note-generation-pipeline-refactor.md

## 范围
- 重构 notes 生成主链内部流程
- 明确 extraction / normalization / generation 三阶段
- 增强 Job 日志阶段性信息
- 保持现有 API 尽量兼容

## 不要做
- 不扩展新产品功能
- 不重构无关页面/接口

## 验收标准
- 三段式流程在代码与日志上清晰可见
- 至少 txt/md/docx 与一条多媒体来源链路通过

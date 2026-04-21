# SA-31 真实环境全来源测试任务单

## 目标
使用用户给定 SiliconFlow 配置，对当前 Docker 环境进行全来源端到端测试，并抽样检查笔记质量。

## 必读文档
- docs/63-note-generation-end-to-end-investigation-main.md
- docs/64-note-generation-end-to-end-requirements.md
- docs/65-note-generation-end-to-end-current-state.md
- docs/66-note-generation-end-to-end-architecture.md
- docs/68-note-generation-end-to-end-api-contracts.md
- docs/71-note-generation-end-to-end-test-plan.md
- docs/72-note-generation-end-to-end-runbook.md

## 范围
- 写入 llm / embedding / ocr / stt 配置
- 测 txt/md/docx/pdf/image/audio
- 抽样检查最终 note 质量、标题、目录、job 日志

## 输出
- 实际命令
- 实际 HTTP 结果
- 每类来源 through/failed
- 产物问题清单

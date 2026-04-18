# SA-02 资料导入与笔记生成任务单

## 目标
实现本地文件夹扫描、来源资产登记、资料导入作业、Markdown 笔记生成任务链、笔记列表/详情 API。

## 必读文档
- docs/00-main-task.md
- docs/03-architecture.md
- docs/04-module-boundaries.md
- docs/05-api-and-data-contracts.md
- docs/06-implementation-plan.md
- docs/07-subagent-orchestration-plan.md

## 范围
- SourceAsset / Note 数据模型补全
- sources scan API
- notes generate API
- job dispatch
- 文件安全写入服务
- OpenAI-compatible provider adapter（LLM/STT/OCR 基础封装）
- 笔记生成占位主链
- notes/tree、notes/list、notes/detail API

## 不要做
- 不做 FSRS 复习
- 不做前端

## 验收标准
- 可扫描工作目录中的文件
- 可登记资产
- 可创建生成任务并产出 markdown note
- 列表与详情 API 可用

## 回传要求
- 改动文件列表
- 执行命令列表
- 通过项 / 未通过项 / 阻塞项

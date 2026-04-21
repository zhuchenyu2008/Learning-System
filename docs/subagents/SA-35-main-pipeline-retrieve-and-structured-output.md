# SA-35 主链retrieve接入与结构化生成输出任务单

## 目标
把 retrieval 阶段正式接入 note generation 主链，并把生成输出从“纯 Markdown 字符串”升级为结构化结果，为后续学科分类与路径写回打基础。

## 必读文档
- docs/73-note-generation-detailed-solution.md
- docs/74-embedding-retrieval-detailed-design.md
- docs/75-prompt-time-and-output-structure-design.md
- docs/77-phased-implementation-and-task-breakdown.md
- docs/78-test-acceptance-and-risk-control-plan.md
- docs/79-pre-implementation-control-freeze.md

## 前置依赖
- SA-34 已完成并提供 embedding runtime + retrieval service

## 重点范围
- `backend/app/services/note_generation_service.py`
- `backend/app/schemas/integrations.py`
- 与 generation output parser / schema 校验直接相关的最小范围

## 必做事项
1. 主链从五段改为六段：
   - ingest
   - extract
   - normalize
   - retrieve
   - generate
   - write
2. Job 日志中增加 `retrieve` 阶段。
3. result_json 中增加 retrieval_summary。
4. LLM 输入显式包含：
   - 当前时间
   - 来源元数据
   - normalized_text
   - retrieved_context
5. LLM 输出升级为结构化结果，至少包含：
   - title
   - subject
   - markdown_body
   - warnings/confidence（可选）
6. 对解析失败/缺关键字段做校验与失败处理。

## 不要做
- 不完成最终路径/命名落库策略
- 不扩张无关前端页面

## 验收标准
- retrieve 阶段真实执行
- 日志可见 retrieve
- LLM 结果不再只是字符串
- 测试与最小真实验证通过

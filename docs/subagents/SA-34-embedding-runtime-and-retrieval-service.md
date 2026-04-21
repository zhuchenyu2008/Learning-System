# SA-34 embedding运行时与retrieval service任务单

## 目标
在不改最终命名/落库逻辑的前提下，先把 embedding provider 从“仅能配置”升级为“可在运行时真实调用”，并新增独立 retrieval service，形成 retrieval 的第一版能力。

## 必读文档
- docs/73-note-generation-detailed-solution.md
- docs/74-embedding-retrieval-detailed-design.md
- docs/77-phased-implementation-and-task-breakdown.md
- docs/78-test-acceptance-and-risk-control-plan.md
- docs/79-pre-implementation-control-freeze.md

## 重点范围
- `backend/app/integrations/openai_compatible.py`
- 新增 `backend/app/services/note_retrieval_service.py`（或等价命名）
- 与 retrieval result schema 直接相关的最小范围

## 必做事项
1. 在 provider adapter 中增加 embedding 运行时调用方法。
2. 独立新增 retrieval service，而不是把检索细节塞进 note generation service。
3. 初版检索数据源优先使用现有 Note 内容切片。
4. 输出 retrieval result，至少包含：
   - matched note ids
   - matched paths
   - snippets
   - scores
   - provider model
   - retrieval context
5. 补充必要测试。

## 不要做
- 不直接改 note generation 主链接线
- 不做最终标题/学科目录落库
- 不扩展无关 provider 类型

## 验收标准
- embedding 真实请求可发出
- retrieval service 可独立工作
- 单测/集成测试给出证据

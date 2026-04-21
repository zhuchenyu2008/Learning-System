# 74-embedding检索接入详细设计

## 1. 目标
将 embedding provider 从“仅可配置、可探活”的状态，升级为真正参与笔记生成主链的运行时能力。

## 2. 当前现状
当前已具备：
- `ProviderType.EMBEDDING`
- AI settings 可读写 embedding 配置
- provider probe 能测试 `/embeddings`

当前缺失：
- 运行时 embedding 调用方法
- retrieval service
- retrieval 数据源
- retrieve 阶段日志与结果摘要

## 3. 设计原则
1. embedding 调用与 LLM/OCR/STT 调用分离
2. retrieval 作为独立 service，不直接耦合在 note_generation_service 内部实现细节中
3. 检索失败要可观测，不能静默吞掉
4. 初版优先使用现有 Note 内容切片作为检索来源，避免一次性重建整套知识点向量库

## 4. 运行时接口设计

### 4.1 Provider Adapter 新增方法
文件：`backend/app/integrations/openai_compatible.py`

建议新增：
- `embed(self, texts: list[str] | str) -> EmbeddingResult`

输入：
- 单个文本或多个文本

输出建议：
- `vectors`
- `model_name`
- `raw_response`
- `usage`（可选）

## 5. Retrieval Service 设计
文件建议新增：
- `backend/app/services/note_retrieval_service.py`

### 5.1 输入
- `normalized_text`
- `source_metadata`
- `top_k`
- 检索策略参数（可选）

### 5.2 输出
- `query_text`
- `matched_note_ids`
- `matched_paths`
- `snippets`
- `similarity_scores`
- `provider_model`
- `retrieval_context`

## 6. 检索数据源设计

### 6.1 初版策略
优先使用 `Note` 记录与 Markdown 内容切片作为候选。

实现口径：
1. 从 `notes` 表读取已有 note 列表
2. 读取对应 Markdown 正文
3. 对正文做简单切片：
   - 按段落
   - 按标题块
   - 或定长字符窗口
4. 为候选切片生成 embedding
5. 与 query embedding 做相似度比较

### 6.2 二期策略
逐步迁移到：
- `KnowledgePoint` 向量化
- 专门 chunk 表
- 预计算 embedding 缓存

## 7. 索引策略

### 7.1 初版
- 小规模 note 库可接受“在线切片 + 在线 embedding + 在线相似度计算”
- 先追求闭环正确性，而不是极致性能

### 7.2 后续优化
- 引入向量缓存
- 增量更新 note embeddings
- 减少每次生成前重复为历史笔记做 embedding

## 8. Query 构造策略
query 不应无脑用全文。

建议构造方式：
- 取 normalized_text 前若干关键段
- 截断超长文本
- 附加来源类型与提取摘要

目标：
- 避免超长 query
- 保留主题表达能力

## 9. Retrieval Context 构造策略
注入 LLM 的不是原始 top-k 全量文本堆砌，而是裁剪后的上下文。

建议：
- 每条匹配仅保留标题、路径、片段摘要
- 总上下文长度限制在安全范围内
- 明确标记“以下是相关旧笔记摘录，仅作辅助参考”

## 10. 主链插入点
在 `NoteGenerationService` 中：
- `_normalize_extracted_text(...)` 之后
- `_generate_note_body(...)` 之前

新增阶段：
- `_retrieve_related_context(...)`

## 11. Job 日志要求
retrieve 阶段记录：
- normalized_chars
- matched_count
- top_paths
- provider_model
- retrieval_context_chars

失败时记录：
- provider missing
- embeddings call failed
- no candidate notes
- no meaningful matches

## 12. 风险与对策

### 风险 1：历史笔记太少或为空
对策：
- 允许 matched_count = 0
- 但要明确记录“检索已执行，无命中”

### 风险 2：在线 embedding 历史笔记性能差
对策：
- 初版先接受，二期再加缓存

### 风险 3：低质量 OCR/STT 文本污染检索
对策：
- 在 retrieve 前复用质量门禁
- 对过短/噪声文本降权或阻断

## 13. 验收标准
1. 主链出现 retrieve 阶段
2. 真实调用 embedding provider
3. result_json 有 retrieval_summary
4. LLM prompt 明确包含 retrieval_context
5. 无命中时也有明确日志，而不是静默跳过

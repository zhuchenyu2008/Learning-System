# 73-笔记生成全流程详细总体方案

## 1. 目标
将当前 `learning-system` 的 AI 笔记生成能力，从“来源提取文本后直接交给 LLM 生成”的简化链路，升级为严格符合用户要求的完整学习笔记生成系统：

1. 各类来源先转为可用纯文本
2. 每次生成前必须执行 embedding 检索相关笔记
3. 将当前时间、来源元数据、检索上下文、规范化文本一并交给 LLM
4. 由 LLM 输出：
   - 学科分类
   - 标题
   - 笔记正文
   - 路径建议 / 相对路径
5. 系统按“学科目录 + 标题-日期-时间”的规则写回笔记库

## 2. 当前问题回顾
基于已完成调查，当前系统存在以下核心偏差：

### 2.1 主链缺 retrieve 阶段
当前仅有：
- ingest
- extract
- normalize
- generate
- write

缺失：
- embedding 检索相关笔记
- retrieval context 注入
- retrieval 结果日志与结果摘要

### 2.2 生成结果过于简单
当前 LLM 生成阶段只返回 Markdown 字符串，不返回：
- subject
- title
- relative_path
- summary
- warnings

导致后续无法由生成结果驱动：
- 学科目录选择
- 标题命名
- 路径构建

### 2.3 路径策略错误
当前路径在生成前就固定：
- 默认 `notes/generated/<source_stem>.md`

这与用户要求冲突，因为正确策略应是：
- 先生成 subject/title
- 再构建最终路径

### 2.4 质量与业务成功未区分
目前“job completed”不等于“笔记符合业务质量要求”。
典型表现：
- PDF OCR 有文本但质量差，仍 completed
- image OCR 空文本，仍生成一篇“说明性 note”
- audio STT 对弱样本只输出无意义短句，仍 completed

因此需要区分：
- 技术链路成功
- 业务产物达标

## 3. 目标主链
最终统一为六阶段：

1. **ingest**
   - 获取 SourceAsset
   - 记录来源类型、来源路径、来源大小、任务上下文

2. **extract**
   - 文本类：txt / md / docx -> 解析文本
   - 图文类：pdf / image -> OCR / 多模态识别文本
   - 音频类：wav / mp3 等 -> STT 识别文本

3. **normalize**
   - 清洗换行、重复片段、明显页眉页脚、占位垃圾
   - 统一形成 `normalized_text`
   - 输出 `normalization_metadata`

4. **retrieve**
   - 使用 embedding 模型对 `normalized_text` 生成 query embedding
   - 从现有笔记库 / 知识点切片中检索相关内容
   - 输出 `retrieved_context`

5. **generate**
   - 向 LLM 注入：
     - 当前日期时间
     - 来源元数据
     - 规范化文本
     - 检索上下文
     - 学习笔记生成策略
   - LLM 输出结构化结果

6. **write**
   - 根据 LLM 生成的 `subject + title + datetime` 构建路径
   - 写入 Markdown
   - 写回 Note 记录与 frontmatter
   - 记录检索摘要与生成摘要

## 4. 各来源处理规则

### 4.1 纯文本来源
适用：
- txt
- md
- docx

流程：
- 解析文本
- normalize
- retrieve
- generate
- write

说明：
- 不需要 OCR/STT
- docx 应继续走解析路径，不应退化为二进制处理

### 4.2 PDF / 图片来源
适用：
- pdf
- png/jpg/webp 等图片

流程：
- OCR / 多模态识别文本
- normalize
- 质量门禁
- retrieve
- generate
- write

说明：
- 若识别结果为空、占位、明显低质量，应 fail fast 或降级标记
- “completed + 垃圾内容”不再视为成功

### 4.3 音频来源
适用：
- wav
- mp3
- 其他 STT 支持格式

流程：
- ASR / STT 转文本
- normalize
- 质量门禁
- retrieve
- generate
- write

说明：
- 对极短、纯噪声、空白音频，要有最小质量判断

## 5. 检索目标定义
检索必须明确“检索什么”，不能停留在抽象层。

### 5.1 候选检索对象
可选对象：
1. Note 全文
2. Note 摘要片段
3. KnowledgePoint 切片
4. 后续新增的 chunk 表

### 5.2 当前推荐策略
短期优先：
- 先使用 **现有 Note 内容切片** 作为检索对象
- 同时保留未来迁移到 `KnowledgePoint` 或 chunk 表的空间

原因：
- 当前仓库虽有 `KnowledgePoint.embedding_vector` 雏形，但未接入完整生成链
- 直接依赖 KnowledgePoint 会增加第一阶段实现复杂度
- 先从现有 Note 正文做切片，更容易快速建立端到端闭环

### 5.3 检索输出
每次 retrieve 至少产出：
- matched note ids
- matched paths
- snippets
- scores
- provider model
- final retrieval context text

## 6. 生成上下文设计
LLM 输入必须由系统显式构造，不依赖模型猜测。

### 6.1 必要上下文
- `current_datetime_utc`
- `current_datetime_local`（如后续需要）
- `source_type`
- `source_path`
- `source_name`
- `normalized_text`
- `retrieved_context`
- `retrieval_summary`
- `prompt_policy_version`

### 6.2 提示词策略
生成策略应参考用户指定的两份 skill，迁入以下原则：
- 面向学习与复习，而不是泛泛摘要
- 优先保留概念、结构、例子、结论、易错点、待复习点
- 对 OCR 噪声、不确定信息进行标注
- 输出适合 Obsidian 的结构化 Markdown
- 输出学科分类与标题建议

## 7. 生成输出设计
LLM 输出不能再只是纯字符串，必须结构化。

建议输出字段：
- `title`
- `subject`
- `subject_slug`
- `relative_path_suggestion`
- `markdown_body`
- `summary`
- `warnings`
- `confidence`

其中：
- `title` 用于用户可见标题
- `subject` 用于学科展示名
- `subject_slug` 用于路径规范化
- `relative_path_suggestion` 可由系统二次清洗后采用

## 8. 命名与目录规则

### 8.1 标题格式
最终文件标题采用：
- `标题-日期-时间`

建议系统固定格式：
- `标题-YYYY-MM-DD-HHmm`

原因：
- 避免模型自由输出各种日期格式
- 便于排序与路径稳定

### 8.2 学科目录
最终路径目标类似：
- `notes/subjects/数学/函数-2026-04-20-1040.md`
- `notes/subjects/英语/虚拟语气-2026-04-20-1041.md`

说明：
- 展示目录先用中文学科名
- 同时内部保留 slug 以防后续扩展

### 8.3 重名处理
- 同名同分钟重复时追加 `-2`、`-3`
- 不允许覆盖已有 note

## 9. 质量门禁策略

### 9.1 提取质量门禁
- placeholder 文本直接 fail
- 空文本直接 fail
- 极短无意义文本标记为低质量

### 9.2 检索质量门禁
- 无法完成 embedding 调用时，不应静默跳过
- 默认应明确记录为 retrieve failed 或降级策略

### 9.3 生成质量门禁
- 若 LLM 输出缺 title / subject / body 关键字段，应判为生成失败
- 不允许只回显 prompt/system prompt

## 10. 日志与可观测性
阶段应扩展为：
- ingest
- extract
- normalize
- retrieve
- generate
- write

每阶段至少记录：
- source_asset_id
- stage
- chars / matched_count / output_chars 等摘要
- 失败原因

`result_json` 至少新增：
- `retrieval_summary`
- `generation_summary`
- `subject`
- `relative_path`
- `quality_flags`

## 11. 实施顺序

### 阶段 A：配置与安全修整
- 修复 `/settings/ai` 回显完整密钥
- 确认 embedding/llm/ocr/stt 四类 provider 配置稳定

### 阶段 B：检索链接入
- 增加 embedding runtime 调用
- 增加 retrieval service
- 在主链中接入 retrieve 阶段

### 阶段 C：生成输出结构化
- 将 `_generate_note_body` 升级为返回结构化结果
- 接入 title/subject/path suggestion

### 阶段 D：命名与落库改造
- 按学科目录 + 标题-日期-时间落库
- 完成重名与路径清洗策略

### 阶段 E：质量门禁与回归
- 对 txt/md/docx/pdf/image/audio 全量回归
- 抽查最终笔记质量

## 12. 验收标准
满足以下条件，才视为本轮主链改造达标：
1. 每类来源都遵守“先转文本、再检索、再生成”
2. Job 日志中可见 retrieve 阶段
3. 生成结果包含 subject/title/path
4. 笔记按学科目录落库
5. 文件名符合 `标题-日期-时间`
6. 真实 SiliconFlow 配置下多来源测试通过
7. PDF/image/audio 不再以“completed 但明显无业务价值”的方式伪装成功

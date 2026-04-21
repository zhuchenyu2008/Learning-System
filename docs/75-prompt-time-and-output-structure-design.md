# 75-生成提示词、时间注入与输出结构详细设计

## 1. 目标
将当前“只输出 Markdown 正文”的生成方式，升级为“输出结构化学习笔记结果”，并在生成时显式注入当前时间、来源信息、检索上下文与学习笔记策略。

## 2. 当前问题
当前 prompt 缺：
- 当前时间日期
- retrieval context
- 学科分类要求
- 标题命名要求
- 输出结构契约

当前输出缺：
- title
- subject
- relative_path suggestion
- warnings/confidence

## 3. 输入上下文结构
建议生成上下文统一为：

### 3.1 时间上下文
- `current_datetime_utc`
- `current_date_utc`
- `current_time_utc`
- 如后续需要，可增加本地时区

### 3.2 来源上下文
- `source_asset_id`
- `source_type`
- `source_name`
- `source_path`
- `extraction_metadata`
- `normalization_metadata`

### 3.3 文本上下文
- `normalized_text`
- `normalized_text_excerpt`

### 3.4 检索上下文
- `retrieved_context`
- `matched note summaries`
- `matched paths`

### 3.5 生成策略上下文
- 笔记用途：学习/复习/回顾
- 输出格式：Obsidian Markdown
- 结构要求：概念、结构、例子、结论、易错点、待复习点

## 4. 生成 Prompt 组织原则

### 4.1 System Prompt 原则
system prompt 应承担：
- 角色定义：学习笔记整理助手
- 风格定义：适合 Obsidian 的学习笔记
- 质量约束：去噪、不乱猜、明确不确定性
- 输出契约：返回结构化结果

### 4.2 User Prompt 原则
user prompt 应承担：
- 当前时间信息
- 来源元数据
- 规范化文本
- 检索上下文
- 输出要求细节

## 5. 输出结构设计
建议 LLM 输出 JSON 或者严格结构化 Markdown+元数据对象，最推荐 JSON。

### 5.1 目标输出字段
- `title`
- `subject`
- `subject_slug`
- `summary`
- `markdown_body`
- `warnings`
- `confidence`

### 5.2 字段约束
#### title
- 不带日期时间后缀
- 由核心主题构成
- 长度适中
- 避免纯文件名复写

#### subject
- 用稳定中文学科名
- 例如：数学、英语、物理、化学、生物、历史、地理、政治、语文、计算机

#### subject_slug
- 用于路径规范化
- 可与 subject 一一映射

#### summary
- 1~3 句摘要
- 可用于检索摘要与列表展示

#### markdown_body
- 为最终主体内容
- 不再包含外层 YAML/frontmatter，由系统写入

#### warnings
- 标记 OCR 噪声高、STT 不确定、内容可能失真等风险

## 6. 标题与日期时间拼接策略
系统而非模型负责最终拼接：
- `final_title = {title}-{YYYY-MM-DD-HHmm}`

原因：
- 避免模型输出格式漂移
- 统一文件名风格
- 便于重名处理

## 7. Markdown 内容结构要求
建议最终正文至少具备：
- 摘要
- 核心内容/章节
- 关键概念/重点
- 示例或补充说明（如适用）
- 易错点/注意点（如适用）
- 待复习点/后续关注点（如适用）

## 8. 不确定性处理规则
若 OCR/STT 文本质量一般：
- 允许保守表达
- 明确写“以下部分可能存在识别误差”
- 不允许把明显噪声直接写成确定知识点

## 9. 风险与对策

### 风险 1：模型不稳定返回结构化结果
对策：
- 使用 JSON schema 约束
- 解析失败时进行严格校验并重试

### 风险 2：subject 不稳定
对策：
- 系统增加 subject 规范化映射
- 非法值回退到“未分类”

### 风险 3：title 太长或非法
对策：
- path builder 做清洗与截断

## 10. 验收标准
1. LLM 输入明确包含时间上下文
2. 输出为结构化结果而非纯 Markdown 字符串
3. 标题最终符合 `标题-日期-时间`
4. 输出中能体现学习笔记而不是泛摘要

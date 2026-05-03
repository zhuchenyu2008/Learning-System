# 05 AI 与 RAG

## 目标

AI 模块负责将多模态学习资料转化为笔记、卡片、总结、思维导图和问答结果。所有模型配置都由管理员填写，系统只提供 OpenAI 兼容的调用抽象和本地模型适配点。

## 模型配置

### 必填模型

管理员必须配置：

- 笔记生成模型。
- Embedding 模型。
- 语音转文字模型。

每项配置必须包含：

- API key。
- Base URL。
- 模型名称。

### 可选模型

- OCR/视觉理解模型。
- Reranker 模型。
- AI 评分模型。

OCR 不要求单独模型，可以使用多模态模型完成图片/PDF 扫描识别。

## OpenAI 兼容调用

模型配置按照 OpenAI API 习惯建模：

- 对话和生成参考 Responses API。
- 向量化参考 Embeddings API。
- 语音转文字参考 Audio Transcriptions API。

参考：

- OpenAI Responses: <https://platform.openai.com/docs/api-reference/responses>
- OpenAI Embeddings: <https://platform.openai.com/docs/api-reference/embeddings>
- OpenAI Audio Transcriptions: <https://platform.openai.com/docs/api-reference/audio/createTranscription>

系统必须允许 base URL 指向第三方 OpenAI 兼容服务，例如硅基流动、本地网关或自部署模型服务。

## 密钥安全

- API key 只在数据库中加密保存。
- 前端保存表单时只显示尾号，例如 `sk-...abcd`。
- 任务日志不得记录 key。
- 文档和示例文件不得提交真实 key。
- 连接测试只保存测试状态和错误摘要。

## 笔记生成流程

输入：

- 选中的 `source_segments`。
- 学科、课程时间、来源类型、管理员补充说明。
- 设置页中的笔记总结额外提示词。

输出：

- AI 生成标题。
- Markdown 正文。
- YAML 风格元数据。
- 关联笔记建议。
- 可生成卡片的候选知识点。

质量规则参考 `obsidian-study-notes`：

- 中文标题和中文路径。
- 成品笔记，不写 TODO。
- 首屏放最关键可复习信息。
- 数学默认使用 LaTeX。
- 关联旧笔记要少而准。
- 资料来源必须可追溯。

## 卡片生成规则

生成笔记后自动生成卡片：

- 一张卡只考一个判断点。
- 优先生成短、准、可判对错、对考试有价值的卡。
- 老师临时比喻、课堂聊天、过泛总结默认不出卡。
- 题面必须明确问“词义、分类、条件、判断依据、对应关系、结构”等哪一种。
- 卡片不写入笔记正文，单独存入 `review_cards`。

## RAG 索引

### 切块

索引来源：

- 笔记。
- 知识点总结。
- 思维导图摘要。
- 可选解析片段。

切块规则：

- 保留标题层级。
- 保留学科、类型、日期、来源。
- Markdown 表格和公式尽量不拆开。
- 每个 chunk 记录来源内容 ID 和位置。

### Embedding

Embedding 必须异步执行：

- 新笔记生成后创建索引任务。
- 内容更新后删除旧 chunk，再写入新 chunk。
- Embedding 模型未配置时，生成内容允许保存，但知识库索引任务失败并提示管理员配置模型。

### 检索

默认检索流程：

1. 查询向量化。
2. pgvector top-k 检索。
3. 按学科、内容类型、权限过滤。
4. 可选 rerank。
5. 组装上下文。
6. 调用问答模型。
7. 返回答案和引用。

## RAG 回答要求

- 答案必须引用来源。
- 找不到可靠来源时应说明“没有在当前笔记库中找到足够依据”。

## Markdown 渲染

前端必须支持：

- GFM。
- 受控 HTML。
- KaTeX。
- Mermaid。
- Markmap。

安全要求：

- HTML 使用白名单 sanitize。
- 禁止脚本、事件属性、外链 iframe。
- 数学公式渲染失败时保留原文。
- Mermaid 和 Markmap 渲染失败时显示错误块。

参考：

- KaTeX: <https://katex.org/docs/autorender>
- Mermaid mindmap: <https://mermaid.js.org/syntax/mindmap.html>
- Markmap: <https://markmap.js.org/>

## RAG 接口

### POST `/api/rag/query`

请求：

- `query`
- `subject?`
- `contentTypes?`
- `topK?`

响应：

- `answerMarkdown`
- `citations`
- `retrievedChunks`
- `jobId?`

长回答或流式回答可以使用 SSE。

## 验收标准

- 未填写必填模型时，相关页面给出明确配置提示。
- 管理员可以测试每个模型配置。
- 上传文本生成笔记后，RAG 能检索该笔记。
- RAG 回答包含引用。
- Markdown 中 HTML、LaTeX、Mermaid、Markmap 均能渲染。


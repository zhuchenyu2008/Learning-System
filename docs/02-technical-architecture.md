# 02 技术架构

## 技术选型

第一轮文档指定后续实现采用 Next.js 全栈：

- Web：Next.js App Router、React、TypeScript。
- 样式：Tailwind CSS 或 CSS Modules，配合自定义织物纹理 token。
- 数据库：PostgreSQL。
- 向量检索：pgvector。
- ORM：Drizzle ORM。
- 异步任务：BullMQ + Redis。
- 文件存储：本地 Docker volume 起步，接口抽象为可替换对象存储。
- AI SDK：OpenAI 兼容 HTTP 客户端，保留 provider adapter。
- Markdown 渲染：`react-markdown`、`remark-gfm`、`rehype-raw` 受控白名单、KaTeX、Mermaid、Markmap。
- 测试：Vitest、Playwright。
- 部署：Docker Compose。

NyaAI 可作为“一体化 AI 工作区、BYOK、多模型配置、知识库和 PWA 体验”的参考，但 Learning-System 不复制其协作平台定位。

## 运行进程

### Web 进程

职责：

- 服务 Next.js 页面。
- 处理认证、权限和短请求。
- 创建异步任务。
- 查询任务状态。
- 提供 Server Actions 或 REST API。

Web 进程不得直接执行长耗时 AI 生成、OCR、转写、导入导出等任务。

### Worker 进程

职责：

- 消费 BullMQ 队列。
- 执行资料解析、AI 生成、向量化、FSRS 统计、Obsidian 导出、数据库导入导出。
- 写入任务进度和任务日志。

Worker 可以水平扩展。不同队列可以配置不同并发。

### Scheduler 进程

职责：

- 注册周期维护任务。
- 触发 FSRS 到期统计、临时文件清理、过期 session 清理、任务日志归档等任务。

MVP 可将 Scheduler 合并到 Worker 进程，但文档和接口仍按独立职责设计。

## 数据流

```text
上传文件
  -> source_files
  -> ingest 队列解析
  -> source_segments
  -> 管理员勾选来源
  -> ai 队列生成笔记
  -> notes
  -> ai 队列生成 cards
  -> review_cards + fsrs_states
  -> embedding 队列切块向量化
  -> rag_chunks
  -> export 队列导出 Markdown
  -> Obsidian export folder
```

## 模块边界

### Ingestion

处理文件上传和解析：

- 音频提取。
- 视频音轨提取与关键帧抽取。
- PDF/PPT/DOCX 文本解析。
- 图片 OCR 或视觉理解。
- 纯文本规范化。

### AI Generation

处理 AI 任务：

- 笔记生成。
- 复习卡片生成。
- RAG 回答。
- AI 评分。
- 知识点总结。
- 思维导图。
- 标题生成。

### Knowledge Base

处理知识库：

- Markdown 切块。
- 元数据抽取。
- Embedding。
- pgvector 检索。
- RAG 引用来源。

### Review

处理复习：

- 卡片生成质量规则。
- FSRS 调度。
- 到期统计。
- 答案评分。
- 复习日志。

### Export

处理导出：

- Markdown 文件生成。
- Obsidian 目录结构。
- 文件名冲突处理。
- 导出状态回写。
- 数据库备份导出。

## API 风格

后续实现可以混用 Server Actions 和 REST API，但必须遵守：

- 页面内部表单优先 Server Actions。
- 文件上传、任务状态、RAG streaming、导入导出优先 REST API。
- 所有写接口必须进行角色校验。
- 所有长任务写接口只创建 job，不同步等待任务完成。

## 外部参考

- NyaAI GitHub: <https://github.com/NitroRCr/nyaai>
- BullMQ 文档: <https://docs.bullmq.io/>
- Drizzle ORM: <https://orm.drizzle.team/>
- pgvector: <https://github.com/pgvector/pgvector>


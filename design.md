# Learning-System Design

## 1. 项目定位

Learning-System 是一个面向课堂学习资料沉淀的 Web 系统。它把录音、视频、图片、PPT、PDF、文本等上课资料转化为可复习、可检索、可导出的学习知识库。

系统核心闭环：

```text
上传资料
  -> 解析资料
  -> 生成 Markdown 笔记
  -> 生成复习卡片
  -> FSRS 复习调度
  -> RAG 问答
  -> 知识点总结
  -> 思维导图
  -> Obsidian Markdown 导出
```

第一轮交付以中文设计文档为主，不包含应用代码、数据库迁移或 Docker 配置文件。

## 2. 设计目标

- 建立完整学习闭环，而不是只做笔记生成工具。
- 数据库作为唯一主存储，Obsidian 文件仅作为自动导出的阅读副本。
- 支持多来源课堂资料解析，并保留来源追溯关系。
- 支持管理员配置 OpenAI 兼容模型，不在仓库中提交真实 API key。
- 使用 FSRS 作为复习调度算法，不使用 SM-2。
- 所有长耗时任务进入异步队列，Web 请求只负责创建任务和查询状态。
- 普通用户和管理员使用同一套界面，不可用能力以禁用态展示并由后端强校验。

## 3. 用户角色

### 管理员

管理员拥有全部系统能力：

- 上传和解析课堂资料。
- 勾选来源并触发笔记生成。
- 编辑、删除、重新生成笔记、卡片、总结和思维导图。
- 配置 AI、Embedding、语音转写、OCR/视觉理解、Obsidian 导出和注册策略。
- 执行数据库导入导出。
- 查看任务日志、系统日志、用户登录情况、观看时长和复习数据。

### 普通用户

普通用户是学习资料的观看者和复习参与者：

- 查看笔记、知识点总结、思维导图。
- 使用 RAG 问答。
- 进行复习并写入自己的复习日志。
- 标记坏卡反馈。

普通用户不能上传、生成、编辑、删除、配置系统、导入导出数据或查看其他用户日志。

## 4. 信息架构

桌面端使用固定左侧树状导航，只有三个一级模块：

```text
学习
  - 总览
  - 笔记生成
  - 笔记库
  - RAG 问答

复习
  - 总览
  - 复习
  - 知识点总结
  - 思维导图生成

设置
  - AI 配置
  - Obsidian 配置
  - 用户与权限
  - 数据导入导出
  - 任务与系统日志
```

桌面端左侧栏只承担全局导航，页面业务区保持单一主工作区，不采用左、中、右三栏工作台。上下文信息放入顶部状态带、下方详情区、标签页、折叠区或抽屉。

移动端使用顶部模块切换、抽屉式导航或底部一级导航作为补充入口，页面主工作区保持单列。

## 5. 技术架构

后续实现采用 Next.js 全栈方案：

- Web：Next.js App Router、React、TypeScript。
- 样式：Tailwind CSS 或 CSS Modules，配合自定义织物纹理 token。
- 数据库：PostgreSQL。
- 向量检索：pgvector。
- ORM：Drizzle ORM。
- 异步任务：BullMQ + Redis。
- 文件存储：本地 Docker volume 起步，抽象为可替换对象存储。
- AI 调用：OpenAI 兼容 HTTP 客户端，保留 provider adapter。
- Markdown 渲染：`react-markdown`、`remark-gfm`、受控 `rehype-raw`、KaTeX、Mermaid、Markmap。
- 测试：Vitest、Playwright。
- 部署：Docker Compose。

### 运行进程

```text
Web
  - 服务页面
  - 处理认证和权限
  - 创建异步任务
  - 查询任务状态
  - 提供 Server Actions / REST API

Worker
  - 消费 BullMQ 队列
  - 执行解析、AI 生成、向量化、导出、导入导出等长任务
  - 写入任务进度和任务日志

Scheduler
  - 触发周期维护任务
  - 统计 FSRS 到期数据
  - 清理临时文件、过期 session、归档任务日志
```

MVP 中 Scheduler 可以合并到 Worker 进程，但职责边界保持独立。

## 6. 核心数据流

```text
source_files
  -> ingest 队列解析
  -> source_segments
  -> 管理员勾选来源片段
  -> ai 队列生成 notes
  -> ai 队列生成 review_cards
  -> fsrs_states 初始化
  -> embedding 队列生成 rag_chunks
  -> export 队列导出 Markdown
  -> Obsidian export folder
```

关键数据对象：

- `users`、`sessions`：用户、认证和会话。
- `ai_model_configs`：各用途模型配置，API key 加密保存。
- `source_files`、`source_segments`：上传源文件和解析片段。
- `notes`、`note_sources`、`note_links`：笔记、来源和关联笔记。
- `review_cards`、`fsrs_states`、`review_logs`：卡片、用户级 FSRS 状态和复习日志。
- `rag_chunks`、`rag_queries`：知识库切块和问答记录。
- `knowledge_summaries`、`mind_maps`：总结和思维导图。
- `jobs`、`job_logs`、`audit_logs`：异步任务、任务日志和审计日志。

## 7. 模块设计

### 7.1 资料解析

Ingestion 模块处理多类型来源：

- 音频转写。
- 视频音轨提取和关键帧抽取。
- PDF、PPT、DOCX 文本解析。
- 图片 OCR 或视觉理解。
- 纯文本规范化。

解析结果写入 `source_segments`，管理员在生成笔记前勾选具体片段，确保生成内容可追溯。

### 7.2 AI 生成

AI Generation 模块负责：

- 课堂笔记生成。
- 复习卡片生成。
- 知识点总结。
- 思维导图。
- RAG 回答。
- 复习答案评分。
- AI 标题生成。

所有模型由管理员在设置页配置。系统按照 OpenAI API 习惯建模，允许 base URL 指向第三方 OpenAI 兼容服务、本地网关或自部署服务。

### 7.3 知识库与 RAG

知识库以 Markdown 内容为主：

- 对笔记、总结、思维导图摘要和可选来源片段切块。
- 切块时保留标题层级、学科、类型、日期和来源。
- Markdown 表格、公式尽量不拆开。
- Embedding 异步执行，并写入 pgvector。

RAG 默认流程：

```text
用户提问
  -> 查询向量化
  -> pgvector top-k 检索
  -> 权限和学科过滤
  -> 可选 rerank
  -> 组装上下文
  -> 调用问答模型
  -> 返回答案、引用和相关片段
```

回答必须包含引用。找不到可靠来源时，应明确说明当前笔记库中没有足够依据。

### 7.4 FSRS 复习

复习模块把笔记中的知识点转成可抽查卡片，并为每个用户维护独立 FSRS 状态。

复习流程：

```text
读取当前用户到期卡片
  -> 用户作答
  -> AI 给出评分建议
  -> 用户确认 AI 建议 rating 或再次作答
  -> 写入 review_logs
  -> 更新 fsrs_states
  -> 展示下一张卡
```

评分映射：

- 完全忘记或答非所问：`again`
- 有方向但关键点错误：`hard`
- 基本正确但有小缺漏：`good`
- 完全正确且表达清楚：`easy`

用户不直接手动选择 Again/Hard/Good/Easy，评分由 AI 根据答案建议，用户只能确认评分或再次作答。坏卡可以被普通用户反馈，管理员可编辑、合并或删除卡片。删除卡片不删除来源笔记，历史复习日志保留。

### 7.5 Obsidian 导出

数据库是主存储，Obsidian 是导出目标。系统只负责写入本地导出目录，不实现 Obsidian Sync 协议。

导出结构：

```text
<导出根目录>/
  <学科>/
    笔记/
    知识点总结/
    思维导图/
```

文件命名规则：

```text
<AI标题> YYYY-MM-DD HH-mm.md
```

导出内容包含 YAML frontmatter，记录内容 ID、类型、学科、来源、创建时间和更新时间。上传源文件不得进入 Obsidian 自动导出目录。

## 8. 权限与安全

系统采用管理员和普通用户两级角色。

安全要求：

- 所有写接口校验登录、角色和输入 schema。
- 普通用户不可用功能前端禁用，但后端仍必须拒绝越权请求。
- 密码使用强哈希。
- Session token 只保存哈希。
- API key 加密存储，前端只展示尾号。
- 日志、任务错误、导出包和页面源码不得包含明文 API key。
- 关键写入操作记录审计日志。

必须记录的审计事件包括登录成功和失败、用户创建和角色变更、内容创建编辑删除、AI 配置修改、Obsidian 配置修改、导入导出、任务重试和取消。

## 9. UI 设计原则

视觉采用“织物质感”：

- 背景使用浅亚麻、帆布、牛仔等织线纹理。
- 主色为温和中性色，少量点缀色用于 CTA、状态和高亮。
- 文字保持高对比，避免纹理影响阅读。
- 边框可以使用缝线、低透明度高光或柔和阴影。
- 重要 CTA 使用布标式按钮。
- Hover 提升高光和阴影，Active 轻微下沉。
- 动效控制在 180-260ms。
- 卡片圆角不超过 8px，不做页面区域的层层嵌套卡片。

Markdown 渲染需要支持 GFM、受控 HTML、KaTeX、Mermaid、Markmap、代码块、表格、引用、任务列表、图片和附件引用。

## 10. API 设计原则

后续实现可混用 Server Actions 和 REST API：

- 页面内部普通表单优先 Server Actions。
- 文件上传、任务状态、RAG streaming、导入导出优先 REST API。
- 长任务写接口只创建 job，不同步等待任务完成。
- 所有写接口都需要权限校验和审计记录。

示例接口：

- `POST /api/sources/upload`
- `POST /api/notes/generate`
- `GET /api/jobs/:id`
- `POST /api/rag/query`
- `GET /api/review/due`
- `POST /api/review/answer`
- `POST /api/review/cards/:id/rating`
- `POST /api/export/obsidian/rebuild`
- `POST /api/admin/data/export`
- `POST /api/admin/data/import`

## 11. Docker 部署

Docker Compose 应包含：

- `web`：Next.js Web 服务。
- `worker`：BullMQ Worker。
- `scheduler`：周期任务服务，MVP 可与 worker 合并。
- `postgres`：PostgreSQL + pgvector。
- `redis`：BullMQ broker。
- `storage`：本地 volume，不一定是独立服务。

建议 volume：

- `postgres_data`
- `redis_data`
- `uploads_data`
- `exports_data`
- `backups_data`

上传源文件和导出文件必须分离。若要导出到宿主机 Obsidian Vault，需要在 compose 中显式挂载宿主机目录到容器导出目录。

## 12. 验收标准

第一轮文档验收：

- `docs/` 下存在核心文档和页面文档。
- 每个页面文档包含目标用户、入口、布局、权限、交互、接口、异步任务、异常状态和验收标准。
- 文档明确数据库是唯一主存储。
- 文档明确上传源文件不进入 Obsidian 自动导出目录。
- 文档明确使用 FSRS，不使用 SM-2。
- 文档明确异步任务架构。
- 文档明确 Docker 部署方式。

后续实现验收：

- 管理员能上传资料并生成笔记。
- 笔记生成后自动生成卡片、向量索引和 Obsidian 导出任务。
- RAG 问答能返回引用来源。
- 每个用户拥有独立 FSRS 复习状态。
- 普通用户可查看、问答、复习，但不能执行管理写操作。
- API key 不出现在日志、页面源码和导出包中。
- Docker Compose 能启动 Web、Worker、Postgres 和 Redis。

## 13. 详细文档索引

- [产品需求](docs/00-product-requirements.md)
- [信息架构](docs/01-information-architecture.md)
- [技术架构](docs/02-technical-architecture.md)
- [数据模型](docs/03-data-model.md)
- [异步任务架构](docs/04-async-tasks.md)
- [AI 与 RAG](docs/05-ai-rag.md)
- [FSRS 复习](docs/06-fsrs-review.md)
- [Obsidian 导出与同步](docs/07-obsidian-export-sync.md)
- [安全、认证与权限](docs/08-security-rbac.md)
- [Docker 部署](docs/09-docker-deployment.md)
- [测试与验收](docs/10-testing-acceptance.md)

# Learning-System 文档索引

本目录是 Learning-System 第一轮交付物：只产出详细中文文档，不包含应用代码、数据库迁移或 Docker 配置文件。

产品定位是一个学习闭环系统：

1. 上传课堂录音、视频、图片、PPT、PDF、纸质资料照片、文本等来源。
2. 通过转写、OCR、文档解析和 AI 整理生成 Markdown 课堂笔记。
3. 自动生成复习卡片，并用 FSRS 安排下一次复习。
4. 基于笔记知识库进行 RAG 问答。
5. 对单篇或多篇笔记生成知识点总结和思维导图。
6. 将数据库中的生成内容自动导出为 Obsidian 友好的 Markdown 文件。

## 文档结构

### 核心文档

- [00 产品需求](00-product-requirements.md)
- [01 信息架构](01-information-architecture.md)
- [02 技术架构](02-technical-architecture.md)
- [03 数据模型](03-data-model.md)
- [04 异步任务架构](04-async-tasks.md)
- [05 AI 与 RAG](05-ai-rag.md)
- [06 FSRS 复习](06-fsrs-review.md)
- [07 Obsidian 导出与同步](07-obsidian-export-sync.md)
- [08 安全、认证与权限](08-security-rbac.md)
- [09 Docker 部署](09-docker-deployment.md)
- [10 测试与验收](10-testing-acceptance.md)

### 页面文档

- [笔记 - 总览](pages/notes-overview.md)
- [笔记 - 笔记生成](pages/notes-generation.md)
- [笔记 - RAG 问答](pages/notes-rag-qa.md)
- [笔记 - 笔记库](pages/notes-library.md)
- [复习 - 总览](pages/review-overview.md)
- [复习 - 复习](pages/review-session.md)
- [复习 - 知识点总结](pages/review-knowledge-summary.md)
- [复习 - 思维导图生成](pages/review-mind-map.md)
- [设置 - AI 配置](pages/settings-ai.md)
- [设置 - Obsidian 配置](pages/settings-obsidian.md)
- [设置 - 用户与权限](pages/settings-users-rbac.md)
- [设置 - 数据导入导出](pages/settings-data-portability.md)
- [设置 - 任务与系统日志](pages/settings-tasks-logs.md)

## 全局约定

- 第一轮只创建文档。
- 技术方向采用 Next.js 全栈：Next.js App Router、TypeScript、PostgreSQL、pgvector、Redis、BullMQ、Drizzle ORM、Docker Compose。
- 数据库是唯一主存储。Obsidian 文件夹只作为自动导出的副本，不作为业务数据源。
- 上传源文件不放入自动导出目录。
- AI 配置由管理员在设置页填写，文档和示例文件不得提交真实 API key。
- 普通用户只负责观看、问答、复习和写入复习日志；管理员负责上传、生成、编辑、删除、配置和用户管理。


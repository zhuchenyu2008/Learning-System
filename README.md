# Learning-System

Learning-System 是一个从课堂资料到笔记、RAG 问答、FSRS 复习、知识点总结、思维导图和 Obsidian 导出的学习闭环系统。

当前阶段已创建单包 Next.js App Router 基础工程，并接入 PostgreSQL + Drizzle ORM 数据库基础设施。此阶段只包含项目脚手架、环境变量模板、基础健康检查 API、数据库健康检查 API、初始数据库 schema、迁移命令和质量命令，不包含业务页面、AI/RAG、权限 UI、Docker Compose、文件扫描或 Markdown 处理。

## 文档

请从 [docs/README.md](docs/README.md) 开始阅读产品、架构和验收文档。

## 环境准备

要求 Node.js 20.9 或更高版本。

```bash
npm install
```

复制环境变量模板：

```bash
cp .env.example .env.local
```

`.env.example` 中包含后续阶段预留变量。第二阶段开始，数据库命令和数据库健康检查需要配置 `DATABASE_URL`。不要把真实 API Key、生产数据库密码或本机私有路径提交到仓库。

## 数据库配置

本项目使用 PostgreSQL 作为唯一主存储，使用 Drizzle ORM 管理 schema 和迁移。请在 `.env.local` 中配置真实数据库连接串：

```bash
DATABASE_URL=postgres://learning:learning@localhost:5432/learning
```

`DATABASE_URL` 只应放在本地环境文件或部署平台密钥中，不要写入源码、README 示例以外的配置或日志。

常用数据库命令：

```bash
npm run db:generate
npm run db:migrate
npm run db:studio
```

- `db:generate` 根据 `src/server/db/schema.ts` 生成迁移文件。
- `db:migrate` 将 `drizzle/` 下的迁移应用到 PostgreSQL。
- `db:studio` 打开 Drizzle Studio，用于本地查看数据库。

这些命令需要 `DATABASE_URL`，但常规质量命令不要求数据库在线。

## 本地启动

```bash
npm run dev
```

启动后访问：

- 应用占位页：<http://localhost:3000>
- 健康检查：<http://localhost:3000/api/health>
- 数据库健康检查：<http://localhost:3000/api/health/db>

基础健康检查只返回安全字段，不连接数据库或 Redis。数据库健康检查只执行数据库连接检查：连接成功返回 200，失败或缺少 `DATABASE_URL` 返回 503；响应不会返回连接串、用户名、密码、host、绝对路径、错误堆栈或完整数据库错误对象。

## 质量命令

每次修改后运行：

```bash
npm run lint
npm run typecheck
npm run test
npm run build
```

## 当前阶段边界

- 不实现业务页面。
- 不实现 AI/RAG。
- 只实现数据库基础设施，不实现业务 CRUD。
- 不实现登录、注册、权限 UI、Redis、BullMQ、Docker Compose。
- 不实现文件扫描或 Markdown 处理。
- `src/worker/` 和 `src/scheduler/` 仅为占位骨架。

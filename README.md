# Learning-System

Learning-System 是一个从课堂资料到笔记、RAG 问答、FSRS 复习、知识点总结、思维导图和 Obsidian 导出的学习闭环系统。

当前阶段已创建单包 Next.js App Router 基础工程，并接入 PostgreSQL + Drizzle ORM 数据库基础设施。第二阶段增加了服务器本地 Markdown 知识库根目录的环境变量读取、目录安全校验、只读配置状态 API、只校验不保存 API，以及最小设置页占位。当前仍不包含数据库业务 CRUD、AI/RAG、完整权限 UI、Docker Compose、文件扫描或 Markdown 处理。

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

## 本地知识库目录配置

第二阶段支持从服务器环境变量读取默认 Markdown 知识库根目录。可在 `.env.local` 中配置其中一个变量：

```bash
KNOWLEDGE_BASE_DIR=/path/to/markdown-vault
# 或
VAULT_ROOT=/path/to/markdown-vault
```

优先级为 `KNOWLEDGE_BASE_DIR`，其次为 `VAULT_ROOT`。仓库示例文件不包含真实本机路径。

当前实现只做目录校验，不保存配置、不连接数据库、不扫描 Markdown、不写入、移动或删除用户文件。API 响应不会向前端返回服务器绝对路径，只返回是否可用、配置来源、脱敏目录名、错误码和安全提示文本。

目录配置接口：

- `GET /api/settings/storage`：返回当前环境变量目录配置状态。
- `POST /api/settings/storage/validate`：请求体为 `{ "path": "/path/to/vault" }`，仅校验输入目录，不保存。

校验规则：

- 路径不能为空。
- 路径必须存在。
- 路径必须是目录。
- 当前进程必须有读取权限。
- 不向前端返回绝对路径或底层错误详情。

## 本地启动

```bash
npm run dev
```

启动后访问：

- 应用占位页：<http://localhost:3000>
- 健康检查：<http://localhost:3000/api/health>
- 数据库健康检查：<http://localhost:3000/api/health/db>
- 本地知识库目录设置占位页：<http://localhost:3000/settings/storage>
- 本地知识库目录状态：<http://localhost:3000/api/settings/storage>

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
- 只实现数据库基础设施和本地知识库目录只读校验，不实现业务 CRUD。
- 不实现登录、注册、权限 UI、Redis、BullMQ、Docker Compose。
- 不实现文件扫描、Markdown 处理或用户文件写入。
- `src/worker/` 和 `src/scheduler/` 仅为占位骨架。

# Learning-System

Learning-System 是一个从课堂资料到笔记、RAG 问答、FSRS 复习、知识点总结、思维导图和 Obsidian 导出的学习闭环系统。

当前阶段已创建单包 Next.js App Router 基础工程。此阶段只包含项目脚手架、环境变量模板、基础健康检查 API 和质量命令，不包含业务页面、AI/RAG、数据库、权限、Docker Compose、文件扫描或 Markdown 处理。

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

`.env.example` 中包含后续阶段预留变量。本阶段只需要默认值即可启动，且不应写入真实 API Key、数据库密码或本机私有路径。

## 本地启动

```bash
npm run dev
```

启动后访问：

- 应用占位页：<http://localhost:3000>
- 健康检查：<http://localhost:3000/api/health>

健康检查当前只返回安全字段，不连接数据库或 Redis。

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
- 不实现数据库、权限、Docker Compose。
- 不实现文件扫描或 Markdown 处理。
- `src/worker/` 和 `src/scheduler/` 仅为占位骨架。

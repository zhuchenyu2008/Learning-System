# Deployment Guide

本文档说明如何使用 Docker Compose 部署 learning-system。

## 1. 部署内容

Compose 编排包含以下服务：

- `frontend`：React/Vite 前端静态站点，由 Nginx 提供服务并反向代理 `/api` 到后端
- `backend`：FastAPI API 服务，容器启动时执行 Alembic 迁移
- `worker`：Celery worker，消费异步任务
- `beat`：Celery beat，注册最小定时任务
- `postgres`：PostgreSQL + pgvector
- `redis`：Redis

## 2. 前置要求

- 已安装 Docker Engine
- 已安装 Docker Compose Plugin（支持 `docker compose`）
- 宿主机预留一个目录作为系统工作目录 / Obsidian Vault 挂载点

建议最低配置：

- 2 CPU
- 4 GB RAM
- 10 GB 可用磁盘

## 3. 初始化环境变量

在仓库根目录执行：

```bash
cp .env.example .env
```

至少修改以下项：

- `POSTGRES_PASSWORD`
- `JWT_SECRET_KEY`
- `INITIAL_ADMIN_PASSWORD`
- `WORKSPACE_HOST_PATH`

如需对接 Obsidian headless，同步补充：

- `OBSIDIAN_VAULT`
- `OBSIDIAN_CONFIG_DIR`
- `OBSIDIAN_DEVICE_NAME`
- `OBSIDIAN_HEADLESS_PATH`

## 4. 目录挂载说明

系统将宿主机目录挂载到后端/worker/beat 容器内的 `/data/workspace`：

```env
WORKSPACE_HOST_PATH=./workspace
WORKSPACE_ROOT=/data/workspace
```

如果你希望直接操作本地 Obsidian Vault，可将 `WORKSPACE_HOST_PATH` 指向 Vault 路径，例如：

```env
WORKSPACE_HOST_PATH=/srv/obsidian/learning-system
```

## 5. 启动服务

```bash
docker compose up -d --build
```

查看状态：

```bash
docker compose ps
```

查看日志：

```bash
docker compose logs -f backend
docker compose logs -f frontend
```

## 6. 访问地址

默认端口：

- 前端：`http://localhost:8080`
- 后端 OpenAPI：`http://localhost:8000/docs`
- 后端健康检查：`http://localhost:8000/api/v1/health`

前端容器会将 `/api/*` 反向代理到 `backend:8000`，因此浏览器访问前端时默认无需额外配置跨域。

## 7. 数据持久化

以下数据默认持久化：

- PostgreSQL 数据卷：`postgres_data`
- Redis 数据卷：`redis_data`
- 宿主机工作目录：`WORKSPACE_HOST_PATH`

备份建议：

1. 备份 PostgreSQL 数据卷或执行数据库导出
2. 备份 `WORKSPACE_HOST_PATH` 对应宿主机目录
3. 安全保存 `.env`

## 8. 常用运维命令

重建服务：

```bash
docker compose up -d --build backend frontend
```

停止服务：

```bash
docker compose down
```

停止并删除数据卷（危险操作）：

```bash
docker compose down -v
```

校验配置：

```bash
docker compose config
```

## 9. 生产建议

- 使用强随机 `JWT_SECRET_KEY`
- 修改默认管理员密码
- 不要将 `.env` 提交到代码仓库
- 如需公网暴露，建议在 `frontend` 前增加反向代理（Nginx / Caddy / Traefik）并配置 HTTPS
- 生产环境优先使用宿主机绝对路径作为 `WORKSPACE_HOST_PATH`
- 若后续继续增强 Celery 链路，可在现有 worker/beat 基础上扩展任务编排、监控与告警

## 10. 当前已知边界

- `worker` / `beat` 已接入最小真实 Celery 运行闭环，但当前仍偏工程化基础版，后续可继续增强任务编排、可观测性与失败重试策略
- Docker 依赖宿主机正确配置 `.env` 与 `WORKSPACE_HOST_PATH`，生产部署建议优先使用绝对路径

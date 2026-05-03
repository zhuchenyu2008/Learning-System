# 09 Docker 部署

## 目标

必须提供 Docker 部署方式。

## 服务组成

Docker Compose 应包含：

- `web`: Next.js Web 服务。
- `worker`: BullMQ Worker。
- `scheduler`: 定时任务服务，MVP 可与 worker 合并。
- `postgres`: PostgreSQL + pgvector。
- `redis`: BullMQ broker。
- `storage`: 本地 volume，不一定是独立服务。

可选：

- `caddy` 或 `nginx` 反向代理。
- `minio` 作为对象存储替代本地文件。

## Volume

建议 volume：

- `postgres_data`
- `redis_data`
- `uploads_data`
- `exports_data`
- `backups_data`

含义：

- `uploads_data`: 上传源文件。
- `exports_data`: Obsidian 自动导出目录。
- `backups_data`: 数据库导出压缩包。

上传源文件和导出文件必须分离。

## 环境变量

示例变量：

```env
DATABASE_URL=postgres://learning:learning@postgres:5432/learning
REDIS_URL=redis://redis:6379
APP_URL=http://localhost:3000
SESSION_SECRET=replace-me
UPLOADS_DIR=/data/uploads
EXPORTS_DIR=/data/exports
BACKUPS_DIR=/data/backups
MAX_UPLOAD_MB=1024
```

AI key 不建议写入 `.env.example` 的真实值。生产中由管理员在设置页填写。

## 本机 Obsidian 路径

Docker 容器不能自动访问宿主机任意目录。要导出到 Obsidian Vault，管理员需要在 compose 中把宿主机 Vault 子目录挂载到容器：

```text
宿主机: D:/ObsidianVault/Learning-System-Export
容器: /data/exports
```

Windows、macOS、Linux 的路径格式不同，部署文档需要分别给示例。

## 启动流程

后续实现应支持：

```bash
docker compose up -d
```

启动后：

1. Postgres 初始化扩展 pgvector。
2. Web 服务启动。
3. Worker 服务连接 Redis。
4. 管理员访问初始化页面。
5. 创建第一个管理员。
6. 配置 AI 模型和 Obsidian 导出。

## 备份

数据库导出由应用任务完成，生成压缩包到 `backups_data`。

备份包包含：

- `manifest.json`
- 表数据。
- 生成内容。
- 可选上传源文件。

不包含：

- 明文 API key。
- Session token。
- 临时任务缓存。

## 健康检查

服务应提供：

- `GET /api/health`
- `GET /api/health/db`
- `GET /api/health/redis`
- `GET /api/health/worker`

Docker healthcheck 使用轻量接口。

## 验收标准

- Docker Compose 可以启动 web、worker、Postgres、Redis。
- Web 能连接数据库。
- Worker 能消费测试任务。
- 上传文件进入 uploads volume。
- 导出内容进入 exports volume。
- 删除容器不删除 volume 数据。


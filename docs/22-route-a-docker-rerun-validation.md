# 22-路线A Docker 实跑复验文档

## 1. 背景
主会话复验时确认：
- 前端 lint/build 已可重新跑通
- Docker images 可 build 完成
- 当前阻塞转为宿主机 `5432` 端口占用，导致 `postgres` 容器无法绑定默认端口

## 2. 复验目标
在不改业务代码的前提下，使用非冲突宿主机端口重新执行 Docker 运行态验证，重点确认：
- backend 容器在修正 `PYTHONPATH` 后可正常启动
- worker / beat 可正常启动并加载 Celery app
- frontend -> backend 代理链路可达

## 3. 复验端口策略
使用 `.env` 中以下宿主机端口：
- `FRONTEND_PORT=18080`
- `BACKEND_PORT=18000`
- `POSTGRES_PORT=15432`
- `REDIS_PORT=16379`

## 4. 验收标准
- `docker compose up -d` 成功
- `docker compose ps` 中关键服务为 up/healthy
- `GET /api/v1/health` 可达
- `http://127.0.0.1:18080/api/v1/health` 代理可达

# 15-Docker 与部署实现细节文档

## 1. 部署目标
提供 Docker 化运行方式，至少覆盖：
- frontend
- backend
- worker（可先占位）
- beat（可先占位）
- postgres
- redis

## 2. 目录与文件
- `frontend/Dockerfile`
- `backend/Dockerfile`
- `docker-compose.yml`
- `.env.example`
- `docs/deployment.md`

## 3. 关键要求
- frontend 使用多阶段构建
- backend 使用 Python slim/alpine 生产镜像
- compose 支持挂载本地工作目录 / Obsidian Vault
- 配置数据库、Redis、后端、前端互联
- 为后续 worker/beat 预留命令

## 4. 验收标准
- `docker compose config` 可通过
- 环境变量清晰
- 部署文档可用

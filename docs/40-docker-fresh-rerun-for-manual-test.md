# 40-Docker 从头重跑与人工测试准备文档

## 1. 用户要求
删除当前项目现有 Docker 运行实例/卷/容器，从头跑一遍 Docker 流程，启动成功后交给用户亲自测试。

## 2. 目标
- 清理当前 `learning-system` 相关 Docker 容器 / 网络 / 卷（在本项目 compose 范围内）
- 重新 build
- 重新 up
- 验证 frontend/backend/worker/beat/postgres/redis 状态
- 验证 health 与前端页面可达
- 向用户交付可访问地址与测试前说明

## 3. 范围
- 只清理本项目 compose 相关资源
- 不删除无关项目 Docker 资源
- 默认沿用当前 `.env` 端口：18080 / 18000 / 15432 / 16379

## 4. 验收标准
- `docker compose down -v --remove-orphans` 完成
- `docker compose build` 完成
- `docker compose up -d` 完成
- `docker compose ps` 关键服务正常
- `http://127.0.0.1:18080` 可访问
- `http://127.0.0.1:18080/api/v1/health` 可访问

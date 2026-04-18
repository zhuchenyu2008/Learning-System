# SA-11A Docker 实跑与联通性验证任务单

## 目标
完成 Docker build/up 与联通性验证。

## 必读文档
- docs/18-roadmap-next-steps.md
- docs/19-route-a-engineering-hardening.md
- docs/21-route-a-orchestration.md

## 范围
- 准备 `.env`
- 执行 `docker compose build`
- 执行 `docker compose up -d`
- 验证 frontend/backend/postgres/redis 启动状态
- 抽样验证前端页面与后端 health/API 可达
- 记录问题

## 不要做
- 不扩展业务功能
- 不进入路线 B

## 验收标准
- 给出 build/up/联通性结果与问题清单

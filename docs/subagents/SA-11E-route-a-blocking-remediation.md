# SA-11E 路线A阻塞问题联修任务单

## 目标
一次性查全并修复路线 A 当前运行态阻塞问题，重点是 Docker / Alembic / backend / worker / beat。

## 必读文档
- docs/18-roadmap-next-steps.md
- docs/19-route-a-engineering-hardening.md
- docs/21-route-a-orchestration.md
- docs/22-route-a-docker-rerun-validation.md
- docs/23-route-a-blocking-issues-remediation.md
- docs/deployment.md

## 范围
- 统一排查并修复：
  - Alembic `MissingGreenlet`
  - backend/worker/beat 启动链路
  - Docker 下数据库 URL / migration engine / import path 问题
  - `.env` 端口映射复验所需最小修整
- 必须实际跑：
  - docker compose build
  - docker compose up -d
  - docker compose ps
  - logs 抽样
  - health / 代理链路验证

## 不要做
- 不进入路线 B
- 不扩展产品功能
- 不大改无关业务逻辑

## 验收标准
- backend / worker / beat 可稳定启动
- backend health 可达
- frontend 代理 health 可达
- 回传问题清单、修复点、剩余边界

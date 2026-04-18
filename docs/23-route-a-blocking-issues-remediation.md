# 23-路线A阻塞问题总排查与联修文档

## 1. 目标
按用户要求，对路线 A 当前暴露的运行态问题做一次性总排查与联修，而不是逐个零敲碎打。

## 2. 当前已确认问题簇
### 2.1 Docker / 运行态问题
- 宿主机默认端口冲突，需要通过 `.env` 端口映射规避。
- backend / worker / beat 在容器启动前执行 Alembic 迁移时失败。
- 当前明确错误：`sqlalchemy.exc.MissingGreenlet`
- 该错误说明 Alembic 迁移链路与 async driver / engine 配置不兼容。

### 2.2 启动链路一致性问题
- backend / worker / beat 都依赖统一 Python 包导入路径。
- 已做 `PYTHONPATH=/app/backend` 修整，但仍需结合迁移链路一起验收。

### 2.3 Compose / 部署体验问题
- `.env` 依赖需要更清晰
- 端口策略需要可复验
- 需确认 frontend -> backend 代理链路可达

### 2.4 工程验证问题
- 需要一轮统一复验，而不是分别看 build、容器、日志
- 需要最终把 completed / blocked / failed 一次性收束

## 3. 本轮联修原则
- 优先“一次性查全问题簇”
- 再按根因聚类修复
- 修复后必须做整套复验：
  - docker compose build
  - docker compose up -d
  - docker compose ps
  - backend health
  - frontend 代理健康
  - worker / beat 日志

## 4. 子任务边界
### SA-11E
- 专注 Docker / Alembic / backend/worker/beat 运行态根因排查与修复

### SA-11F
- 在 SA-11E 修复后执行整套联通性复验与路线 A 最终收口确认

## 5. 验收标准
- backend / worker / beat 能稳定启动
- postgres / redis / frontend / backend / worker / beat 均能进入可运行状态
- `GET /api/v1/health` 可达
- `http://frontend/api/v1/health` 代理可达
- 路线 A 的 blocked 项显著减少并形成最终结论

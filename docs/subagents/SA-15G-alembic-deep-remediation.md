# SA-15G Alembic 深度排障任务单

## 目标
深挖并修复 Alembic 版本状态不落库的问题，打通完整测试阶段最后一个部署稳定性阻塞。

## 必读文档
- docs/35-test-execution-guide.md
- docs/36-test-phase-deployment-blocker-remediation.md
- docs/37-test-phase-alembic-state-remediation.md
- docs/38-alembic-deep-remediation.md

## 范围
- 容器内单独排查 `alembic current / upgrade / stamp`
- 核对 SQL 级行为与事务提交
- 修复版本表持久化问题
- 重跑：
  - 全新卷首次启动
  - 已有卷重复重启
  - backend/worker/beat/health/proxy

## 不要做
- 不扩展新业务功能
- 不大改部署结构
- 不用“删库重来”掩盖持久化问题

## 验收标准
- `alembic_version` 真实落库
- 两类启动场景都通过
- 输出 through / blocked / failed 与问题清单

# SA-15F Alembic 状态持久化修整任务单

## 目标
修复 Alembic 版本状态持久化/识别问题，打通“已有卷重复重启”的部署稳定性。

## 必读文档
- docs/35-test-execution-guide.md
- docs/36-test-phase-deployment-blocker-remediation.md
- docs/37-test-phase-alembic-state-remediation.md

## 范围
- 排查 `alembic_version` 表状态问题
- 修复迁移状态识别与持久化
- 重跑：
  - docker compose down -v / up
  - docker compose restart
  - ps / logs / health / proxy

## 不要做
- 不扩展新业务功能
- 不大改部署结构
- 不修改无关测试基线

## 验收标准
- 全新卷首次启动通过
- 已有卷重启通过
- backend / worker / beat 稳定

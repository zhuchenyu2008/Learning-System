# SA-15E 测试阶段部署阻塞修整任务单

## 目标
修复完整测试阶段暴露的 Alembic 迁移字段长度阻塞问题，并重跑 Docker 运行态验证。

## 必读文档
- docs/33-full-test-plan.md
- docs/35-test-execution-guide.md
- docs/36-test-phase-deployment-blocker-remediation.md

## 范围
- 修复 `alembic_version.version_num` 长度兼容问题
- 重跑 docker compose up / ps / logs / health / proxy 验证
- 输出 through / blocked / failed 与问题清单

## 不要做
- 不扩展新业务功能
- 不大改部署结构
- 不修改与该阻塞无关的测试基线

## 验收标准
- backend / worker / beat 稳定启动
- backend health 可达
- frontend 代理 health 可达

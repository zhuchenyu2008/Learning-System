# 36-测试阶段部署阻塞修整文档

## 1. 背景
完整测试阶段（SA-15D）显示：
- 后端自动化测试通过
- 前端自动化测试通过
- Docker config/build 通过
- Docker 运行态部署链路被 Alembic 迁移失败阻塞

## 2. 当前阻塞
核心错误：
- `asyncpg.exceptions.StringDataRightTruncationError`
- `value too long for type character varying(32)`

触发位置：
- `alembic_version.version_num`
- 当前迁移版本号：`0005_sa12a_job_runtime_visibility`

## 3. 修整目标
- 修复 Alembic 版本字段长度兼容问题
- 让 backend / worker / beat 在 Docker 下完成迁移并稳定启动
- 重跑 Docker 运行态验证

## 4. 范围
- 允许修改：
  - Alembic 迁移兼容逻辑
  - 容器启动前迁移策略中最小必要部分
  - 与该问题直接相关的部署脚本/配置
- 不允许：
  - 扩展业务功能
  - 大改现有部署结构
  - 趁机重构无关模块

## 5. 验收标准
- `docker compose up -d` 后 backend / worker / beat 稳定
- backend health 可达
- frontend -> backend 代理可达
- 对完整测试阶段阻塞项给出收口结果

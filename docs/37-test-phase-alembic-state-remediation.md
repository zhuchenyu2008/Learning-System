# 37-测试阶段迁移状态持久化修整文档

## 1. 背景
SA-15E 已修复 Alembic 版本号长度问题，并验证“全新卷首次启动”可通过；但在“已有卷重启”场景下，迁移状态未被稳定识别，导致 backend / worker / beat 重启时重复执行 `0001_backend_foundation`，进而触发 `DuplicateTableError`。

## 2. 当前阻塞
- `alembic_version` 表在首次成功迁移后未稳定存在或未被正确识别
- 重启时 Alembic 误判为未迁移状态
- 结果：已有卷下不可稳定重启

## 3. 修整目标
- 查清 `alembic_version` 缺失/失效根因
- 修复 Alembic 版本状态持久化与识别问题
- 验证两种场景：
  1. 全新卷首次启动
  2. 已有卷重复重启

## 4. 范围
- 允许修改：
  - Alembic env / migration 执行逻辑
  - entrypoint 中最小必要迁移策略
  - 与版本状态持久化直接相关的脚本/配置
- 不允许：
  - 扩展业务功能
  - 大改部署结构
  - 牵扯无关业务模块

## 5. 验收标准
- 首次启动迁移成功
- 已有卷重启不重复撞表
- backend / worker / beat 可重复稳定启动
- health / proxy 复验通过

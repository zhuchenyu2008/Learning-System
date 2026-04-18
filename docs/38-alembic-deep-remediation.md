# 38-Alembic 深度排障与状态持久化修整文档

## 1. 背景
SA-15F 已经确认并修复了两类表层问题：
1. backend / worker / beat 并发执行迁移
2. 运行态 `create_all()` 绕开 Alembic

但核心问题仍未收口：
- Alembic 日志显示 upgrade 已执行
- 数据库中却不存在 `alembic_version` 表
- 因而无法保证已有卷下的重复重启稳定性

## 2. 本轮目标
对 Alembic 状态持久化问题做一次更深的单点排障，只围绕：
- `env.py` async migration 上下文
- 事务提交与版本表写入
- 容器内单独执行 `alembic current / upgrade / stamp`
- SQL 级行为核对

## 3. 排障要求
必须尽量回答清楚：
1. 版本表为什么没有落库
2. 是创建失败、事务回滚、连接上下文问题，还是被自定义逻辑绕过
3. 最小修复方案是什么
4. 修复后是否能同时通过：
   - 全新卷首次启动
   - 已有卷重复重启

## 4. 允许修改范围
- `backend/alembic/env.py`
- Alembic 相关迁移兼容逻辑
- `backend/entrypoint.sh`
- 与迁移状态持久化直接相关的 Docker/启动配置

## 5. 不允许
- 不扩展业务功能
- 不重构无关模块
- 不把问题转嫁为“删除数据重来”作为唯一方案

## 6. 验收标准
- `alembic_version` 真实存在并记录到 head
- 全新卷启动通过
- 已有卷重启通过
- backend / worker / beat 稳定
- health / proxy 通过

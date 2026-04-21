# 59-worker 数据库访问模型修整文档

## 1. 背景
当前真实 Docker 环境下，`POST /api/v1/notes/generate` 接口已能成功排队，但 Celery worker 在接单后数据库访问阶段失败，导致任务卡在 `pending`，无 notes 产出。

## 2. 已确认根因
核心错误：
- `asyncpg.exceptions._base.InterfaceError: cannot perform operation: another operation is in progress`
- `sqlalchemy.exc.InterfaceError: ... cannot perform operation: another operation is in progress`

定位说明：
- 失败发生在 worker 任务刚接单、访问数据库读取 Job 记录时
- 不只是 notes 任务，`review_maintenance` 也出现同类异常
- 说明是 **worker 进程中的 Celery + async SQLAlchemy + asyncpg 使用模型** 存在系统性问题

## 3. 修整目标
- 修复 worker 中的数据库访问模型
- 让异步任务在当前 Docker 环境下真实可执行
- 打通：上传来源 -> 生成笔记 -> Job 完成 -> notes 有产出

## 4. 范围
- `backend/app/worker/tasks.py`
- `backend/app/db/session.py`
- Celery worker 相关数据库访问辅助逻辑
- 与该问题直接相关的测试/验证脚本

## 5. 不要做
- 不扩展新功能
- 不大改无关 provider 逻辑
- 不重构整套任务系统

## 6. 验收标准
- worker 不再报 `another operation is in progress`
- notes 生成任务在真实 Docker 环境下可完成
- 至少一条 txt/md/docx 生成链路成功落地 note

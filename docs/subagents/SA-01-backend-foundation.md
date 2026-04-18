# SA-01 后端基础骨架任务单

## 目标
实现后端基础工程：FastAPI 应用骨架、配置系统、数据库模型基础、Alembic 初始化、认证与角色权限、统一响应结构。

## 必读文档
- docs/00-main-task.md
- docs/03-architecture.md
- docs/04-module-boundaries.md
- docs/05-api-and-data-contracts.md
- docs/06-implementation-plan.md
- docs/07-subagent-orchestration-plan.md

## 范围
- backend 基础目录结构
- FastAPI app / api/v1 / health
- 配置管理
- SQLAlchemy models: User, SystemSetting, AIProviderConfig, Job（至少这些）
- JWT auth / refresh 基础
- role-based dependency
- 初始 seed 管理员说明
- pytest 基础测试

## 不要做
- 不做笔记生成主链
- 不做复习主链
- 不做前端

## 验收标准
- backend 可启动
- OpenAPI 正常
- 基本 auth 路由可工作
- 测试可运行

## 回传要求
- 改动文件列表
- 执行命令列表
- 通过项 / 未通过项 / 阻塞项

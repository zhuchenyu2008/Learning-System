# SA-10 后端设置与管理接口任务单

## 目标
补齐 settings/admin 后端接口，支撑前端设置模块真实联调。

## 必读文档
- docs/00-main-task.md
- docs/05-api-and-data-contracts.md
- docs/06-implementation-plan.md
- docs/07-subagent-orchestration-plan.md
- docs/16-backend-settings-admin-module.md

## 范围
- 实现 settings system/ai/obsidian API
- 实现 test-provider API
- 实现 admin users/user-activity/login-events API
- 实现 database export/import API（首版可简化但必须真实）
- 实现 obsidian sync trigger API
- 基本测试覆盖权限与主链

## 不要做
- 不改前端
- 不扩展 notes/review 功能
- 不伪造成功响应

## 验收标准
- 前端 settings 所需接口可访问
- admin 权限限制正确
- 基本测试通过

## 回传要求
- 改动文件列表
- 执行命令列表
- 通过项
- 未通过项
- 阻塞项

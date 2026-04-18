# 14-前端设置模块实现细节文档

## 1. 页面范围
- 设置 / AI 配置
- 设置 / 工作区与 Obsidian
- 设置 / 用户与登录情况
- 设置 / 导入导出
- 设置 / 任务与调度

## 2. 页面细节
### 2.1 AI 配置
- LLM / Embedding / STT / OCR 四类配置表单
- base_url / api_key / model_name
- 测试连接按钮占位或基础调用
- 普通用户禁用

### 2.2 工作区与 Obsidian
- workspace_root
- Vault 路径
- obsidian-headless 路径
- vault name/id
- config dir
- device name
- 触发同步按钮

### 2.3 用户与登录情况
- 用户列表
- 角色与状态
- 最近登录时间
- 登录事件 / 观看时长占位展示

### 2.4 导入导出
- 数据库导出按钮
- 数据库导入表单
- 结果状态展示

### 2.5 任务与调度
- scheduler placeholder 任务列表
- 后台 job 状态列表
- 注册开关 / 系统配置展示

## 3. API 对接
- `GET /api/v1/settings/system`
- `PUT /api/v1/settings/system`
- `GET /api/v1/settings/ai`
- `PUT /api/v1/settings/ai`
- `GET /api/v1/settings/obsidian`
- `PUT /api/v1/settings/obsidian`
- `POST /api/v1/settings/test-provider`
- `GET /api/v1/admin/users`
- `GET /api/v1/admin/user-activity`
- `GET /api/v1/admin/login-events`
- `POST /api/v1/admin/database/export`
- `POST /api/v1/admin/database/import`
- `POST /api/v1/admin/obsidian/sync`
- `GET /api/v1/jobs`
- `GET /api/v1/scheduler/tasks`

## 4. 验收标准
- 管理员页面结构齐全
- 普通用户禁用态正确
- Obsidian 增强同步配置入口可见

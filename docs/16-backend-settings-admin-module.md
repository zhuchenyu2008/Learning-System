# 16-后端设置与管理接口模块实现细节文档

## 1. 模块目标
补齐前端设置模块所依赖的后端 settings/admin API，使系统配置、AI 配置、Obsidian 配置、用户管理、登录事件、数据库导入导出、手动同步等能力形成真实后端主链。

## 2. API 范围
### 2.1 Settings
- `GET /api/v1/settings/system`
- `PUT /api/v1/settings/system`
- `GET /api/v1/settings/ai`
- `PUT /api/v1/settings/ai`
- `GET /api/v1/settings/obsidian`
- `PUT /api/v1/settings/obsidian`
- `POST /api/v1/settings/test-provider`

### 2.2 Admin
- `GET /api/v1/admin/users`
- `GET /api/v1/admin/user-activity`
- `GET /api/v1/admin/login-events`
- `POST /api/v1/admin/database/export`
- `POST /api/v1/admin/database/import`
- `POST /api/v1/admin/obsidian/sync`

## 3. 数据模型/存储策略
- 复用 `SystemSetting`
- 扩展 `AIProviderConfig` 支持 llm / embedding / stt / ocr 多条配置
- 如当前缺少登录事件/用户活动实体，可在不破坏边界前提下补最小模型：
  - `LoginEvent`
  - `UserActivitySnapshot` 或等效简化实现
- 数据库导入导出首版可先做“数据库文件/SQLA 导出包 + 元数据 JSON”的管理接口，不要求做复杂在线迁移

## 4. 实现策略
- 所有 settings/admin 接口仅 admin 可访问
- `test-provider` 实际走 OpenAI-compatible provider 探活，不伪造成功
- `obsidian/sync` 实际调用现有 obsidian sync service
- 导入导出首版以可运行、安全、边界清晰为主
- 若用户活动/观看时长暂无完整埋点主链，可先提供结构化接口与最小可用统计

## 5. 验收标准
- 前端 settings 所依赖接口全部可访问
- 基本测试覆盖至少关键配置读取/写入与权限校验
- 不破坏现有 auth / notes / review 主链

# 设置 - Obsidian 配置

## 目标用户

- 管理员：配置 Obsidian 导出目录和同步辅助能力。
- 普通用户：查看导出是否启用，不能修改。

## 入口

- 路由：`/settings/obsidian`
- 侧边栏：设置 -> Obsidian 配置

## 页面目标

让数据库中的生成内容自动导出为 Obsidian 友好的 Markdown 文件，同时明确上传源文件不进入导出目录。

## 布局

页面分区：

1. 导出总开关。
2. Vault/导出路径配置。
3. 导出目录结构预览。
4. 文件命名规则。
5. Obsidian URI 测试。
6. Local REST API 可选配置。
7. 全量重新导出。

## 织物质感 UI 规则

- 路径预览使用等宽字体，放在浅帆布块中。
- 成功测试使用绿色织带状态。
- 路径错误使用红棕缝线提示。
- 全量重新导出是高影响操作，按钮使用稳重警示样式。

## 管理员权限

管理员可以：

- 配置导出根目录。
- 测试目录写入权限。
- 测试 Obsidian URI。
- 配置 Local REST API 地址和 token。
- 触发全量重新导出。
- 设置删除策略。

## 普通用户权限

普通用户可以：

- 查看是否启用导出。
- 查看导出说明。

普通用户不能：

- 修改路径。
- 测试写入。
- 触发全量导出。
- 查看 Local REST API token。

## 禁用状态

普通用户访问时：

- 路径输入框只读。
- 测试写入、测试 URI、全量重新导出按钮禁用。
- Local REST API token 脱敏。
- 删除策略只读。

## 导出结构预览

页面必须展示：

```text
<导出根目录>/
  <学科>/
    笔记/
    知识点总结/
    思维导图/
```

并明确说明：

```text
上传源文件不会写入此目录。
```

## 主要交互

- 管理员填写导出根目录并保存。
- 管理员点击“测试写入”创建测试任务。
- 管理员点击“测试 Obsidian URI”验证本机打开体验。
- 管理员配置 Local REST API 并测试连接。
- 管理员点击“全量重新导出”创建后台任务。

## 接口与数据读写

读取：

- `GET /api/settings/obsidian`
- `GET /api/export/status`

写入：

- `PUT /api/settings/obsidian`，仅管理员。
- `POST /api/settings/obsidian/test-write`，仅管理员。
- `POST /api/settings/obsidian/test-uri`，仅管理员。
- `POST /api/export/rebuild-all`，仅管理员。

写入表：

- `app_settings`
- `jobs`
- `audit_logs`

## 异步任务

- `export.full_rebuild_obsidian`
- `export.test_obsidian_path`

## 异常状态

- 路径不存在：测试失败。
- 路径不可写：测试失败。
- Docker 未挂载宿主路径：提示检查 volume。
- Obsidian URI 不可用：不影响导出。
- Local REST API 不可用：降级为文件导出。

## 验收标准

- 管理员可以配置并测试导出目录。
- 页面明确上传源文件不导出。
- 全量重新导出走异步任务。
- 普通用户不能修改配置。
- 导出路径预览与实际规则一致。

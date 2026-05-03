# 07 Obsidian 导出与同步

## 目标

系统数据库是唯一主存储。Obsidian 只作为阅读、双链浏览和跨设备同步的导出目标。

导出内容包括：

- 笔记。
- 知识点总结。
- 思维导图。

上传源文件不导出到 Obsidian 自动导出目录。

## 官方能力边界

Obsidian Sync 是 Obsidian 的同步能力，适合同步 vault 中的 Markdown 文件。系统不直接实现 Obsidian Sync 协议，只负责写入本地导出目录。

参考：

- Obsidian Sync: <https://help.obsidian.md/sync>
- Obsidian URI: <https://help.obsidian.md/Extending+Obsidian/Obsidian+URI>
- Local REST API 插件: <https://github.com/coddingtonbear/obsidian-local-rest-api>

## 推荐同步方案

### 默认方案：导出到 Vault 文件夹

管理员在设置页配置：

- Obsidian Vault 路径。
- 导出根目录。
- 是否覆盖同名文件。
- 是否删除数据库中已删除内容对应的导出文件。

系统将生成内容写入：

```text
<Vault路径>/<导出根目录>/<学科>/笔记/
<Vault路径>/<导出根目录>/<学科>/知识点总结/
<Vault路径>/<导出根目录>/<学科>/思维导图/
```

随后由用户本机 Obsidian 和 Obsidian Sync 完成跨设备同步。

## 文件命名

标题由 AI 生成，但必须追加具体时间：

```text
<AI标题> YYYY-MM-DD HH-mm.md
```

冲突处理：

1. 相同数据库内容重复导出时覆盖原导出文件。
2. 不同内容生成同名文件时追加短 ID。
3. 文件名清理非法字符。
4. 保留标题中的中文、数字、常见符号和 LaTeX 必要字符。

## Markdown Frontmatter

导出文件包含 YAML frontmatter：

```yaml
id: note_123
类型: 笔记
学科: 数学
来源: Learning-System
创建时间: 2026-05-03 20:30
更新时间: 2026-05-03 20:40
```

Frontmatter 后写入正文。

## 思维导图导出

思维导图导出为 Markdown：

- 首先写入标题、来源范围、生成时间。
- 写入 Markmap Markdown。
- 追加 Mermaid `mindmap` 兼容代码块。
- 追加简短说明和来源链接。

## 反向链接

导出 Markdown 中可以使用 Obsidian wikilink：

```markdown
[[数学/笔记/函数单调性 2026-05-03 20-30|函数单调性]]
```

链接生成规则：

- 只链接真实存在或将被导出的内容。
- 关联笔记少而准。
- 不暴露向量检索分数。

## 导出任务

导出必须走 `export` 队列：

- `export.export_note_to_obsidian`
- `export.export_summary_to_obsidian`
- `export.export_mind_map_to_obsidian`
- `export.full_rebuild_obsidian`

导出成功后回写：

- `export_status`
- `export_path`
- `exported_at`

## 错误处理

- 导出目录不可写：任务失败，提示管理员检查路径权限。
- 文件名冲突：自动追加短 ID。
- Vault 路径不存在：设置页测试失败。
- Obsidian 未安装：不影响文件导出，只影响打开按钮。
- Local REST API 不可用：降级为文件导出。

## 验收标准

- 上传源文件不会进入导出目录。
- 笔记、知识点总结、思维导图按学科分类导出。
- 文件名包含 AI 标题和具体时间。
- 重新导出不会产生无限重复文件。
- Docker 部署文档说明服务端路径映射限制。


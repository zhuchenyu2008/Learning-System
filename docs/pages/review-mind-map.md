# 复习 - 思维导图生成

## 目标用户

- 管理员：手动选择笔记范围生成思维导图。
- 普通用户：查看和交互浏览思维导图。

## 入口

- 路由：`/review/mind-maps`
- 侧边栏：复习 -> 思维导图生成

## 页面目标

把单篇或多篇笔记转成可交互思维导图，帮助用户理解知识结构。该页面只保留手动生成和历史导图查看。

## 实现方案

主方案：

- AI 输出 Markmap Markdown。
- 前端用 Markmap 渲染交互 SVG。
- 支持展开、折叠、缩放、拖拽、适配屏幕。

兼容方案：

- 同时保存 Mermaid `mindmap` 代码块。
- 导出 Markdown 时包含 Mermaid 版本，方便 Obsidian 插件或其他 Markdown 工具渲染。

参考：

- Markmap: <https://markmap.js.org/>
- Mermaid mindmap: <https://mermaid.js.org/syntax/mindmap.html>

## 布局

桌面端：

- 左侧：导图列表、学科筛选。
- 中间：全幅导图画布。
- 右侧：来源范围、生成设置、节点摘要。

移动端：

- 导图画布优先。
- 列表和设置使用抽屉。

## 织物质感 UI 规则

- 画布背景使用极淡织纹，避免影响节点线条。
- 节点像布签，层级越深颜色越轻。
- 连接线使用低透明度墨色。
- Hover 节点时提升高光，不大幅缩放。
- 工具栏使用图标按钮，带 tooltip。

## 管理员权限

管理员可以：

- 选择来源范围生成导图。
- 输入额外提示词。
- 删除导图。
- 重新生成。
- 重新导出。

## 普通用户权限

普通用户可以：

- 查看导图。
- 缩放、拖拽、展开、折叠。
- 打开来源笔记。

普通用户不能：

- 生成。
- 删除。
- 重新生成。

## 禁用状态

普通用户：

- 生成按钮禁用。
- 来源选择禁用。
- 画布交互保持可用。

## 手动生成

管理员输入：

- 学科。
- 来源范围。
- 额外提示词，可为空。
- 导图深度，默认 4 层。
- 是否包含例题节点。
- 是否导出 Mermaid 兼容版本，默认开启。

AI 输出必须包含：

- `markmap_markdown`
- `mermaid_mindmap`
- `summary_markdown`
- AI 标题。

生成入口只接受本次手动选择的范围、导图深度和提示词。

## 主要交互

- 点击导图列表项加载画布。
- 使用工具栏进行放大、缩小、适配屏幕、全部展开、全部折叠。
- 点击节点查看对应摘要和来源笔记。
- 管理员点击“生成导图”打开来源范围选择。
- 管理员提交后查看异步生成进度。
- 管理员可重新导出或重新生成。

## 接口与数据读写

读取：

- `GET /api/mind-maps`
- `GET /api/mind-maps/:id`
- `GET /api/notes?selectable=true`

写入：

- `POST /api/mind-maps/generate`，仅管理员。
- `DELETE /api/mind-maps/:id`，仅管理员。
- `POST /api/mind-maps/:id/export`，仅管理员。

写入表：

- `mind_maps`
- `jobs`
- `rag_chunks`

## 异步任务

- `ai.generate_mind_map`
- `embedding.index_mind_map`
- `export.export_mind_map_to_obsidian`

## 异常状态

- Markmap 渲染失败：显示 Markdown 原文和错误。
- Mermaid 生成失败：不影响 Markmap 主渲染，但导出提示兼容版本缺失。
- 来源范围过大：提示缩小范围。
- AI 输出格式不合法：任务失败并记录原始错误摘要。
- 画布过大：默认折叠深层节点。

## 验收标准

- 管理员可以对多篇笔记生成导图。
- 普通用户可以交互浏览导图。
- 手动生成支持额外提示词。
- 页面只提供手动生成配置。
- 导出到 `<学科>/思维导图/`。

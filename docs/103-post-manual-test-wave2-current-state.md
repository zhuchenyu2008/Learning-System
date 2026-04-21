# 103-仓库/现状分析文档

## 1. 已知现状
- review card generation 已改为 LLM 优先 + fallback，但用户最新实际观察仍认为任务日志透明度不足甚至可能未真正执行
- summaries/mindmaps 页面已能预览详情，但生成成功提示仍使用立即返回 payload，可能出现 `output_note_id=0/空路径` 的占位文案
- 笔记/总结/导图页面当前未见通用删除入口
- `NoteDetailRenderer` 及相关渲染链当前主要覆盖 Markdown/HTML/Mermaid，尚未确认 KaTeX/Math 支持
- notes/review 多页面使用三列/大网格布局，移动端存在 overflow 风险
- 多选列表使用 label + checkbox + card 样式，用户仍反馈出现“卡片已选中但 checkbox 没勾上”的一致性问题
- 现有 review 主要面向复习执行，不具备管理员精细卡片管理页

## 2. 风险点
- 删除能力涉及 DB 与文件系统一致性
- 复习卡片按学科分组需要补齐后端数据来源与前端选择流
- LaTeX 支持需避免破坏现有 Mermaid/HTML 渲染

## 3. 实施原则
- 优先修关键闭环：日志/状态透明度、删除、渲染、移动端
- review-card 管理与按学科复习并行设计，但实现边界必须清晰

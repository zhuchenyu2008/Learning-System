# 106-API / 数据契约主文档

## 1. 删除相关
### DELETE /api/v1/notes/{note_id}
- 删除普通笔记；返回删除结果与级联摘要

### DELETE /api/v1/review/summaries/{artifact_id}
- 删除 summary artifact + 其输出 note

### DELETE /api/v1/review/mindmaps/{artifact_id}
- 删除 mindmap artifact + 其输出 note

## 2. review card 管理
### GET /api/v1/review/cards/admin
- 支持 subject / note_id / query / pagination

### POST /api/v1/review/cards/admin
- 新建卡片/知识点最小闭环

### PATCH /api/v1/review/cards/admin/{card_id}
- 编辑题面/答案/标签/学科/暂停状态

### DELETE /api/v1/review/cards/admin/{card_id}
- 删除卡片，必要时同步清理空 knowledge point

## 3. 按学科复习
### GET /api/v1/review/subjects
- 返回可复习学科及卡片数量

### GET /api/v1/review/cards/due?subject=物理&limit=20
- 复习待复习卡片查询支持 subject + limit

## 4. 任务状态体验
- 总结/导图生成接口返回 job_id/status，前端以后续 job 查询为准
- 若 output_note_id 尚未准备，不展示 0/空路径为“完成结果”

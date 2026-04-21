# 104-总体架构文档

## 1. 架构分层
### A. Review job transparency layer
- job 执行日志、result_json、前端状态呈现统一增强

### B. Artifact lifecycle layer
- notes / summary / mindmap 增加删除 API 与前端入口
- 删除时统一走服务层，保证 DB + 文件系统 + artifact 关系一致

### C. Render layer
- `NoteDetailRenderer` 为统一内容渲染核心
- 在该层接入 Markdown + Mermaid + LaTeX 共存渲染

### D. Review management layer
- 管理员复习卡片管理页
- 卡片 CRUD + 按学科筛选
- 用户复习会话启动时支持 subject + limit 输入

### E. Responsive UX layer
- notes/review 页面网格布局、容器宽度、溢出治理
- 多选卡片交互状态统一

## 2. 数据流关键点
- 任务创建类页面不再把“创建成功”误报为“产物已准备好”
- 任务状态由 job 查询驱动
- 复习卡片学科优先从关联 note/knowledge_point 推导并固化到读模型/API

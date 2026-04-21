# 105-模块边界文档

## M1 Review job audit / transparency
- backend review_service / job_service / review endpoints
- frontend 任务状态展示相关 review pages

## M2 Delete lifecycle
- backend notes/review artifact endpoints + service
- frontend notes library / summary / mindmap list actions

## M3 Rendering / LaTeX
- frontend shared renderer components only
- 不在业务页分散实现公式逻辑

## M4 Responsive + selection UX
- notes generate / summaries / mindmaps / notes library / review 关键页面布局与选择组件

## M5 Admin review-card management
- backend review-card CRUD APIs
- frontend admin management page or admin-only section

## M6 Subject-based review session
- backend 查询/聚合/过滤
- frontend 复习开始前配置入口

## 冲突规避
- M3 与 M4 可并行，但都可能改 renderer/page layout，需限制在共享渲染 vs 页面布局两类文件
- M5 与 M6 共享 review domain，需串行由同一实现链处理或拆成先 API 后前端

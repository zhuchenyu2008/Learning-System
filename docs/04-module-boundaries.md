# 04-模块边界文档

## 1. backend/api
职责：REST API、认证、参数校验、权限、响应包装。
不负责：耗时 AI 任务直接执行。

## 2. backend/services
职责：业务编排、数据库事务、文件与任务生命周期。
不负责：HTTP 层响应。

## 3. backend/workers
职责：异步执行多媒体处理、生成、同步、调度。
不负责：前端展示逻辑。

## 4. backend/integrations
职责：OpenAI 兼容 LLM/Embedding/STT/OCR、Obsidian Sync、文件扫描器。
不负责：业务权限判断。

## 5. frontend/app-shell
职责：布局、路由、主题、权限态 UI。

## 6. frontend/features/notes
职责：笔记概览、生成、列表、详情渲染。

## 7. frontend/features/review
职责：复习总览、复习会话、知识点总结、思维导图。

## 8. frontend/features/settings
职责：AI/同步/系统配置、用户管理、导入导出、任务配置。

## 9. shared contracts
职责：OpenAPI 驱动的 DTO / TS 类型。

## 10. local workspace folder
职责：原始资料、Markdown、生成产物、导出包。
边界：只通过后端受控读写；前端不直接操作宿主文件。

# 108-subagent 总拆分计划文档

## SA-56 Review jobs 透明度与 artifact 生成状态体验
- 范围：task 调查、review job logging/result、summary/mindmap 生成状态文案/轮询

## SA-57 删除能力
- 范围：删除 note / summary / mindmap 的后端 API + 前端入口

## SA-58 渲染与移动端 UX
- 范围：LaTeX 支持、移动端 overflow、checkbox 选择态一致性

## SA-59 复习卡片管理与按学科复习
- 范围：管理员 review-card CRUD、subject 聚合、用户按学科+数量开始复习

## 串并行
- SA-56 / SA-57 / SA-58 可并行
- SA-59 依赖 review 域接口设计，单独串行
- 最后统一验证并视情况 Docker 重启

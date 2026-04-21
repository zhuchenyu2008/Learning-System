# 101-新一轮人工测试问题主任务文档

## 1. 用户新增反馈
1. 复习卡片任务仍异常：task `80b23505-e2fd-4837-80a7-85089e7c9e4f` 开始/结束/更新时间相同，日志仅 `job completed`
2. 增加删除笔记 / 知识点总结 / 思维导图功能
3. 总结与思维导图生成时，状态体验应对齐笔记生成，不应直接显示“已创建任务 #x，输出笔记 #0（）”
4. 所有渲染页面支持 LaTeX
5. 移动端多处向右溢出
6. 选中笔记时偶现“已选择但前面复选框未打勾”
7. 管理员需要复习卡片详细增删功能
8. 复习卡片按学科分组，用户可选择学科与本轮复习数量进行复习

## 2. 本轮目标
完成上述 8 项问题的设计、拆分、实现、验证，并维持当前 learning-system 主链稳定。

## 3. 范围
- backend: review cards, notes/artifacts delete, subject-based review session filtering
- frontend: summaries/mindmaps UX, LaTeX render, mobile overflow, selection consistency, admin review-card management
- docs/tests: 本轮修复需要的最小验证与交接文档

## 4. 非目标
- 不重做整套产品信息架构
- 不扩张到新的 AI 能力探索
- 不擅自 push

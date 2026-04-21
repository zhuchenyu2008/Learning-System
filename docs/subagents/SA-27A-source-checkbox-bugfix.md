# SA-27A 来源资产勾选显示缺陷任务单

## 目标
修复笔记生成页来源资产列表“实际已选中但勾选不显示”的前端 bug。

## 必读文档
- docs/45-notes-upload-first.md
- docs/55-sixth-feedback-remediation.md
- docs/56-sixth-feedback-followup-bugs.md

## 范围
- 排查 checkbox 受控状态、事件冒泡、列表 key、重渲染时机、Mutation 成功后状态写入
- 修复显示不一致问题
- 补前端测试

## 不要做
- 不扩展新功能
- 不重构整套笔记生成页

## 验收标准
- 单击后 UI 勾选立即稳定显示
- 选中状态与生成请求使用的 source_asset_ids 一致

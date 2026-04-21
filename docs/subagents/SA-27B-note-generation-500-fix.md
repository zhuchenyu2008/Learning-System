# SA-27B 笔记生成 500 缺陷任务单

## 目标
查清并修复当前环境中“开始生成笔记”仍报 500 的真实根因。

## 必读文档
- docs/29-final-delivery-summary.md
- docs/45-notes-upload-first.md
- docs/56-sixth-feedback-followup-bugs.md

## 范围
- 结合当前 Docker 环境/日志排查 `POST /api/v1/notes/generate`
- 明确是上传资产内容处理、provider 调用、文件写入、数据库写入、任务调度还是返回解析出错
- 修复最小必要链路
- 补测试与验证

## 不要做
- 不扩展新功能
- 不大改无关 provider 结构

## 验收标准
- 500 根因明确
- 生成链路修复
- 至少一条真实来源资产生成路径可通过

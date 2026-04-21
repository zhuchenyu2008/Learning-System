# SA-27B2 笔记生成500真实链路续查任务单

## 目标
继续在当前 Docker 运行环境下完成笔记生成 500 的真实链路验证与收口。

## 必读文档
- docs/56-sixth-feedback-followup-bugs.md
- docs/57-note-generation-500-followup.md
- docs/subagents/SA-27B-note-generation-500-fix.md

## 范围
- 管理员登录
- 上传 txt/md/docx 来源
- 调用 `/api/v1/notes/generate`
- 检查 backend / worker / beat / postgres 日志
- 给出最终 through / blocked / failed 与根因

## 不要做
- 不扩展新功能
- 不改无关模块

## 验收标准
- 给出真实环境中的最终结论

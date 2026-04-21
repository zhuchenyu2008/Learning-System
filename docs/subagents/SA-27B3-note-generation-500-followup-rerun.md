# SA-27B3 笔记生成500真实链路续查重试任务单

## 目标
重新完成当前 Docker 环境下的笔记生成 500 真实链路验证，并保证回传有证据。

## 必读文档
- docs/56-sixth-feedback-followup-bugs.md
- docs/57-note-generation-500-followup.md
- docs/58-note-generation-500-followup-rerun.md
- docs/subagents/SA-27B-note-generation-500-fix.md

## 范围
- 管理员登录
- 上传 txt / md / docx
- 调用生成接口
- 查看运行日志
- 必要时做最小修复

## 不要做
- 不扩展新功能
- 不做无关重构

## 验收标准
- 回传必须包含实际命令、实际返回、through/blocked/failed

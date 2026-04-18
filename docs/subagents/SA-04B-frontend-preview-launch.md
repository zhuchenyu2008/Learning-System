# SA-04B 前端预览启动任务单

## 目标
在不修改业务代码的前提下，将前端项目启动在 `18794` 端口，供预览使用。

## 必读文档
- docs/00-main-task.md
- docs/07-subagent-orchestration-plan.md
- docs/09-frontend-preview-launch.md

## 范围
- 进入 `frontend` 目录
- 如依赖缺失则补装
- 启动 Vite dev server：监听 `0.0.0.0:18794`
- 验证本机访问是否返回 HTML

## 不要做
- 不修改业务功能
- 不修改后端
- 不扩展页面逻辑

## 验收标准
- 进程保持运行
- `http://127.0.0.1:18794` 可返回页面内容

## 回传要求
- 启动命令
- 验证命令
- 结果
- 若失败写明阻塞项

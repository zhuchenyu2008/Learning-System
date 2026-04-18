# SA-04A 前端构建修整任务单

## 目标
修整前端构建配置，使现有前端壳层在不破坏结构的前提下通过构建。

## 必读文档
- docs/00-main-task.md
- docs/06-implementation-plan.md
- docs/07-subagent-orchestration-plan.md
- docs/08-foundation-remediation-plan.md
- docs/subagents/SA-04-frontend-shell-and-theme.md

## 当前已知问题
- `npm install` 已成功
- `npm run build` 失败
- 已知错误：
  - `Cannot find module 'node:path'`
  - `Cannot find name '__dirname'`

## 范围
- 只修前端构建与 TS/Vite 配置
- 保持现有路由、主题、页面结构
- 必要时补 Node 类型、ESM 路径写法等

## 不要做
- 不扩展业务页面功能
- 不改后端

## 验收标准
- `npm run build` 通过

## 回传要求
- 改动文件列表
- 执行命令列表
- 通过项
- 未通过项
- 阻塞项

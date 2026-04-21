# SA-47 前端既有TS错误修复任务单

## 目标
先修掉当前阻塞前端全量构建的既有 TypeScript 错误，为最终交付总结更新和 Docker 重启扫清阻塞。

## 必读文档
- docs/83-final-delivery-summary.md
- docs/84-commit-preparation-notes.md
- docs/95-final-pre-handoff-ts-fix-and-rerun-main.md

## 重点范围
- `frontend/src/pages/notes/notes-library-page.tsx`
- 与该类型错误直接相关的最小类型/状态定义范围

## 必做事项
1. 修复 `notes-library-page.tsx` 中阻塞 build 的 TS 类型错误
2. 运行前端全量构建验证
3. 不扩张到无关功能修改

## 验收标准
- `npm run build` 在 frontend 目录下通过
- 回传改动文件、命令与证据

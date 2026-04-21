# 51-SA-22A 回退文档

## 1. 用户要求
用户明确要求：**撤销 SA-22A 的前端改动**，原因是视觉效果“改得越来越丑”。

## 2. 回退范围
仅回退 SA-22A 本轮改动带来的前端视觉/布局调整，目标文件以当时回传为准：
- `frontend/src/components/app-shell.tsx`
- `frontend/src/pages/notes/notes-generate-page.tsx`
- `frontend/src/pages/settings/settings-workspace-page.tsx`
- `frontend/src/styles.css`

## 3. 回退原则
- 只回退 SA-22A 这轮改动
- 不波及其他已确认有效的问题修复（例如上传功能、注册闭环、活动统计修复等）
- 若某文件中既有 SA-22A 改动，也包含其他后续有效修复，则只做最小定向回退

## 4. 验收标准
- SA-22A 带来的视觉/布局变化被撤销
- 前端仍可 build
- 不引入新的功能性回退

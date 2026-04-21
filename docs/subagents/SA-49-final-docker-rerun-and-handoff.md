# SA-49 Docker普通流程重启与交接前确认任务单（最终）

## 目标
在前端构建阻塞修复和最终交付总结更新后，按普通流程重启 Docker，并完成最小健康确认，交给用户做最终人工测试。

## 必读文档
- docs/95-final-pre-handoff-ts-fix-and-rerun-main.md

## 前置依赖
- SA-47 已完成
- SA-48 已完成

## 执行范围
- `docker compose down -v --remove-orphans`
- `docker compose build`
- `docker compose up -d`
- `docker compose ps`
- backend/proxy health
- frontend 首页可达

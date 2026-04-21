# SA-55 最新修复后 Docker 重启与交接确认任务单

## 目标
在当前最新代码基础上，按普通流程重启 Docker，并完成最小健康确认，交给用户继续人工测试。

## 必读文档
- docs/100-latest-fixes-handoff-main.md

## 执行范围
- `docker compose down -v --remove-orphans`
- `docker compose build`
- `docker compose up -d`
- `docker compose ps`
- backend health
- proxy health
- frontend 首页可达

## 不要做
- 不改代码
- 不做额外环境改造

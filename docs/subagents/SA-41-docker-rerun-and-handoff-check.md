# SA-41 Docker普通流程重启与交接前确认任务单

## 目标
用当前最新代码按普通流程重启 Docker，并完成最小健康确认，为用户最终人工测试准备环境。

## 必读文档
- docs/81-final-delivery-and-release-prep-main.md
- docs/82-final-handoff-orchestration-plan.md

## 范围
- 执行：
  - `docker compose down -v --remove-orphans`
  - `docker compose build`
  - `docker compose up -d`
- 核验：
  - `docker compose ps`
  - backend health
  - proxy health
  - frontend 首页可达

## 不要做
- 不再改代码
- 不擅自做额外环境改造

## 验收标准
- 服务全部启动
- health 通过
- 可把测试入口交给用户

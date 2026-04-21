# SA-24 回退后 Docker 普通流程重启任务单

## 目标
在 SA-23 回退完成后，重新按普通 Docker 流程启动项目，供用户人工查看效果。

## 必读文档
- docs/46-docker-normal-rerun.md
- docs/51-revert-sa22a.md
- docs/52-docker-rerun-after-sa23.md

## 范围
- `docker compose down -v --remove-orphans`
- `docker compose build`
- `docker compose up -d`
- `docker compose ps`
- health / 页面 / 代理验证

## 不要做
- 不扩展新功能
- 不修改无关配置

## 验收标准
- Docker 普通流程通过
- 返回最新可访问地址

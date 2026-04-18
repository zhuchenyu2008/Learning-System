# SA-17 Docker 全新重跑与人工测试准备任务单

## 目标
把 learning-system 当前 Docker 资源按项目范围清掉后重新跑起来，交付给用户做人工测试。

## 必读文档
- docs/29-final-delivery-summary.md
- docs/deployment.md
- docs/40-docker-fresh-rerun-for-manual-test.md

## 范围
- docker compose down -v --remove-orphans
- docker compose build
- docker compose up -d
- docker compose ps / logs / health / 页面验证
- 回传访问地址与测试注意事项

## 不要做
- 不删除无关项目 Docker 资源
- 不扩展新功能
- 不修改无关配置

## 验收标准
- 项目容器从头拉起成功
- 用户可直接访问前端并开始人工测试

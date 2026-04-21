# SA-21 Docker 普通流程重启任务单

## 目标
按普通 Docker 流程把 learning-system 现有容器删掉，并用最新代码重新启动。

## 必读文档
- docs/deployment.md
- docs/46-docker-normal-rerun.md

## 范围
- `docker compose down -v --remove-orphans`
- `docker compose build`
- `docker compose up -d`
- `docker compose ps`
- `curl` 验证前端、backend health、frontend 代理 health
- 输出测试地址与注意事项

## 不要做
- 不删除无关项目 Docker 资源
- 不修改无关配置
- 不扩展新功能

## 验收标准
- Docker 普通流程重启成功
- 最新代码在容器里可用

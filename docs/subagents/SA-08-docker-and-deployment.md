# SA-08 Docker 与部署任务单

## 目标
补齐 Dockerfile、docker-compose、环境变量样例、运行脚本、部署文档。

## 必读文档
- docs/00-main-task.md
- docs/03-architecture.md
- docs/06-implementation-plan.md
- docs/07-subagent-orchestration-plan.md

## 范围
- frontend/backend/worker Dockerfile
- docker-compose.yml
- .env.example
- 部署说明文档

## 不要做
- 不大改业务逻辑

## 验收标准
- compose 配置可解析
- 启动所需环境变量明确

## 回传要求
- 改动文件列表
- 执行命令列表
- 通过项 / 未通过项 / 阻塞项

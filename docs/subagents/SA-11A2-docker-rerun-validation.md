# SA-11A2 Docker 实跑复验任务单

## 目标
使用非冲突宿主机端口重跑 Docker 运行态验证，确认 backend / worker / beat / frontend 代理链路。

## 必读文档
- docs/19-route-a-engineering-hardening.md
- docs/21-route-a-orchestration.md
- docs/22-route-a-docker-rerun-validation.md
- docs/deployment.md

## 范围
- 准备 `.env`
- 写入非冲突宿主机端口
- 执行 `docker compose up -d`
- 检查 `docker compose ps`
- 检查 backend / worker / beat 日志
- 验证 health 与前端代理链路

## 不要做
- 不扩展业务功能
- 不进入路线 B
- 不大改 compose 结构

## 验收标准
- 关键服务可起
- health 与代理链路可达
- 若失败，明确新的根因

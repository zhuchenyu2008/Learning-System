# 07-subagent 总拆分计划文档

## 1. 编排原则
- 实现型 subagent 只按指定文档和模块边界实现。
- 所有实现必须以 `fullstack-developer` 为质量基准。
- 每个 subagent 必须回传：改动文件、执行命令、通过项/未通过项/阻塞项。
- 主 agent 将在每轮完成后抽样核验文件与命令结果。

## 2. 串行/并行安排
### 串行主链
1. SA-01 后端基础骨架
2. SA-02 笔记生成链路
3. SA-03 复习与衍生任务链路
4. SA-08 Docker 与部署补齐
5. SA-09 最终验证

### 可并行前端链
- SA-04 前端壳层与主题
- SA-05 笔记模块
- SA-06 复习模块
- SA-07 设置模块

其中：
- SA-05 依赖 SA-04 与 SA-02 API 基本稳定。
- SA-06 依赖 SA-04 与 SA-03 API 基本稳定。
- SA-07 依赖 SA-04 与 SA-01/06 部分 API。

## 3. 任务单清单
- `docs/subagents/SA-01-backend-foundation.md`
- `docs/subagents/SA-02-ingestion-and-note-generation.md`
- `docs/subagents/SA-03-review-summary-mindmap.md`
- `docs/subagents/SA-04-frontend-shell-and-theme.md`
- `docs/subagents/SA-05-frontend-notes-module.md`
- `docs/subagents/SA-06-frontend-review-module.md`
- `docs/subagents/SA-07-frontend-settings-module.md`
- `docs/subagents/SA-08-docker-and-deployment.md`
- `docs/subagents/SA-09-final-validation.md`

## 4. 质量门禁
- 后端：lint / tests / app import / migrations 基础可运行
- 前端：lint / build 通过
- API：关键路由可启动、OpenAPI 生成正常
- Docker：compose 配置可解析
- 验证：至少完成一次端到端主链手工/脚本检查

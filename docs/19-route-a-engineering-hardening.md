# 19-路线A：收尾工程化文档

## 1. 目标
把当前项目从“主链已成立、骨架可交付”推进到“更稳定、可部署、可维护”的工程化状态。

## 2. 子目标拆解
### A1. Docker 实跑验证
- 执行 `docker compose build`
- 执行 `docker compose up`
- 验证 frontend/backend/postgres/redis 启动与互联
- 验证 Nginx 代理与 API 通路

### A2. Worker / Beat 真闭环
- 引入或补齐 Celery app / entrypoint
- 让 worker 可真实消费任务
- 让 beat 可注册最小定时任务
- 与现有 Job 状态流转对齐

### A3. 前端工程质量收尾
- 修掉现有 lint warning
- 清理可明显优化的代码边角
- 保持现有功能不回退

### A4. 前端包体优化
- Mermaid / 重组件按需拆包
- 路由级或模块级动态加载
- 观察 build 输出，降低主要 chunk 体积

### A5. 工程化验收文档
- 输出构建、启动、联通性、已知边界结果
- 明确哪些已经可上线试运行，哪些仍为增强项

## 3. 风险点
- Celery 引入可能牵动现有同步 Job 主链，需要尽量以兼容方式改造
- Docker 实跑可能暴露环境变量与挂载路径问题
- 包体优化需避免破坏 Mermaid 与 Markdown 渲染体验

## 4. 验收标准
- `docker compose build` 通过
- `docker compose up` 后关键服务健康
- worker / beat 可运行
- 前端 lint warning 下降到 0 或剩余项明确
- 前端包体相较当前有可见优化

# 21-路线A实施编排文档

## 1. 当前阶段目标
正式进入路线 A（收尾工程化），按已冻结路线文档推进：
1. Docker build/up 与联通性验证
2. worker / beat 真闭环
3. 前端 lint warning 修整
4. 前端包体优化
5. 路线 A 收口验证与总结

## 2. 子任务拆分
| SA | 目标 | 类型 | 依赖 |
|---|---|---|---|
| SA-11A | Docker build/up 与联通性验证 | 实现/验证 | 当前代码基线 |
| SA-11B | worker / beat 真闭环接入 | 实现 | 当前后端 Job 主链 |
| SA-11C | 前端 lint warning 修整 + 包体优化 | 实现 | 当前前端基线 |
| SA-11D | 路线A最终验证与文档更新 | 验证 | SA-11A/B/C |

## 3. 串并行策略
- SA-11A、SA-11B、SA-11C 可并行推进
- SA-11D 必须最后执行

## 4. 质量门禁
- Docker：`docker compose build` / `docker compose up` 抽样通过
- Worker/Beat：具备最小真实运行能力
- Frontend：warning 清零或明确残留；build 包体有优化证据
- 路线 A 验证文档回填

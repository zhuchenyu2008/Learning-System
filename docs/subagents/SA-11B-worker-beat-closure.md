# SA-11B Worker/Beat 真闭环任务单

## 目标
补齐最小可运行的 worker / beat 闭环，使异步任务与定时任务具备真实基础执行能力。

## 必读文档
- docs/18-roadmap-next-steps.md
- docs/19-route-a-engineering-hardening.md
- docs/21-route-a-orchestration.md

## 范围
- 引入/补齐 Celery app / entrypoint
- 对接现有 Job 主链的最小真实消费
- 提供 beat 最小任务注册
- 补必要配置与基础测试/验证

## 不要做
- 不扩展路线 B 体验增强
- 不大改现有业务边界

## 验收标准
- worker/beat 可启动
- 至少有最小任务可真实执行

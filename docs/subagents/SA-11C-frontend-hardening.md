# SA-11C 前端工程质量收尾任务单

## 目标
修整前端 lint warning，并做包体优化。

## 必读文档
- docs/18-roadmap-next-steps.md
- docs/19-route-a-engineering-hardening.md
- docs/21-route-a-orchestration.md

## 范围
- 修现有 router warning
- 尽量降到 0 warning
- 做 Mermaid / 重依赖拆包或 manualChunks 优化
- 跑 lint/build，对比优化结果

## 不要做
- 不扩展新业务功能
- 不进入路线 B

## 验收标准
- warning 清零或给出残留说明
- build 产物体积有优化证据

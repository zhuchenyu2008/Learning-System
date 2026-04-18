# SA-12F 路线B收尾修整任务单

## 目标
解决路线 B 的两个尾项：notes 页面观看时长上报闭环 + 后端测试环境依赖补齐与回归。

## 必读文档
- docs/20-route-b-product-enhancement.md
- docs/25-route-b-orchestration.md
- docs/28-route-b-tail-remediation.md

## 范围
- 在前端 notes 页面补最小真实 watch_seconds 上报链路
- 补齐 celery 测试环境依赖
- 重跑关键测试与必要构建

## 不要做
- 不扩展路线 B 新功能
- 不大改现有 API
- 不进入路线外新需求

## 验收标准
- watch_seconds 闭环落地
- 后端关键测试可执行并尽量通过
- 给出 through/blocked/failed 或通过项/未通过项/阻塞项

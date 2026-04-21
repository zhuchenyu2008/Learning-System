# SA-20E 用户活动概览异常排查任务单

## 目标
排查并修复“用户活动概览数据全 0”的问题，明确是否为程序问题，并让统计链路产生真实数据。

## 必读文档
- docs/26-route-b-knowledgepoint-activity.md
- docs/39-watch-seconds-bugfix.md
- docs/48-first-feedback-round2-remediation.md

## 范围
- 排查登录、页面访问、note view、watch_seconds、review log 到 user activity snapshot 的整条链路
- 明确 HTTP/代理是否影响统计（通常不应影响）
- 修复数据未更新或读取错误问题
- 补必要测试与验证

## 不要做
- 不扩展新的分析系统
- 不大改无关业务模块

## 验收标准
- 能明确根因
- 活动概览出现真实非零数据或能通过可复现步骤生成

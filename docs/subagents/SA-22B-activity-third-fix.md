# SA-22B 用户活动概览继续排障任务单

## 目标
继续排查“用户活动概览仍全 0”的问题，并真正让前台操作能在概览里体现为非零数据。

## 必读文档
- docs/26-route-b-knowledgepoint-activity.md
- docs/39-watch-seconds-bugfix.md
- docs/48-first-feedback-round2-remediation.md
- docs/49-third-feedback-remediation.md

## 范围
- 实测从前端操作到后端 snapshot 聚合全链路
- 排查是否前端未触发、后端未记、管理接口未读、页面未显
- 修复根因并给出复现步骤

## 不要做
- 不扩展全新分析系统
- 不大改无关业务

## 验收标准
- 可复现地产生非零活动数据
- 管理侧概览正常显示

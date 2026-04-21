# SA-22I 活动概览第四轮排障任务单

## 目标
继续排查“用户活动概览仍全 0”的真实使用链路问题，必须结合当前 Docker 运行环境与前端真实操作链路判断。

## 必读文档
- docs/26-route-b-knowledgepoint-activity.md
- docs/39-watch-seconds-bugfix.md
- docs/48-first-feedback-round2-remediation.md
- docs/53-fourth-feedback-remediation.md

## 范围
- 结合当前运行中的 Docker 环境
- 实测登录、打开笔记、watch flush、review、管理员查看概览
- 判断是前端未触发、后端未记、接口未读、页面没显，还是排序/筛选问题仍未彻底解决
- 做最小修复

## 不要做
- 不扩展新分析系统
- 不大改无关业务模块

## 验收标准
- 给出可稳定复现非零数据的真实链路，或彻底修复原因

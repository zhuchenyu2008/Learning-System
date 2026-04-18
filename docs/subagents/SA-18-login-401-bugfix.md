# SA-18 登录401缺陷修复任务单

## 目标
修复当前 Docker 环境下登录 401 的问题。

## 必读文档
- docs/29-final-delivery-summary.md
- docs/40-docker-fresh-rerun-for-manual-test.md
- docs/41-login-401-bugfix.md

## 范围
- 排查 backend auth / seed admin / Docker entrypoint / 前端登录请求链路
- 修复登录主链
- 重跑 Docker 下登录验证

## 不要做
- 不扩展新功能
- 不处理无关问题

## 验收标准
- 登录 401 根因明确
- 登录成功可复现
- 回传测试账号与验证结果

# SA-21A Docker普通流程阻塞修整任务单

## 目标
修复 `frontend/src/pages/register-page.test.tsx` 语法错误，并重跑普通 Docker 流程。

## 必读文档
- docs/46-docker-normal-rerun.md
- docs/47-docker-normal-rerun-blocker-fix.md

## 范围
- 只修该测试文件语法问题
- 重跑 docker compose down/build/up/ps
- 验证前端页面、backend health、frontend 代理 health

## 不要做
- 不扩展新功能
- 不改无关文件

## 验收标准
- build 通过
- Docker 普通流程通过

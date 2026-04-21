# SA-27D worker 数据库访问模型修复任务单

## 目标
修复 worker 执行任务时的数据库访问并发冲突，打通真实笔记生成异步链路。

## 必读文档
- docs/56-sixth-feedback-followup-bugs.md
- docs/57-note-generation-500-followup.md
- docs/58-note-generation-500-followup-rerun.md
- docs/59-worker-db-concurrency-remediation.md

## 范围
- 修 worker 任务中的数据库访问方式
- 修与 Celery/async SQLAlchemy/asyncpg 冲突直接相关的实现
- 重跑真实 Docker 环境：登录 -> 上传 txt/md/docx -> 生成笔记 -> 查 job -> 查 notes

## 不要做
- 不扩展新功能
- 不大改无关模块

## 验收标准
- worker 稳定执行任务
- job 不再卡 pending
- 至少一条真实来源资产生成成功

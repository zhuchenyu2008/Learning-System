# 60-笔记生成任务后半段收尾阻塞修整文档

## 1. 背景
上一轮已确认并修复 worker 数据库并发访问根因，当前新任务链路中已不再出现 `cannot perform operation: another operation is in progress`。

但真实环境里仍存在新的后半段阻塞：
- 3 个来源文件仅生成出 2 条 note
- job 仍停留在 `running`
- 说明问题已从数据库并发前置故障，转移到“单文件处理 / 写回 / Job 状态收尾”阶段

## 2. 当前目标
继续沿真实阻塞点排查并修复：
1. 第 3 个 source asset 为什么没有完成
2. job 为什么没有从 `running` 进入 `completed` / `failed`
3. 笔记生成主链在真实 Docker 环境下如何完整闭环

## 3. 排查范围
- `backend/app/services/note_generation_service.py`
- `backend/app/services/job_service.py`
- `backend/app/worker/tasks.py`
- 与单文件内容提取、LLM 返回处理、note 写入、Job 收尾直接相关的最小范围

## 4. 不要做
- 不回头重做已解决的 DB concurrency 问题
- 不扩展新功能
- 不大改无关 provider/前端逻辑

## 5. 验收标准
- 真实链路下 3 个来源文件全部处理完成，或明确给出唯一阻塞根因
- job 不再无故卡在 `running`
- 至少一轮真实 Docker 环境验证有完整证据

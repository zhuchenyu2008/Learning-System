# SA-27E 笔记生成后半段收尾阻塞修复任务单

## 目标
继续修复当前真实环境下笔记生成任务“后半段卡住”的问题。

## 必读文档
- docs/56-sixth-feedback-followup-bugs.md
- docs/57-note-generation-500-followup.md
- docs/58-note-generation-500-followup-rerun.md
- docs/59-worker-db-concurrency-remediation.md
- docs/60-note-generation-tail-fix.md

## 范围
- 真实 Docker 环境下：登录 -> 上传 txt/md/docx -> 生成 -> 查 job -> 查 notes -> 查 logs
- 聚焦单文件处理、LLM 返回处理、note 写入、Job 收尾状态更新
- 必要时做最小修复

## 不要做
- 不扩展新功能
- 不大改无关模块
- 不重复回头处理已解决的数据库并发根因

## 验收标准
- 3 个来源文件全部完成或给出唯一精确阻塞根因
- job 不再卡在 running
- 回传实际命令、实际 HTTP 返回、through/blocked/failed 与问题清单

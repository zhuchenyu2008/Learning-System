# SA-23 回退 SA-22A 任务单

## 目标
按用户要求撤销 SA-22A 的前端改动。

## 必读文档
- docs/49-third-feedback-remediation.md
- docs/51-revert-sa22a.md

## 范围
- 定向回退 SA-22A 相关前端改动
- 保留其他有效修复
- 跑前端 build 验证

## 不要做
- 不扩展新功能
- 不顺手回退无关改动
- 不回退后端逻辑

## 验收标准
- SA-22A 改动被撤销
- 前端 build 通过
- 回传变更与验证结果

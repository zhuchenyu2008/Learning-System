# SA-01C 后端密码哈希兼容修整任务单

## 目标
只修复后端密码哈希与依赖兼容问题，让 backend tests 恢复通过。

## 必读文档
- docs/00-main-task.md
- docs/08-foundation-remediation-plan.md
- docs/10-backend-password-hash-remediation.md
- docs/subagents/SA-01A-backend-remediation.md
- docs/subagents/SA-01B-venv-retry-validation.md

## 当前已知问题
- `ValueError: password cannot be longer than 72 bytes, truncate manually if necessary`
- `AttributeError: module 'bcrypt' has no attribute '__about__'`

## 范围
- 只修密码哈希兼容问题
- 允许修改 security 实现与相关依赖约束
- 跑 backend tests 验证

## 不要做
- 不扩展业务功能
- 不改前端
- 不进入 SA-02/SA-03

## 验收标准
- backend tests 通过
- 认证逻辑保持合理、安全

## 回传要求
- 改动文件列表
- 执行命令列表
- 通过项
- 未通过项
- 阻塞项

# SA-22G 内阴影收敛修整任务单

## 目标
按用户反馈收掉当前前端中过度使用的内阴影，保留织物质感但不再“处处 inset”。

## 必读文档
- docs/44-frontend-nav-mobile-copy-registration.md
- docs/49-third-feedback-remediation.md
- docs/50-remove-heavy-inset-shadow.md

## 范围
- 调整 fabric 样式体系
- 修受影响最明显的页面/控件表现
- 跑前端 build 验证

## 不要做
- 不扩展新功能
- 不改后端逻辑
- 不引入新的重风格偏差

## 验收标准
- 内阴影明显减少
- UI 仍符合织物质感方向
- build 通过

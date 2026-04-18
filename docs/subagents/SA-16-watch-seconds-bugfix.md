# SA-16 watch_seconds 统计缺陷修复任务单

## 目标
按方案 A 修复 watch_seconds 导致访问次数重复累计的统计 bug。

## 必读文档
- docs/29-final-delivery-summary.md
- docs/39-watch-seconds-bugfix.md
- docs/34-test-matrix.md

## 范围
- 拆分 notes detail 与 watch 上报接口语义
- 更新前端 notes 页面上报逻辑
- 补后端/前端相关测试
- 跑必要回归验证

## 不要做
- 不扩展新功能
- 不大改 activity 系统
- 不处理无关性能问题

## 验收标准
- `GET /notes/{id}` 不再承担 watch 上报语义
- `POST /notes/{id}/watch` 落地
- watch 不再重复累计 view 次数
- 测试通过

## 回传要求
- 改动文件列表
- 执行命令列表
- 通过项
- 未通过项
- 阻塞项

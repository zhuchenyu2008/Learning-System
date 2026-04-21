# SA-26B 上传/生成/活动统计链路排障任务单

## 目标
修复上传/生成/活动统计链路中的剩余问题：docx/txt/md 500、70MB wav 413、活动概览关键字段仍为 0。

## 必读文档
- docs/39-watch-seconds-bugfix.md
- docs/45-notes-upload-first.md
- docs/54-fifth-feedback-remediation.md
- docs/55-sixth-feedback-remediation.md

## 范围
- 排查 docx/txt/md 上传后生成笔记 500 的真实根因并修复
- 排查 70MB wav 上传 413 的来源（nginx/backend/body size）并修复最小必要链路
- 排查活动概览中观看时长、页面访问仍为 0 的真实使用链路问题并修复
- 补必要测试与验证

## 不要做
- 不扩展新功能
- 不大改无关 provider/活动系统结构

## 验收标准
- docx/txt/md 生成链路通过
- 70MB wav 上传链路通过或有受控限制与清晰提示
- 活动概览关键字段出现真实非零数据

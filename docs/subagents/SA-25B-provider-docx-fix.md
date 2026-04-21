# SA-25B Provider 与 docx 生成链路排障任务单

## 目标
排查并修复：
1. ASR provider 配置 502
2. OCR/多模态 provider 配置 502
3. LLM/Embedding 已通过后，docx 上传生成笔记时报 500

## 必读文档
- docs/29-final-delivery-summary.md
- docs/45-notes-upload-first.md
- docs/54-fifth-feedback-remediation.md

## 范围
- 排查 OpenAI-compatible provider 探活请求
- 排查 SiliconFlow + SenseVoiceSmall / DeepSeek-OCR 配置兼容性
- 排查 docx 上传后进入 notes 生成链的异常点
- 修复最小必要链路并补测试/验证

## 不要做
- 不扩展新功能
- 不大改无关 provider 结构

## 验收标准
- 502 根因明确并修复
- docx 生成笔记链路通过

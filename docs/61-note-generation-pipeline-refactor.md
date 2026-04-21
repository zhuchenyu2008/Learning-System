# 61-AI笔记生成主链重构文档

## 1. 用户新要求
AI 生成笔记的正确流程应为：
1. 各种来源资产（音频 / 视频 / 图片 / PDF / docx / txt / md 等）
2. 先通过对应手段统一转成**规范化文本**
3. 再把规范化文本交给 LLM 生成最终笔记

## 2. 当前问题
当前实现中，部分来源类型在“提取/清洗/结构化文本”与“AI 生成笔记”之间的边界不够清晰，导致：
- 某些来源直接在半结构化状态下进入生成链
- provider 兼容差异被混进笔记生成流程
- 调试和错误定位困难

## 3. 重构目标
将笔记生成主链收敛为统一三段式：
1. SourceAsset Ingestion
2. Text Extraction & Normalization
3. LLM Note Generation

## 4. 设计要求
### 4.1 来源到文本
- 音频/视频：ASR -> 文本
- 图片/PDF：OCR/多模态 -> 文本
- docx/txt/md：解析/清洗 -> 文本
- 所有来源都输出统一 `extracted_text` 与 `extraction_metadata`

### 4.2 文本到笔记
- LLM 只接收规范化文本与元数据
- 不直接处理原始二进制来源
- 生成 Markdown 笔记并写回 Note

### 4.3 可观测性
- Job 日志明确分阶段：ingest / extract / normalize / generate / write
- 任一阶段失败都能定位

## 5. 本轮实现范围
- 不扩展新功能面
- 只重构 notes 生成主链内部流程与日志/状态结构
- 保持现有 API 尽量兼容

## 6. 验收标准
- notes 生成链路代码结构符合“三段式”
- 至少 txt/md/docx 与一个多媒体来源路径能在新结构下通过
- 日志中可看出“先提取文本，再生成笔记”

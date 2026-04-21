# 66-笔记生成全流程总体架构

## 1. 目标架构
统一五段式：
1. Source Ingestion
2. Source-specific Text Extraction
3. Text Normalization
4. Related Note Retrieval via Embedding
5. LLM Note Generation + Classification + Naming + Writeback

## 2. 数据流
- 原始来源文件上传为 `SourceAsset`
- 根据文件类型进入：解析 / OCR / STT
- 输出统一 `normalized_text`
- 使用 embedding 对现有笔记库进行相似检索，得到 `retrieved_context`
- 组合：当前时间 + 来源元数据 + normalized_text + retrieved_context + prompt policy
- 交给 LLM 生成结构化 Markdown、学科分类、标题、写入路径
- 写回 Note 与 Job result/log

## 3. 设计原则
- 先文本化，再检索，再生成
- 检索与生成分离，便于观测与调试
- 失败要能区分：提取失败 / 检索失败 / 生成失败 / 写回失败
- 目录与标题应由生成结果驱动，而不是仅由源文件名驱动

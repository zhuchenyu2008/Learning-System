# 65-笔记生成全流程当前仓库与现状分析

## 1. 已知现状
- 项目已有 notes 生成主链：ingest -> extract -> normalize -> generate -> write
- 现有 provider 类型主要覆盖 LLM / OCR / STT
- 当前纯文本、PDF、图片、音频路径都通过 `OpenAICompatibleProviderAdapter` 聚合
- 已确认 PDF 在无 provider 时会落入 placeholder；目前已加门禁避免生成垃圾 note

## 2. 初步差距
1. 现有主链中尚未明确存在“embedding 检索相关笔记”阶段
2. provider 配置端点 / 数据模型可能尚未完整表达 embedding provider
3. LLM prompt 尚未完全按用户指定的两份 skill 口径组织
4. 当前标题、目录、学科分类大概率仍是文件名导向，不是 AI 分类导向
5. 当前时间上下文注入需要核实
6. 真实 SiliconFlow 配置在 Docker 环境中尚未完成全来源闭环验证

## 3. 当前高风险点
- embedding 阶段缺失会导致用户认为主链根本没按要求实现
- 目录与命名策略若继续用原文件名，会与 Obsidian 学习体系冲突
- PDF / 图片 / 音频链虽然可跑，但不代表最终笔记质量合格
- 使用用户提供的真实 API key 做测试时，必须尽量只写入运行配置，不在文档或日志里扩散敏感值

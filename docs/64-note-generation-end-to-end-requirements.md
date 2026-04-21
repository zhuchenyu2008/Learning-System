# 64-笔记生成全流程需求拆解

## 1. 输入类型与处理规则
### 1.1 纯文本来源
- 支持：txt / md / docx
- 流程：内容解析 -> 规范化文本 -> embedding 检索相关笔记 -> LLM 生成笔记

### 1.2 文档/图像来源
- 支持：pdf / 图片
- 流程：OCR / 多模态识别 -> 规范化文本 -> embedding 检索相关笔记 -> LLM 生成笔记

### 1.3 音频来源
- 支持：wav / mp3 等
- 流程：ASR -> 规范化文本 -> embedding 检索相关笔记 -> LLM 生成笔记

## 2. 模型要求
- Embedding：`Qwen/Qwen3-Embedding-8B`
- LLM：`deepseek-ai/DeepSeek-V3.2`
- OCR：`deepseek-ai/DeepSeek-OCR`
- STT：`FunAudioLLM/SenseVoiceSmall`
- baseURL：`https://api.siliconflow.cn/v1`
- key：由用户已提供，用于真实环境测试与配置注入

## 3. 检索要求
- 每次生成前必须进行 embedding 检索
- 检索对象至少包含现有笔记库中的相关笔记
- 检索结果需作为 LLM 上下文的一部分

## 4. 生成要求
- 参考 skill：`obsidian-spaced-recall`、`obsidian-study-notes`
- 注入当前日期 / 时间 / 来源信息
- 由 AI 决定学科分类
- 标题格式：`标题-日期-时间`
- 落库目录按学科分类

## 5. 验收要求
- 真实 SiliconFlow 配置下，对 txt/md/docx/pdf/image/audio 做端到端测试
- 不只验证 job 成功，还要抽查笔记质量
- 需明确问题清单与对应方案

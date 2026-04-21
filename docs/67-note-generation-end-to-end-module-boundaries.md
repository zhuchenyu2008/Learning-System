# 67-笔记生成全流程模块边界

## 1. Provider 配置模块
- 负责保存 / 读取 LLM、Embedding、OCR、STT provider 配置
- 不负责具体业务编排

## 2. 内容提取模块
- 输入：SourceAsset
- 输出：统一 `ProviderExtractionResult` / `normalized_text`
- 不负责检索与最终笔记组织

## 3. 检索模块
- 输入：normalized_text / 来源元数据
- 输出：相关笔记片段、候选笔记、检索元数据
- 不负责最终 Markdown 生成

## 4. 生成模块
- 输入：normalized_text + retrieved_context + time_context + policy_prompt
- 输出：笔记正文、学科分类、标题、路径建议

## 5. 写回模块
- 将生成结果落盘为 Obsidian Markdown
- 更新 Note / Job / frontmatter / result_json

## 6. 测试模块
- 负责真实 SiliconFlow 配置注入
- 分来源做端到端回归与产物质量检查

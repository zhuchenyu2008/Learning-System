# 72-笔记生成全流程运行与配置说明

## 1. 本轮测试使用的目标配置
- baseURL：SiliconFlow OpenAI-compatible endpoint
- LLM：DeepSeek-V3.2
- Embedding：Qwen3-Embedding-8B
- OCR：DeepSeek-OCR
- STT：SenseVoiceSmall

## 2. 安全要求
- API key 仅写入运行配置，不在普通文档中重复扩散
- 测试日志与汇报中不回显完整密钥

## 3. 运行方式
- 使用当前 Docker 环境
- 通过真实 HTTP 流程：登录 -> 配置 AI -> 上传来源 -> generate -> 查 job/log/note

## 4. 文档冻结规则
- 在 SA-30/31/32 回传前，本说明只冻结测试目标与安全要求
- 具体实现改造方案待主 agent 汇总后定稿

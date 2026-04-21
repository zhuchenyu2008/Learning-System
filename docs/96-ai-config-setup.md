# 96-AI配置写入任务文档

## 1. 目标
将用户提供的真实 SiliconFlow AI 配置写入当前 `learning-system` 运行实例，用于后续人工测试。

## 2. 配置目标
- baseURL: `https://api.siliconflow.cn/v1`
- Embedding: `Qwen/Qwen3-Embedding-8B`
- LLM: `deepseek-ai/DeepSeek-V3.2`
- OCR: `deepseek-ai/DeepSeek-OCR`
- STT: `FunAudioLLM/SenseVoiceSmall`
- API key: 由用户已提供，写入运行配置但不在汇报中回显完整值

## 3. 执行范围
- 登录当前运行实例后台接口
- 写入 `/api/v1/settings/ai`
- 读取 `/api/v1/settings/ai` 做最小核验
- 可选 probe 各 provider 以确认可达

## 4. 不做事项
- 不改代码
- 不重启 Docker
- 不扩张到无关设置

## 5. 验收标准
- 四类 provider 配置已写入当前实例
- 读取设置可见 `has_api_key=true` 与正确 model/baseURL
- 如 probe 成功，则补充可达证据

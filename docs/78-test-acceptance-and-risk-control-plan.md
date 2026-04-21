# 78-测试、验收与风险控制详细计划

## 1. 测试目标
不仅验证“能不能生成 note”，还要验证：
- 主链是否正确
- 检索是否执行
- 命名是否正确
- 目录是否正确
- 内容是否有业务价值

## 2. 测试分层

### 2.1 配置测试
- llm provider probe
- embedding provider probe
- ocr provider probe
- stt provider probe
- `/settings/ai` 脱敏验证

### 2.2 单元测试
- embedding adapter 行为
- retrieval service 结果
- subject normalization
- path builder
- generation output parser

### 2.3 集成测试
- txt/md/docx -> retrieve -> generate
- pdf/image -> OCR -> retrieve -> generate
- wav/mp3 -> STT -> retrieve -> generate

### 2.4 真实环境回归
- 使用 SiliconFlow 配置
- 对 6 类来源逐一跑
- 轮询 job 直到完成
- 抽样检查 note 内容

## 3. 每类来源验收项

### 共通验收项
1. 上传成功
2. extract 成功
3. normalize 成功
4. retrieve 执行成功
5. generate 成功
6. write 成功
7. 日志包含 retrieve
8. result_json 含 retrieval_summary
9. 标题符合 `标题-日期-时间`
10. 路径在学科目录下

### 额外质量验收项
#### txt/md/docx
- 笔记内容不应只是原文复写
- 应有结构化学习整理

#### pdf/image
- 对 OCR 失败或空文本，应 fail 或明确警告
- 不允许 completed 但正文只有“无法识别”说明

#### audio
- 对空音频/纯噪声样本要能识别质量低
- 不允许把单个无意义词当业务成功

## 4. 风险控制

### 风险 1：embedding retrieval 接入后 token 激增
对策：
- retrieval context 截断
- top_k 控制
- snippet 摘要化

### 风险 2：LLM 返回 JSON 不稳定
对策：
- schema 校验
- fail fast + retry

### 风险 3：分类错误导致目录错放
对策：
- subject normalization
- fallback 未分类

### 风险 4：历史 note 向量化太慢
对策：
- 初版先 small-scale 检索
- 后续再做缓存

### 风险 5：真实 API 成本与速率限制
对策：
- 测试素材控制规模
- 每类先小样本验证

## 5. 最终验收口径
本轮不以“所有来源都生成 completed”为标准，而以以下标准为准：
1. 主链正确
2. retrieval 真实执行
3. 产物结构符合要求
4. 低质量输入不会伪装成功
5. 多来源真实测试下系统行为可解释、可追踪、可交付

# 77-分阶段实施与任务拆分详细计划

## 1. 总体原则
- 先改最上游契约，再改主链，再改验证
- 每个 subagent 只做一小块边界清晰的工作
- 先打通 retrieval + 结构化输出，再做质量修整

## 2. 阶段拆分

### 阶段 1：配置安全与契约准备
目标：
- 修掉 `/settings/ai` API key 回显
- 冻结 provider、retrieval、generation output 契约

交付：
- settings 脱敏方案
- 新/旧契约兼容策略

### 阶段 2：embedding 运行时接入
目标：
- 在 adapter 中增加 embedding 调用
- 允许真实 embeddings 请求

交付：
- embedding runtime API
- 单元测试/探活兼容

### 阶段 3：retrieval service 接入
目标：
- 新增 note retrieval service
- 先用 note 正文切片完成初版检索

交付：
- retrieval result 结构
- retrieval logging
- retrieve summary

### 阶段 4：主链插入 retrieve 阶段
目标：
- note_generation_service 改为：
  - ingest
  - extract
  - normalize
  - retrieve
  - generate
  - write

交付：
- retrieve 阶段日志
- result_json 新增 retrieval_summary

### 阶段 5：生成输出结构化
目标：
- 不再只返回 markdown string
- 返回 title/subject/body 等结构化结果

交付：
- generation output parser
- JSON/schema 校验

### 阶段 6：命名与目录落库
目标：
- 学科分类规范化
- 标题-日期-时间
- path builder

交付：
- 学科目录落库
- 重名处理

### 阶段 7：质量门禁强化
目标：
- image/pdf/audio 对“completed 但无业务价值”进行纠偏
- 区分技术成功与业务失败

交付：
- 质量标记
- fail fast / warning 策略

### 阶段 8：真实环境全量回归
目标：
- 用 SiliconFlow 重新测 txt/md/docx/pdf/image/audio
- 抽样检查最终笔记质量

交付：
- 真实回归报告
- 风险清单

## 3. 建议 subagent 切分

### SA-33：settings 脱敏与配置契约修整
负责：
- `/settings/ai` 脱敏
- provider 契约兼容

### SA-34：embedding runtime + retrieval service
负责：
- adapter embed 方法
- retrieval service 初版

### SA-35：note generation retrieve 接入 + 结构化输出
负责：
- 主链改造
- generation output 结构化

### SA-36：学科分类、命名、路径写回
负责：
- subject normalization
- path builder
- frontmatter/path/title 写回

### SA-37：质量门禁与真实回归
负责：
- image/pdf/audio 质量纠偏
- 全来源回归验证

## 4. 串并行关系
- SA-33 可先行
- SA-34 完成前，SA-35 不应开工
- SA-35 完成后，SA-36 再接
- SA-37 必须最后做

## 5. 每阶段最小验收
- 阶段 1：key 不再回显
- 阶段 2：embedding 真请求可发出
- 阶段 3：retrieval_summary 可生成
- 阶段 4：job 日志有 retrieve
- 阶段 5：LLM 结果带 title/subject/body
- 阶段 6：文件按学科目录、标题-日期-时间落库
- 阶段 7：低质量 OCR/STT 不再伪装成功
- 阶段 8：真实多来源结果可验收

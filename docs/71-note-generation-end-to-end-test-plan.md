# 71-笔记生成全流程测试与验证计划

## 1. 配置验证
- 后台 AI settings 中写入 llm / embedding / ocr / stt 四类模型
- provider probe 分别验证可达性

## 2. 来源覆盖
- 文本：txt / md / docx
- 图文：pdf / image
- 音频：wav / mp3

## 3. 每条测试链检查项
- 上传成功
- 提取成功
- 规范化文本是否合理
- 检索阶段是否执行
- LLM 生成是否执行
- 生成笔记标题是否为 `标题-日期-时间`
- 是否落入 AI 决定的学科目录
- 产出 Markdown 质量是否正常

## 4. 失败分层
- provider 配置失败
- 来源提取失败
- embedding 检索失败
- 生成失败
- 写回失败
- 质量不达标但链路成功

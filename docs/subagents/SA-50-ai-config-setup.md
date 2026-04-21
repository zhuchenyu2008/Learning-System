# SA-50 AI配置写入任务单

## 目标
把用户提供的 AI 配置写入当前 `learning-system` 运行实例，并做最小核验。

## 必读文档
- docs/95-final-pre-handoff-ts-fix-and-rerun-main.md
- docs/96-ai-config-setup.md

## 必做事项
1. 登录后台接口
2. 写入 llm / embedding / ocr / stt 四类 provider
3. 读取设置确认写入成功
4. 尽量 probe 各 provider 可达

## 不要做
- 不改代码
- 不重启 Docker
- 不在回传中暴露完整 API key

## 验收标准
- 配置已写入
- 最小核验完成

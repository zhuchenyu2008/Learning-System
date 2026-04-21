# SA-45B docx失败日志定位与链路补强任务单

## 目标
定位 docx 在用户现场“无法生成”的高可信根因，并在当前代码范围内补强 docx 提取与日志链路。

## 必读文档
- docs/90-post-test-issue-master-table.md
- docs/91-next-fix-wave-orchestration.md
- docs/93-p1-fixes-main.md

## 重点范围
- `backend/app/services/safe_file_service.py`
- `backend/app/services/file_types.py`
- `backend/app/services/note_generation_service.py`
- `backend/app/worker/tasks.py`
- docx 相关测试最小范围

## 必做事项
1. 复核 docx 提取实现与类型归类
2. 增强 docx extraction / generation 失败日志可观测性
3. 尽量补一个更贴近真实样本的 docx 回归或链路测试
4. 输出：修复结果，或唯一精确根因

## 不要做
- 不扩张到 UI 文案/artifact 分组/卡片/复习时长

## 验收标准
- docx 问题要么被修复，要么被收敛到唯一根因并有证据

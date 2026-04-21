# SA-53 思维导图质量约束修复任务单

## 目标
修复思维导图内容混乱的问题，重点收紧 mindmap 生成提示与输入边界，而不是只处理渲染。

## 必读文档
- docs/97-new-issues-wave-main.md
- docs/98-new-issues-breakdown.md
- docs/99-new-issues-orchestration.md

## 重点范围
- `backend/app/services/artifact_service.py`
- 如有必要，相关 mindmap 前端验证最小范围
- 必要测试

## 验收标准
- mindmap prompt / output 约束明显加强
- 对现有样本生成结果质量有改善，或能明确指出剩余受限点

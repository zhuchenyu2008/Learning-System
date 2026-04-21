# SA-36 学科分类、命名与路径写回任务单

## 目标
在 retrieval 与结构化生成输出已经存在的前提下，完成 subject normalization、标题-日期-时间命名、学科目录落库与 frontmatter/path/title 写回。

## 必读文档
- docs/73-note-generation-detailed-solution.md
- docs/75-prompt-time-and-output-structure-design.md
- docs/76-subject-classification-naming-and-path-design.md
- docs/77-phased-implementation-and-task-breakdown.md
- docs/78-test-acceptance-and-risk-control-plan.md
- docs/79-pre-implementation-control-freeze.md

## 前置依赖
- SA-35 已完成并提供结构化 generation output

## 重点范围
- `backend/app/services/note_generation_service.py`
- 可新增 path builder / subject normalization 辅助模块
- `backend/app/models/note.py`（仅在确有必要时最小调整）
- frontmatter 写入逻辑相关最小范围

## 必做事项
1. 建立 subject normalization 规则。
2. 标题最终格式由系统拼接为：`标题-YYYY-MM-DD-HHmm`。
3. relative_path 按学科目录落库，例如：`notes/subjects/<学科>/...`。
4. 做路径清洗、非法字符处理、重名处理。
5. frontmatter / note.title / relative_path 与最终产物保持一致。

## 不要做
- 不处理 image/pdf/audio 的质量门禁修整
- 不扩张无关表结构，除非绝对必要

## 验收标准
- 最终路径按学科目录
- 标题符合 `标题-日期-时间`
- 重名与非法路径问题可处理
- 测试通过

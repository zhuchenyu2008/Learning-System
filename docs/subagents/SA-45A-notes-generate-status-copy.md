# SA-45A 生成页状态文案与job状态联动任务单

## 目标
修复笔记生成页的状态文案，让 queued/running/completed/failed 在 UI 中正确表达，不再出现“已创建任务，生成0篇笔记”的误导。

## 必读文档
- docs/90-post-test-issue-master-table.md
- docs/91-next-fix-wave-orchestration.md
- docs/93-p1-fixes-main.md

## 重点范围
- `frontend/src/pages/notes/notes-generate-page.tsx`
- `frontend/src/lib/notes-api.ts`
- `frontend/src/types/notes.ts`
- 与 jobs 状态轮询/提示文案直接相关的最小范围

## 必做事项
1. queued/running/completed/failed 四阶段文案分离
2. 初始创建任务后显示“正在生成”，而不是生成0篇
3. 若有必要，引入最小 job 轮询或复用现有 jobs 查询能力
4. 补最小前端测试

## 不要做
- 不扩张到 docx / artifact 分组 / 卡片 / 复习时长

## 验收标准
- 创建任务后文案正确
- 完成后文案正确
- 失败态可见

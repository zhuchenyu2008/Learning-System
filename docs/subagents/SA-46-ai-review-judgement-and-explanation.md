# SA-46 复习AI判分与讲解任务单

## 目标
在当前 review session 基础上，最小可行接入 AI judge + explanation，让复习从“纯手工评分”升级为“AI 建议评分 + 讲解 + 用户确认/覆盖”的流程。

## 必读文档
- docs/90-post-test-issue-master-table.md
- docs/91-next-fix-wave-orchestration.md
- docs/94-p2-ai-review-judgement-main.md
- 参考：obsidian-spaced-recall / obsidian-study-notes 的相关原则

## 必做事项
1. 设计 review answer 提交流程
2. AI 返回至少：
   - score suggestion / rating suggestion
   - correctness judgement
   - expected answer
   - concise explanation
3. 用户可确认 AI 建议评分，或手动覆盖
4. 最终再写 review log / 更新 FSRS
5. 补最小测试或链路验证

## 重点范围
- backend/app/api/v1/endpoints/review.py
- backend/app/services/review_service.py
- backend/app/schemas/review.py
- frontend/src/pages/review/review-session-page.tsx
- frontend/src/lib/review-api.ts

## 不要做
- 不扩张到新卡片体系重构
- 不扩张到无关页面
- 不一次性做复杂多轮对话 agent，只做最小 judge/explain 流程

## 验收标准
- review session 内可提交答案
- 可收到 AI 评分建议与讲解
- 用户确认/覆盖后可正常落 review log

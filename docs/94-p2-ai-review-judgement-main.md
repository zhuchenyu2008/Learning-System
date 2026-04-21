# 94-P2修复主文档

## 1. 本轮范围
本轮只修 P2 一项：复习时 AI 判分与讲解。

## 2. 修复目标
- 在当前 review session / FSRS 流程基础上，接入 AI judge step
- 支持：用户作答 -> AI 给评分建议 -> AI 给讲解 -> 用户确认/覆盖 -> 写 review log / 更新复习状态
- 保持 AI judge 与最终 FSRS 落库之间可追踪、可回退、可人工纠偏

## 3. 设计原则
1. AI 先做“建议评分”，不直接无条件接管 FSRS
2. 讲解必须结合当前题目、标准答案、用户答案，并尽量结合检索到的相关上下文
3. 复习题本身应尽量是可短答、可判对错的最小记忆单元
4. review session 仍是主流程，AI judge 是其判分与讲解增强层

## 4. 影响范围
- `backend/app/api/v1/endpoints/review.py`
- `backend/app/services/review_service.py`
- `backend/app/schemas/review.py`
- `frontend/src/pages/review/review-session-page.tsx`
- `frontend/src/lib/review-api.ts`
- 与 AI judge / explanation 直接相关的最小测试范围

## 5. 验收标准
1. 用户可以提交答案，而不是只点 Again/Hard/Good/Easy
2. 系统能返回 AI 评分建议与讲解
3. 用户可确认/覆盖评分后再写入 review log
4. AI judge 失败时有可解释回退，不拖垮复习会话

# SA-51 复习卡片生成链审计与修复任务单

## 目标
确认并修复当前 review_card_generation 虽然有独立任务，但仍未真正使用 AI 生成卡片的问题。

## 必读文档
- docs/97-new-issues-wave-main.md
- docs/98-new-issues-breakdown.md
- docs/99-new-issues-orchestration.md
- 参考：obsidian-study-notes / obsidian-spaced-recall 中关于卡片独立生成、最小记忆单元、可判分性的原则

## 重点范围
- `backend/app/services/review_service.py`
- `backend/app/worker/tasks.py`
- `backend/app/api/v1/endpoints/review.py`
- 必要的 review tests

## 验收标准
- 能明确说明当前卡片任务是否走 AI
- 若未走 AI，则补成最小可行 AI 卡片生成链或给出唯一受限根因
- 保留独立异步任务形态

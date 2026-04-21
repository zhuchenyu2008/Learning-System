# SA-45D 笔记后异步生成复习卡片任务单

## 目标
在主笔记生成完成后，引入独立的复习卡片派生任务链，而不是继续依赖手工 bootstrap 作为唯一方式。

## 必读文档
- docs/90-post-test-issue-master-table.md
- docs/91-next-fix-wave-orchestration.md
- docs/93-p1-fixes-main.md

## 重点范围
- `backend/app/services/review_service.py`
- `backend/app/worker/tasks.py`
- `backend/app/api/v1/endpoints/review.py`
- 如有必要，前端状态显示最小范围

## 必做事项
1. 设计并落地 `review_card_generation` 派生任务
2. 主笔记成功后可触发卡片生成链（最小可行版本）
3. 主笔记成功与卡片任务失败状态分离
4. 补最小测试或链路验证

## 不要做
- 不扩张到 AI 判分讲解
- 不扩张到复习时长统计

## 验收标准
- 卡片生成不再只依赖手工 bootstrap
- 具备独立异步任务链

# SA-45E 复习时长统计模型修正任务单

## 目标
修复复习页面时长统计长期为 0 的问题，引入 review session 化的最小可行方案。

## 必读文档
- docs/90-post-test-issue-master-table.md
- docs/91-next-fix-wave-orchestration.md
- docs/93-p1-fixes-main.md

## 重点范围
- `frontend/src/pages/review/review-session-page.tsx`
- `backend/app/services/review_service.py`
- `backend/app/api/v1/endpoints/review.py`
- `backend/app/models/review_log.py`
- `backend/app/models/admin_entities.py`
- 与 review_watch_seconds 聚合相关最小范围

## 必做事项
1. 复习会话引入 start/heartbeat/finalize 或等价机制
2. 让 review_watch_seconds 能稳定增长并落库
3. 明确前端显示时间与后台累计时间口径
4. 补最小测试或链路验证

## 不要做
- 不扩张到 AI 判分讲解

## 验收标准
- 复习时长不再长期为 0
- review session 统计口径清晰可解释

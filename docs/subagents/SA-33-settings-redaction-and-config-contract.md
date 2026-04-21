# SA-33 settings脱敏与配置契约修整任务单

## 目标
先完成实现阶段的最上游安全与契约准备：修掉 `/api/v1/settings/ai` 对完整 API key 的回显，并保证 llm / embedding / ocr / stt 四类 provider 的读写契约在脱敏后仍可兼容现有前端与后续实现。

## 必读文档
- docs/73-note-generation-detailed-solution.md
- docs/74-embedding-retrieval-detailed-design.md
- docs/77-phased-implementation-and-task-breakdown.md
- docs/78-test-acceptance-and-risk-control-plan.md
- docs/79-pre-implementation-control-freeze.md

## 重点范围
- `backend/app/api/v1/endpoints/settings.py`
- `backend/app/services/settings_admin_service.py`
- `backend/app/schemas/settings_admin.py`
- `frontend/src/types/settings.ts`
- `frontend/src/pages/settings/settings-ai-page.tsx`
- 与 settings API 契约兼容直接相关的最小范围

## 必做事项
1. `/settings/ai` 的 GET / PUT 响应不再回显完整 API key。
2. 保证前端页面在脱敏后仍能正确展示、编辑并保存 provider 配置。
3. 保持 llm / embedding / ocr / stt 四类 provider 契约可继续使用。
4. 补充必要测试，至少覆盖：
   - API 响应脱敏
   - 更新 provider 时旧 key 保留/新 key 覆盖逻辑

## 不要做
- 不实现 embedding retrieval
- 不改 note generation 主链
- 不扩展无关设置页功能

## 验收标准
- GET/PUT `/api/v1/settings/ai` 不再返回完整密钥
- 现有 provider 配置功能不坏
- 测试通过并回传证据

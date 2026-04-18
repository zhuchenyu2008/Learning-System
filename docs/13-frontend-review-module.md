# 13-前端复习模块实现细节文档

## 1. 页面范围
- 复习 / 总览
- 复习 / 复习会话
- 复习 / 知识点总结
- 复习 / 思维导图生成

## 2. 页面细节
### 2.1 复习总览
- 今日到期卡片数
- 总卡片数
- 最近复习统计
- CTA：开始复习、生成总结、生成思维导图

### 2.2 复习会话
- 拉取 review queue
- 展示卡片标题、摘要、来源笔记
- Again / Hard / Good / Easy 评分按钮
- 写入 duration_seconds 与可选日志备注
- 空队列态展示

### 2.3 知识点总结页
- 列表展示已有 summary 产物
- 手动生成表单：scope、note_ids、prompt_extra
- 普通用户只读

### 2.4 思维导图页
- 列表展示已有 mindmap 产物
- 手动生成表单：scope、note_ids、prompt_extra
- Mermaid 渲染预览
- 普通用户只读

## 3. API 对接
- `GET /api/v1/review/overview`
- `GET /api/v1/review/queue`
- `POST /api/v1/review/cards/bootstrap`
- `POST /api/v1/review/session/{card_id}/grade`
- `GET /api/v1/review/logs`
- `POST /api/v1/review/logs`
- `POST /api/v1/summaries/generate`
- `GET /api/v1/summaries`
- `POST /api/v1/mindmaps/generate`
- `GET /api/v1/mindmaps`

## 4. 验收标准
- 复习页面链路可交互
- 总结 / 思维导图可发起生成并查看结果
- 普通用户权限符合要求

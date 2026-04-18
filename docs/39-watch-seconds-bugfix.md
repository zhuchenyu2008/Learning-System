# 39-watch_seconds 统计口径缺陷修复文档

## 1. 缺陷结论
当前 `watch_seconds` 上报复用了 `GET /notes/{id}` 详情接口，导致“查看详情”和“上报观看时长”两个语义混在一起。

结果是：
- 观看时长累计时，同时会重复累计 `page_view_count` / `note_view_count`
- 管理员侧活动统计数据被污染

这应被视为**真实 bug**，而不是单纯的低风险观察项。

## 2. 缺陷定级
- 类型：统计口径错误 / 行为埋点 bug
- 优先级：P1
- 影响范围：
  - notes 详情阅读链路
  - admin 用户活动面板
  - 页面访问次数 / 笔记查看次数统计

## 3. 修复方案（定稿）
采用**方案 A：拆分接口语义**。

### 3.1 后端接口拆分
- `GET /api/v1/notes/{id}`
  - 只负责获取笔记详情
  - 如需保留查看事件，最多只记录一次明确的 `note_view`
  - 不再接收 `watch_seconds` 参数

- `POST /api/v1/notes/{id}/watch`
  - 只负责上报观看时长
  - 请求体包含最小必要字段：`watch_seconds`
  - 不再累加 `page_view_count` / `note_view_count`
  - 只更新观看时长相关统计与活动快照

### 3.2 前端改动
- Notes 页面停止通过 `getNoteDetail(..., watchSeconds)` 上报时长
- 新增独立 `reportWatchSeconds(noteId, watchSeconds)` 调用新接口
- 保持现有 pagehide / hidden / unmount / switch note 的上报时机

### 3.3 测试要求
- 后端：
  - notes detail 正常读取
  - `POST /notes/{id}/watch` 正常上报
  - watch 不重复累计 view 次数
- 前端：
  - notes 页面仍能正常上报 watch_seconds
  - API 层调用已切到新接口

## 4. 边界
- 不扩展新的埋点体系
- 不同时处理 Mermaid 包体等无关问题
- 不借机重构整套 activity 统计系统

## 5. 验收标准
- view 与 watch 语义彻底拆开
- 管理侧访问次数不再因 watch flush 重复累计
- 自动化测试补上并通过

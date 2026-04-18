# 34-测试矩阵文档

## 1. 使用说明
本矩阵用于将“测试计划”落到可执行的模块/场景/检查点层级。

阅读方式：
- SA-15B 重点看后端矩阵
- SA-15C 重点看前端与部署矩阵
- SA-15D 按优先级与执行顺序汇总执行

状态约定建议：
- P0：关键主链，必须覆盖
- P1：重要能力，应覆盖
- P2：增强能力，可抽样或次级覆盖

---

## 2. 后端测试矩阵

| 模块 | 场景 | 核心检查点 | 优先级 | 建议类型 |
|---|---|---|---|---|
| Health | 服务健康检查 | 健康接口返回成功；依赖初始化不报错 | P0 | API 集成 |
| Auth | 登录成功 | 合法账号可登录；返回 token/用户信息结构正确 | P0 | API 集成 |
| Auth | 登录失败 | 密码错误、用户禁用、参数缺失时返回预期错误 | P0 | API 集成 |
| Auth | refresh | refresh 可换取新 token；非法 token 被拒绝 | P1 | API 集成 |
| Auth | logout | 登出接口可调用；结果契约稳定 | P2 | API 集成 |
| Auth | me | 已登录可获取当前用户；未登录被拒绝 | P0 | API 集成 |
| Auth | viewer/admin 权限 | viewer 与 admin 能力边界符合文档契约 | P0 | API 集成 |
| Sources | scan | 扫描请求成功；响应结构正确；任务/结果可观测 | P1 | API 集成 |
| Sources | upload-manifest | 上传清单成功；非法输入被拒绝 | P2 | API 集成 |
| Sources | list | 可列出资源；字段结构符合契约 | P1 | API 集成 |
| Sources | 异常路径 | 不存在路径/非法参数/权限不足时返回正确错误 | P1 | API 集成 |
| Notes | generate | 可触发生成；返回 job 或结果信息；鉴权正确 | P0 | API 集成 |
| Notes | list | 列表可返回；支持基础过滤/分页（如已有） | P0 | API 集成 |
| Notes | tree | 树结构可返回；层级数据不为空或格式正确 | P1 | API 集成 |
| Notes | detail | 详情可读取；字段完整；不存在资源返回 404/等价错误 | P0 | API 集成 |
| Notes | reindex | 可触发重建索引；非法 note id 返回预期错误 | P1 | API 集成 |
| Notes | watch_seconds | 上报成功；确认不会导致接口失败；统计偏差作为已知低风险单独记录 | P1 | API 集成 |
| Review | overview | 概览数据可返回；关键统计字段存在 | P0 | API 集成 |
| Review | queue | 队列可返回；空队列与非空队列行为正确 | P0 | API 集成 |
| Review | bootstrap | 可初始化卡片；重复初始化/空数据路径可判定 | P1 | API 集成 |
| Review | grade | 可提交评分；评分非法值被拒绝；状态更新合理 | P0 | API 集成 + Service |
| Review | logs(list) | 可查询复习日志；结构正确 | P1 | API 集成 |
| Review | logs(create) | 可写入日志；未登录/参数异常路径正确 | P1 | API 集成 |
| ReviewService | FSRS 状态流转 | 评分后 due/state 字段合理变化 | P0 | Service |
| Summaries | generate | 可生成摘要任务/结果；鉴权正确 | P1 | API 集成 |
| Summaries | list | 可查询摘要产物；artifact 字段正确 | P1 | API 集成 |
| Mindmaps | generate | 可生成思维导图任务/结果 | P1 | API 集成 |
| Mindmaps | list | 可查询思维导图产物；输出 note/artifact 正确 | P1 | API 集成 |
| Settings | system get/put | admin 可读写；viewer 被拒绝；字段校验正确 | P0 | API 集成 |
| Settings | ai get/put | AI 配置可读写；敏感字段处理合理 | P1 | API 集成 |
| Settings | obsidian get/put | Obsidian 配置可读写；路径/参数异常可判定 | P1 | API 集成 |
| Settings | test-provider | 测试接口可调用；失败路径可观测 | P2 | API 集成 |
| Admin | users | admin 可读用户列表；viewer 被拒绝 | P0 | API 集成 |
| Admin | user-activity | 管理侧活动数据可返回；字段结构正确 | P1 | API 集成 |
| Admin | login-events | 登录事件可返回；权限正确 | P1 | API 集成 |
| Admin | database export | 可触发导出；权限正确；结果可观测 | P1 | API 集成 |
| Admin | database import | 可触发导入；非法输入/权限不足路径正确 | P1 | API 集成 |
| Admin | obsidian sync | 可触发同步；返回任务/结果契约清晰 | P2 | API 集成 |
| Jobs | list | queued/running/completed/failed 可区分；字段完整 | P0 | API 集成 |
| Jobs | detail | `logs_json`、`celery_task_id`、状态字段可读取 | P1 | API 集成 |
| JobService | 状态流转 | job 状态迁移、错误信息、结果写回正确 | P1 | Service |

---

## 3. 前端测试矩阵

| 页面/模块 | 场景 | 核心检查点 | 优先级 | 建议类型 |
|---|---|---|---|---|
| 登录页 | 页面渲染 | 输入框、提交按钮、错误提示区域可见 | P0 | 页面测试 |
| 登录页 | 登录成功 | 成功后跳转正确；用户状态被写入 | P0 | 页面测试 |
| 登录页 | 登录失败 | 错误提示展示；重复提交状态可控 | P0 | 页面测试 |
| Notes Overview | 页面加载 | 统计/入口卡片正常渲染；空态可见 | P1 | 页面测试 |
| Notes Generate | 生成表单 | 必填项校验；提交后请求触发；loading/成功/失败状态正确 | P0 | 页面测试 |
| Notes Library | 列表展示 | 列表、筛选、空态、错误态正常 | P0 | 页面测试 |
| Notes Detail | 内容展示 | 标题、正文、元信息正常显示 | P0 | 页面测试 |
| Notes Detail | Markdown 渲染 | GFM 渲染正常；代码块/列表/表格显示正确 | P0 | 组件/页面测试 |
| Notes Detail | HTML 白名单渲染 | 安全白名单 HTML 可显示；危险标签被过滤 | P0 | 组件测试 |
| Notes Detail | Mermaid 渲染 | `mermaid` 代码块被识别并渲染；异常内容有降级表现 | P0 | 组件/页面测试 |
| Notes Detail | watch_seconds 上报 | 页面停留/触发时有上报请求；不要求在前端层修复统计口径问题 | P1 | 页面测试 |
| Review Overview | 页面加载 | 概览统计、入口按钮、空态/错误态正确 | P0 | 页面测试 |
| Review Session | 取题与作答 | 队列加载、评分按钮、提交后状态切换正确 | P0 | 页面测试 |
| Review Session | 异常路径 | 空队列、请求失败、非法响应时可展示提示 | P1 | 页面测试 |
| Review Summaries | 列表展示 | 摘要列表、生成入口、空态正常 | P1 | 页面测试 |
| Review Mindmaps | 列表展示 | 思维导图列表、生成入口、空态正常 | P1 | 页面测试 |
| Settings AI | 配置读写 | 表单回填、保存、错误提示正常 | P1 | 页面测试 |
| Settings Workspace | 系统配置 | workspace/system 配置可读写；字段校验正确 | P1 | 页面测试 |
| Settings Users | 用户管理 | 用户列表可见；仅 admin 可操作 | P0 | 页面测试 |
| Settings Import/Export | 导入导出 | 按钮启用态、调用行为、结果提示正常 | P1 | 页面测试 |
| Settings Jobs | Jobs 展示 | 列表、状态标签、详情信息、日志区域正常 | P0 | 页面测试 |
| 权限禁用态 | viewer 受限行为 | viewer 在管理/写操作页面按钮禁用或入口隐藏 | P0 | 页面测试 |
| 权限禁用态 | admin 完整行为 | admin 能看见并操作完整入口 | P0 | 页面测试 |
| 全局导航 | 路由与菜单 | 各主要路由可达；菜单高亮/跳转正确 | P1 | 页面测试 |
| 全局错误处理 | 请求失败 | toast/错误提示/重试入口表现合理 | P1 | 页面测试 |

---

## 4. 部署与集成测试矩阵

| 模块 | 场景 | 核心检查点 | 优先级 | 建议类型 |
|---|---|---|---|---|
| Compose | config | `docker compose config` 可通过 | P0 | 部署验证 |
| Compose | build | 镜像可构建完成；关键服务无构建错误 | P0 | 部署验证 |
| Compose | up -d | 服务可启动；容器状态可观测 | P0 | 部署验证 |
| Backend | health | backend 健康接口返回正常 | P0 | 部署验证 |
| Frontend | 页面可达 | 前端页面可访问；静态资源加载正常 | P0 | 部署验证 |
| Proxy | frontend -> backend | 代理访问后端接口成功，无系统性 502 | P0 | 部署验证 |
| Postgres | 服务就绪 | 容器就绪、后端可连库 | P0 | 部署验证 |
| Redis | 服务就绪 | Redis 可用、worker/beat 可连接 | P0 | 部署验证 |
| Worker | 进程就绪 | worker 进程启动成功；日志无明显启动失败 | P1 | 部署验证 |
| Beat | 进程就绪 | beat 进程启动成功；日志无明显启动失败 | P1 | 部署验证 |
| Env | `.env` 基线 | `.env.example` 可用；关键变量有说明 | P1 | 部署验证 |
| Runtime | backend recreate 后 frontend 代理 | 如有短暂 upstream 陈旧，需记录为已知低风险，而非误报系统阻塞 | P2 | 部署验证 |

---

## 5. 回归矩阵

| 回归主题 | 检查点 | 优先级 | 备注 |
|---|---|---|---|
| 路线 A 工程化收口 | backend / worker / beat / frontend / postgres / redis 可起 | P0 | 必测 |
| 路线 A 工程化收口 | health / 代理链路可达 | P0 | 必测 |
| 路线 A 工程化收口 | 前端构建与基础 lint 基线不回退 | P1 | 可结合已有命令 |
| 路线 B 增强项 | Jobs 可见性字段完整 | P0 | 必测 |
| 路线 B 增强项 | Markdown / HTML / Mermaid 渲染不回退 | P0 | 必测 |
| 路线 B 增强项 | 管理员 / 普通用户禁用态不回退 | P0 | 必测 |
| 路线 B 增强项 | PDF / 多模态相关入口不出现主链级错误 | P2 | 抽样 |
| 路线 B 增强项 | KnowledgePoint / activity 数据链路基础可见 | P1 | 抽样 |

---

## 6. 已知风险标注规则
以下问题在执行时若再次出现，应优先标注为“已知低风险项复现”，不要直接归类为新阻塞：
- `watch_seconds` 上报会附带重复累计 `page_view_count / note_view_count`
- Mermaid chunk 体积偏大
- backend recreate 后 frontend 可能短暂 502，重启 frontend 可恢复

但若出现以下情况，则应升级为缺陷：
- `watch_seconds` 导致接口错误或页面卡死
- Mermaid 无法正常渲染主链内容
- 代理 502 持续且无法自恢复/无法通过既定方式恢复

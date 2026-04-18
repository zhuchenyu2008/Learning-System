# 35-测试实施说明文档

## 1. 文档目的
本说明文档用于把测试计划与测试矩阵进一步落到“谁先做什么、脚本怎么组织、执行时按什么顺序跑、结果如何判定”的操作层。

目标：
- 让 SA-15B 直接开始后端测试实现
- 让 SA-15C 直接开始前端/集成测试实现
- 让 SA-15D 拿到统一执行入口与结果归档方式

## 2. 子任务执行顺序

### 阶段 A：文档完成（已由 SA-15A 负责）
完成以下文档：
- `docs/33-full-test-plan.md`
- `docs/34-test-matrix.md`
- `docs/35-test-execution-guide.md`

### 阶段 B：后端测试实现（SA-15B）
优先事项：
1. 确认 `pytest` 入口可运行
2. 梳理 `backend/tests` 现状
3. 按模块补充 API 测试
4. 按高价值服务补充 service 测试
5. 输出后端测试命令与说明

### 阶段 C：前端/集成测试实现（SA-15C）
优先事项：
1. 选定并接入前端测试框架
2. 补测试命令到 `frontend/package.json`
3. 先覆盖关键页面渲染与权限禁用态
4. 再覆盖 Markdown / HTML / Mermaid 渲染
5. 补少量高价值集成验证脚本

### 阶段 D：完整测试执行（SA-15D）
严格按以下顺序执行：
1. 环境/依赖检查
2. 后端自动化测试
3. 前端自动化测试
4. Docker/部署验证
5. 回归抽样验证
6. 测试结果归档

## 3. 建议目录与脚本组织

### 3.1 后端测试建议组织
建议 SA-15B 在不破坏现有结构前提下优先采用：
- `backend/tests/api/`
- `backend/tests/services/`
- `backend/tests/conftest.py`
- `backend/tests/fixtures/`（如确有必要）

组织原则：
- 一个模块一组测试
- 公共鉴权、用户构造、数据库准备逻辑集中复用
- 测试名直接体现模块/场景/预期

### 3.2 前端测试建议组织
建议 SA-15C 在 `frontend/` 下建立：
- `src/test/` 或 `tests/`
- 页面级测试
- 渲染类组件测试
- API mock / 测试工具封装

组织原则：
- 先高价值页面，后细组件
- 优先断言用户可见行为，不依赖实现细节
- Mermaid / HTML 渲染测试需关注“渲染结果或降级结果”，避免脆弱快照泛滥

### 3.3 部署验证脚本建议
如需脚本化，可考虑沉淀到：
- `scripts/test/` 或等价目录

最低应明确：
- compose 配置校验命令
- compose 构建命令
- compose 启动命令
- health 检查命令
- 代理验证命令
- 查看 worker / beat 日志命令

## 4. 推荐执行命令方向
以下为方向性约束，具体命令由 SA-15B / SA-15C 结合仓库实现补齐。

### 4.1 后端
建议至少具备以下能力：
- 运行全部后端测试
- 按模块运行后端测试
- 在失败时输出足够日志

推荐方向示例：
- `pytest`
- `pytest backend/tests/api -q`
- `pytest backend/tests/services -q`

### 4.2 前端
由于当前 `frontend/package.json` 尚无测试脚本，SA-15C 需要先补齐：
- 单次测试命令
- CI/无交互测试命令
- 必要时的 e2e/集成测试命令

推荐方向示例：
- `npm run test`
- `npm run test:run`
- `npm run test:e2e`

### 4.3 部署验证
推荐方向示例：
- `docker compose config`
- `docker compose build`
- `docker compose up -d`
- `docker compose ps`
- `docker compose logs backend --tail=200`
- `docker compose logs worker --tail=200`
- `docker compose logs beat --tail=200`

## 5. 执行顺序细化

### 5.1 SA-15D 执行顺序（必须遵守）

#### Step 1：环境准备
- 校验 Python / Node / Docker 基础可用
- 校验依赖已安装或可安装
- 校验 `.env` 存在并满足最小配置

#### Step 2：后端测试
- 先跑 smoke/核心模块
- 再跑完整 pytest
- 汇总失败模块与错误类型

#### Step 3：前端测试
- 先跑页面渲染/权限相关核心集
- 再跑完整前端测试
- 汇总失败页面与失败断言

#### Step 4：部署验证
- 跑 compose config/build/up
- 验证 backend health
- 验证 frontend 页面可达
- 验证 frontend -> backend 代理
- 验证 worker / beat / postgres / redis 状态

#### Step 5：回归抽样
重点回归：
- 登录
- notes 生成/列表/详情
- review queue/session/grade
- settings admin 页面与权限
- jobs 列表/详情
- Mermaid / HTML / Markdown 渲染

#### Step 6：报告归档
按统一模板输出：
1. 改动文件列表
2. 执行命令列表
3. 通过项
4. 未通过项
5. 阻塞项

## 6. 通过标准细化

### 6.1 后端通过标准
至少满足：
- pytest 可执行
- P0 模块均有可运行测试
- auth / notes / review / settings-admin / jobs 覆盖关键主链
- viewer/admin 权限边界有验证

### 6.2 前端通过标准
至少满足：
- 前端测试命令可执行
- 登录、notes、review、settings、jobs 关键页面有测试
- 权限禁用态有覆盖
- Markdown / HTML / Mermaid 渲染有覆盖

### 6.3 部署通过标准
至少满足：
- compose config/build/up 成功
- backend health 正常
- frontend 可访问
- frontend -> backend 代理可达
- worker / beat 无启动级阻塞错误

### 6.4 阶段报告通过标准
至少满足：
- 能区分通过项、未通过项、阻塞项
- 能区分新问题与已知低风险遗留项
- 每个失败/阻塞都有证据

## 7. 失败分类规则

### 7.1 通过项
- 用例/脚本执行成功
- 结果与契约一致
- 无需人工解释即可判定通过

### 7.2 未通过项
- 存在断言失败或行为不符合预期
- 但不阻断后续整体执行
- 有明确模块归属与复现方式

### 7.3 阻塞项
- 环境无法启动
- 测试入口无法运行
- 核心鉴权/主链不可用
- Docker 关键服务无法启动
- 前后端代理链路不可达

## 8. 已知低风险项处理规则
遇到以下情况时，应记录为“已知低风险项复现”：
- `watch_seconds` 导致访问次数统计重复累计
- Mermaid chunk 体积偏大但不影响功能
- backend recreate 后 frontend 短暂 502，但可按既定方式恢复

若其影响升级，则改判为未通过或阻塞：
- 导致主链无法操作
- 持续性失败无法恢复
- 结果与用户关键功能直接冲突

## 9. 对 SA-15B / SA-15C 的直接约束

### 9.1 SA-15B 必须做到
- 不只写 smoke test
- 至少覆盖 P0 后端矩阵
- 输出清晰测试命令
- 尽量复用 fixture，避免重复拼装数据

### 9.2 SA-15C 必须做到
- 先补前端测试入口，再补用例
- 至少覆盖 P0 前端矩阵
- 对渲染类能力给出稳定断言方案
- 不用无边界 e2e 替代页面级测试

## 10. 对 SA-15D 的直接约束
- 不得跳过后端或前端测试直接只跑部署
- 不得只给口头结论，必须给命令与结果依据
- 不得把“未执行”写成“通过”
- 不得把“已知低风险项”遗漏不报

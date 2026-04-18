# 32-完整测试阶段总控文档

## 1. 目标
正式进入完整测试阶段，对 `learning-system` 做覆盖全面的功能测试、接口测试、前端交互测试、部署测试与回归测试。

## 2. 测试阶段原则
- 先文档、后测试实现
- 优先补齐测试计划与测试矩阵
- 再分别落自动化测试脚本与必要的验证工具
- 最后做阶段性测试执行与问题收敛

## 3. 测试范围
### 3.1 后端
- auth / health
- sources / notes / jobs
- review / FSRS / summaries / mindmaps
- settings / admin
- Celery / worker / beat
- Docker 下 health / proxy / service 联通性

### 3.2 前端
- 登录
- notes 三页
- review 四页
- settings 五页
- 权限禁用态
- Markdown / HTML / Mermaid 渲染
- Jobs / activity 展示

### 3.3 部署与集成
- docker compose build/up
- frontend -> backend 代理
- postgres / redis / worker / beat
- `.env` 配置基线

## 4. 测试输出物
- 主测试计划文档
- 测试矩阵文档
- 测试脚本/自动化用例
- 阶段执行报告
- 问题清单

## 5. 子任务拆分
| SA | 目标 | 类型 |
|---|---|---|
| SA-15A | 测试计划与测试矩阵文档 | 文档 |
| SA-15B | 后端测试增强与测试脚本 | 实现 |
| SA-15C | 前端/集成测试脚本与验证工具 | 实现 |
| SA-15D | 完整测试执行与测试报告 | 验证 |

## 6. 串并行规则
- SA-15A 必须先完成
- SA-15B / SA-15C 可并行
- SA-15D 最后执行

# 08-基础盘修整计划文档

## 1. 当前修整目标
在进入 SA-02 / SA-03 / SA-05~07 前，先修复并验收第一批基础骨架的可运行性问题。

## 2. 已发现问题
### 2.1 后端
- `pyproject.toml` 声明 `requires-python >=3.11`，但当前机器为 Python 3.10.12。
- 当前 `.venv` 不可直接用于安装/测试，缺少 pip 与核心依赖。
- 因此 backend import / pytest 尚未完成验收。

### 2.2 前端
- `npm install` 已成功。
- `npm run build` 失败。
- 已知错误集中在 `vite.config.ts`：
  - `Cannot find module 'node:path'`
  - `Cannot find name '__dirname'`
- 说明需要补 Node 类型和 ESM 兼容写法修整。

## 3. 修整策略
### 3.1 SA-01A 后端环境修整
- 只修后端环境/依赖/配置兼容问题。
- 目标是让：
  - 依赖可安装
  - `from app.main import app` 可导入
  - backend tests 至少可执行
- 如需调整 Python 版本要求，必须与现有机器条件保持一致，并尽量不破坏后续 PostgreSQL/FastAPI 架构。

### 3.2 SA-04A 前端构建修整
- 只修前端构建与配置问题。
- 目标是让：
  - `npm run build` 通过
  - 保持现有路由与主题结构不被破坏

## 4. 验收标准
- 后端：安装命令明确、依赖可装、最小 import 成功、测试命令可执行。
- 前端：build 通过。

## 5. 后续解锁条件
只有 SA-01A 与 SA-04A 验收通过后，才继续派发：
- SA-02 资料导入与笔记生成
- SA-03 复习 / 总结 / 思维导图
- SA-05~07 前端业务页

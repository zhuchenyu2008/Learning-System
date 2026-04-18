# SA-01B venv 重试验证任务单

## 目标
在已安装 `python3.10-venv` 后，重新验证项目标准虚拟环境创建流程是否可用，并补做最小安装/导入/测试验收。

## 必读文档
- docs/00-main-task.md
- docs/08-foundation-remediation-plan.md
- docs/subagents/SA-01A-backend-remediation.md

## 范围
- 删除旧 `.venv`（如需要）
- 重新执行标准 `python3 -m venv .venv`
- 在新 `.venv` 中安装项目依赖
- 验证 `from app.main import app`
- 运行 backend tests

## 不要做
- 不扩展业务功能
- 不改前端
- 不进入 SA-02/SA-03 功能开发

## 验收标准
- `.venv` 可正常创建
- `.venv/bin/pip` 可用
- 后端依赖可安装
- 导入成功
- backend tests 可执行并尽量通过

## 回传要求
- 执行命令
- 结果
- 若失败说明阻塞项

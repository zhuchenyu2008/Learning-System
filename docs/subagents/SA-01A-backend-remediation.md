# SA-01A 后端环境修整任务单

## 目标
修整后端基础环境与配置兼容问题，使后端能完成最小安装、导入与测试验收。

## 必读文档
- docs/00-main-task.md
- docs/06-implementation-plan.md
- docs/07-subagent-orchestration-plan.md
- docs/08-foundation-remediation-plan.md
- docs/subagents/SA-01-backend-foundation.md

## 当前已知问题
- 当前机器 Python 为 3.10.12
- `pyproject.toml` 声明 `requires-python >=3.11`
- `.venv` 缺 pip / 依赖未装
- backend import / pytest 尚未通过

## 范围
- 只修后端环境与基础配置问题
- 可修改：`pyproject.toml`、README、安装/测试说明、必要的轻微兼容代码
- 可重建本项目 `.venv` 或使用明确可复现方式安装依赖
- 跑通最小导入与测试

## 不要做
- 不扩展业务功能
- 不进入 SA-02/03 范围
- 不改前端

## 验收标准
- 依赖安装方式明确可执行
- `from app.main import app` 成功
- backend tests 至少可执行并尽量通过

## 回传要求
- 改动文件列表
- 执行命令列表
- 通过项
- 未通过项
- 阻塞项

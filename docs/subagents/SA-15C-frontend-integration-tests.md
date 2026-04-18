# SA-15C 前端/集成测试脚本任务单

## 目标
补前端测试基础设施与关键页面/组件测试，并提供必要的集成验证工具。

## 必读文档
- docs/33-full-test-plan.md
- docs/34-test-matrix.md
- docs/35-test-execution-guide.md

## 范围
- 选定并接入前端测试框架
- 补 `frontend/package.json` 测试命令
- 覆盖关键页面渲染与权限禁用态
- 覆盖 Markdown / HTML / Mermaid 高价值场景
- 视情况补少量集成验证脚本

## 不要做
- 不扩展新业务功能
- 不用无边界 e2e 替代页面级测试

## 验收标准
- 前端测试命令可执行
- 至少覆盖 P0 前端矩阵核心项

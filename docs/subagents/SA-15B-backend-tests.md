# SA-15B 后端测试增强与测试脚本任务单

## 目标
补强后端测试覆盖，围绕现有后端主链建立更完整的 API / service 自动化测试。

## 必读文档
- docs/33-full-test-plan.md
- docs/34-test-matrix.md
- docs/35-test-execution-guide.md

## 范围
- 梳理并增强 `backend/tests`
- 优先覆盖 P0/P1 后端测试矩阵
- 补必要 fixture / 测试脚本组织
- 输出清晰的后端测试执行命令

## 不要做
- 不改前端
- 不扩展新业务功能
- 不跳过现有测试基线直接重写一整套

## 验收标准
- 后端测试覆盖明显增强
- pytest 命令可执行
- 有明确 through/未通过/阻塞项

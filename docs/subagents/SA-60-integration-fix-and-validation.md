# SA-60 集成修复与总体验证任务单

## 目标
完成 SA-56/57/58/59 合并后的集成修复，解决真实碰到的报错，并完成关键验证。

## 必读文档
- docs/101-post-manual-test-wave2-main.md
- docs/107-post-manual-test-wave2-implementation-plan.md
- docs/109-post-manual-test-wave2-test-plan.md
- docs/110-wave2-finalization-main.md
- docs/111-wave2-finalization-plan.md

## 重点范围
- 前后端集成冲突
- 类型错误/测试错误/构建错误
- 必要时 Docker 最终验证

## 验收标准
- 关键报错已修
- 前端 build 通过
- 后端关键测试通过
- 如执行 Docker，则健康检查通过

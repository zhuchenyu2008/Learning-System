# SA-37 质量门禁与真实回归任务单

## 目标
在主链、retrieval、结构化输出、命名与路径写回都落地后，专门收口低质量输入的业务判定，并用真实 SiliconFlow 配置重新跑全来源回归。

## 必读文档
- docs/73-note-generation-detailed-solution.md
- docs/74-embedding-retrieval-detailed-design.md
- docs/75-prompt-time-and-output-structure-design.md
- docs/76-subject-classification-naming-and-path-design.md
- docs/77-phased-implementation-and-task-breakdown.md
- docs/78-test-acceptance-and-risk-control-plan.md
- docs/79-pre-implementation-control-freeze.md

## 前置依赖
- SA-33 ~ SA-36 已完成

## 重点范围
- image/pdf/audio 的质量门禁逻辑
- 全来源真实回归测试链
- 产物抽样检查与最终报告

## 必做事项
1. 区分技术成功与业务成功。
2. 对 image/pdf/audio 的低质量输入进行纠偏：
   - fail fast
   - warning
   - 或明确质量标记
3. 重新使用真实 SiliconFlow 配置跑：
   - txt
   - md
   - docx
   - pdf
   - image
   - audio
4. 抽样检查最终 note：
   - retrieve 是否执行
   - 标题是否符合要求
   - 目录是否符合要求
   - 质量是否达标
5. 输出最终回归报告与风险清单。

## 不要做
- 不再大改上游主链架构
- 不把“completed”直接等同于“验收通过”

## 验收标准
- 全来源真实回归有证据
- retrieval、标题、目录、质量四项都被核验
- 最终能明确 through/failed/blocked

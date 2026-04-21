# SA-39 retrieval真实命中专项验真任务单

## 目标
专门验证当前最新代码下，embedding retrieval 是否已经在已有历史候选笔记库上形成非空真实命中，而不是只执行空 retrieve 阶段。

## 必读文档
- docs/73-note-generation-detailed-solution.md
- docs/78-test-acceptance-and-risk-control-plan.md
- docs/79-pre-implementation-control-freeze.md
- docs/80-retrieval-real-hit-validation-plan.md

## 范围
- 不做主链大改
- 不重做全部 6 类样本总回归
- 只做 retrieval 真命中专项验证

## 必做事项
1. 启动/保持当前最新代码实例可用
2. 构造并保留一批历史候选笔记
3. 使用高相关新样本触发生成
4. 核验：
   - retrieve 阶段真实执行
   - `matched_count > 0`
   - `matched_paths` 非空
   - `retrieval_context_chars > 0`
   - 最终产物含 retrieval_summary
5. 给出 through / failed / blocked 结论

## 不要做
- 不清空已构造好的候选库
- 不再追求 image/pdf/audio 总质量收口
- 不扩张到无关代码修改，除非为了使当前实例使用最新代码所必需

## 验收标准
- 形成非空 retrieval 命中证据
- 证据来自当前最新代码运行实例，而不是旧 results 文件

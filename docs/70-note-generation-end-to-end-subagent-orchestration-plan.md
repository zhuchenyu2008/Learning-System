# 70-笔记生成全流程subagent编排计划

## 总体原则
本轮先调查与建模，再进入实现。先派调查型 subagent，不直接大改代码。

## SA-30：Skill口径与流程差距调查
- 输入：用户给定两份 skill、当前代码
- 输出：embedding 检索、prompt 口径、目录/命名规则差距清单

## SA-31：真实环境全来源测试与证据收集
- 输入：用户给定 SiliconFlow 配置、当前 Docker 环境
- 输出：txt/md/docx/pdf/image/audio 的真实测试证据、产物样例、问题清单

## SA-32：配置与代码结构审计
- 输入：provider 配置代码、note generation 主链代码
- 输出：是否支持 embedding provider、是否支持 retrieve 阶段、需要改哪些模块

## 串并行关系
- SA-30 / SA-31 / SA-32 可并行
- 三者结果汇总后，主 agent 再定稿差距与解决方案
- 在主 agent 未定稿解决方案前，不进入实现型 subagent

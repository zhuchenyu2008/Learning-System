# 69-笔记生成全流程实现总方案

## 阶段 1：调查与真实测试
- 接入用户给定 SiliconFlow 配置到当前环境
- 核实四类 provider 配置与测试接口
- 对 txt/md/docx/pdf/image/audio 做真实端到端测试
- 抽样检查生成笔记质量、命名、学科目录、日志

## 阶段 2：差距确认
- 明确 embedding 是否缺失
- 明确标题/分类/时间注入/skill prompt 差距
- 明确哪些问题是配置问题，哪些是代码结构问题

## 阶段 3：设计修整
- 确认 provider 数据模型是否要扩展 embedding
- 确认检索模块如何插入现有主链
- 确认生成输出结构是否要支持 subject/title/path 建议

## 阶段 4：小块实现
- 配置层与 provider 类型修整
- embedding 检索链接入
- prompt / 时间上下文 / 标题与学科分类接入
- 写回路径与命名策略接入
- 端到端测试修整

## 阶段 5：最终验收
- 再跑真实多来源测试
- 对产出笔记做人工抽样检查
- 总结 remaining risks

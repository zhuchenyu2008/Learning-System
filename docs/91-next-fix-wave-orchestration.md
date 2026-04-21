# 91-下一轮修复编排计划（P0/P1/P2）

## P0（立即推进）
### P0-1 笔记内容污染清理
目标：
- 最终用户笔记正文只保留成品内容
- retrieval_summary、normalized excerpt、extracted preview、调试性 warnings 不再直接进入正文
- 保留必要元数据，但隐藏到 job result / debug artifact / 精简 frontmatter

### P0-2 思维导图双重 mermaid fence 与渲染失败修复
目标：
- 后端保存前先 sanitize mermaid 内容
- 去除双重 fenced block
- 前端渲染失败只降级当前图块，不拖垮主页面

## P1（P0 完成后）
### P1-1 生成页状态文案与 job 状态联动
### P1-2 docx 失败日志定位与链路补强
### P1-3 artifact 与笔记分组/展示分离
### P1-4 笔记后异步生成复习卡片
### P1-5 复习时长统计模型修正

## P2（P1 完成后）
### P2-1 复习 AI 判分与讲解

## 本轮执行规则
- 先写 P0 文档与任务单，再派实现型 subagent
- P0 修完后必须先做回归验证，再进入 P1
- 如果 subagent 遇到权限受限，主 agent 接手补做对应操作，但不跳过文档与验收

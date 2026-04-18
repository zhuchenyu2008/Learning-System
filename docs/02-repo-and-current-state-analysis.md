# 02-仓库与现状分析文档

## 1. 当前现状
当前项目仓库不存在，本轮将在 `/root/projects/learning-system` 新建完整工程。

## 2. 参考来源分析
### 2.1 obsidian-study-notes 参考要点
- 以 Obsidian Markdown 作为长期沉淀的主载体。
- 支持录音/转写/讲义/图片/错题材料入库。
- 强调模板化、YAML、统一目录命名。
- 支持关联旧笔记、语义召回、同步脚本。

### 2.2 obsidian-spaced-recall 参考要点
- 将笔记内容拆为适合复习的颗粒。
- 维护到期队列、待提交状态、复习状态回写。
- 支持定时生成“今日复习”。
- 适合配合 Obsidian 工作流使用。

### 2.3 本项目对参考 skill 的吸收方式
- 保留“文件夹优先 + Markdown 为核心资产”的方法论。
- 不直接照搬其脚本结构；改为 Web 产品 + 标准 API + 数据库索引。
- 将其单用户、本地脚本风格扩展为多用户 Web 管理系统。
- 将 SM-2 复习替换为 FSRS。

## 3. 外部能力调研结论
### 3.1 Obsidian 同步
当前已确认采用**增强方案**：
1. 用户指定本地 Vault 路径，系统直接写入文件。
2. 集成官方 `obsidian-headless` CLI，由管理员在设置中配置命令路径、vault 标识、config dir、device name，并在写入后触发同步。
3. 保留自定义同步 hook 扩展能力，但首版不绑定第三方 LiveSync 协议。

### 3.2 Mermaid + HTML 渲染
前端采用 `react-markdown + remark-gfm + rehype-raw + rehype-sanitize`，并针对 mermaid code block 做自定义渲染组件，以兼容 Markdown 中的原生 HTML 与 Mermaid。

### 3.3 FSRS
后端优先使用 Python FSRS 实现；若生态不足，可封装稳定算法服务。首版要求：支持标准 FSRS 评分、到期计算、复习日志落库。

### 3.4 PDF 处理策略
首版 PDF 不做独立复杂版面解析链，直接进入多模态大模型理解流程，按文件页图/原文件内容交给可配置模型处理，再进入笔记生成主链。

## 4. 工程风险
- 多媒体处理链较长，必须任务化。
- 本地路径访问存在安全风险，必须路径白名单化。
- 多模型配置复杂，必须做好校验与失败提示。
- Obsidian 同步方式多样，首版需做“官方 CLI 优先、其他方案兼容”的边界控制。

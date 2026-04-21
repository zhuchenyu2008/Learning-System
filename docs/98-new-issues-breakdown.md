# 98-新问题拆解文档

## 1. 复习卡片任务疑似没走 AI
### 重点排查
- review_card_generation 当前是否仍主要依赖 `bootstrap_cards()` 规则切片
- 派生 job 是否只是把旧逻辑异步化，而没有 LLM 参与
- 与 `obsidian-study-notes` / `obsidian-spaced-recall` 的卡片生成原则差多少

## 2. 知识点总结没有预览
### 重点排查
- summaries 页是否只有产物列表，没有预览/详情联动
- summary note 是否可被 notes API 获取但前端未渲染
- 与 mindmap 页相比缺少哪一层 detail query / renderer

## 3. 思维导图内容混乱
### 重点排查
- prompt 是否过于宽泛
- 输入是否把脏内容/无关内容喂给了 mindmap 生成
- 是否需要更强的结构约束或后处理

# 80-retrieval真实命中专项验真方案

## 1. 目标
在当前最新代码基础上，专门验证“embedding retrieval 不是只执行了空阶段，而是真正在已有历史候选笔记库上发生了非空命中”。

## 2. 背景
上一轮真实回归中，虽然：
- retrieve 阶段日志已出现
- retrieval_summary 已落到结果中

但因为执行了：
- `docker compose down -v --remove-orphans`

导致数据库卷被清空，历史候选 note 库为空，最终所有成功 job 的 retrieval_summary 都表现为：
- `matched_count = 0`
- `matched_note_ids = []`
- `matched_paths = []`
- `retrieval_context_chars = 0`

因此，上一轮只能证明“retrieve 代码路径被执行”，不能证明“真实 embedding 检索已有效命中已有笔记”。

## 3. 本轮目标
本轮不再大改代码，也不再追求全来源总回归；只做 retrieval 真命中专项验真：
1. 构造并保留一批历史候选笔记
2. 确保这些候选笔记在当前实例中可被 retrieval service 读取
3. 用与候选笔记语义接近的新样本触发生成
4. 验证 retrieval_summary 为非空
5. 验证 retrieved_context 真实进入生成链

## 4. 核心原则
- **保留候选库**：本轮不得在“候选笔记已构造完”后再执行 `down -v`
- **样本要可控**：候选笔记内容与新生成样本必须是高相关主题，避免“没命中是因为样本太偏”
- **证据要闭环**：必须同时拿到 job log、result_json、最终 note/frontmatter 中的 retrieval 证据

## 5. 验证范围
优先验证文本类 retrieval：
- 候选库：人工构造 2~4 篇历史学习笔记
- 新样本：txt / md / docx 中选 1~2 个高相关样本

原因：
- 先把 retrieval 真命中这件事单独验清
- 避免被 OCR/STT 质量噪声干扰

## 6. 候选历史笔记构造策略
在当前实例运行后，手动写入一批历史 Markdown 笔记到工作区，例如：
- 数学：导数的定义、导数的几何意义
- 物理：牛顿第一定律、牛顿第二定律
- 英语：虚拟语气基础、线性回归速记（若要测计算机类）

要求：
- 内容结构清晰
- 路径放在系统当前检索可扫描到的位置
- 至少 2 篇与新样本主题高度相关

## 7. 新样本设计策略
新样本应故意与候选库主题贴近，例如：
- 如果候选库有《牛顿第一定律》《牛顿第二定律》，则新样本写“牛顿第二定律的受力分析与质量加速度关系”
- 如果候选库有《导数的定义》《导数的几何意义》，则新样本写“导数在切线斜率中的应用”

目标：
- 最大化非空 retrieval 命中概率
- 让结果具有解释力

## 8. 验证步骤
1. 启动当前最新代码实例
2. 确认 provider 配置已就绪
3. 写入候选历史笔记
4. 确认这些历史笔记能被 retrieval service 读取（必要时直接读文件/看数据库 note 记录）
5. 上传新样本并触发 note generation
6. 轮询 job 到完成
7. 抽取并核对：
   - retrieve 阶段日志
   - `retrieval_summary.matched_count > 0`
   - `matched_paths` 包含候选历史笔记路径
   - `retrieval_context_chars > 0`
   - 最终 note/frontmatter 中存在 retrieval_summary

## 9. 通过标准
以下条件全部满足，才可宣称“retrieval 真命中通过”：
1. retrieve 阶段真实执行
2. `matched_count > 0`
3. `matched_paths` 非空且与候选历史笔记一致
4. `retrieval_context_chars > 0`
5. 最终生成结果与候选主题存在合理关联，而不是空检索下的普通生成

## 10. 非目标
- 本轮不再重新判断 pdf/image/audio 质量是否达标
- 本轮不再重做全部 6 类样本总回归
- 本轮重点只在 retrieval 真命中证据

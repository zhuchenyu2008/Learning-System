# 76-学科分类、命名与落库路径详细设计

## 1. 目标
将当前按源文件名与固定目录落库的策略，升级为：
- AI 判定学科
- 系统规范化学科
- 标题采用 `标题-日期-时间`
- 按学科目录落库

## 2. 当前问题
当前：
- `title = source file stem`
- `relative_path = note_directory or notes/generated`
- 没有学科分类
- 没有命名策略
- 没有目录规范

## 3. 学科分类设计

### 3.1 目标学科集合
初版建议支持：
- 语文
- 数学
- 英语
- 物理
- 化学
- 生物
- 历史
- 地理
- 政治
- 计算机
- 通识
- 未分类

### 3.2 分类方式
- LLM 输出中文 `subject`
- 系统做 subject normalization
- 无法识别时回退 `未分类`

### 3.3 规范化策略
示例：
- `数学`、`高中数学` -> `数学`
- `英语`、`英文` -> `英语`
- `计算机`、`编程`、`CS` -> `计算机`

## 4. 路径策略

### 4.1 目标目录
建议目录：
- `notes/subjects/<学科>/`

示例：
- `notes/subjects/数学/导数概念-2026-04-20-1045.md`
- `notes/subjects/英语/虚拟语气-2026-04-20-1046.md`

### 4.2 路径构建责任
新增 path builder，负责：
- subject 规范化
- title 清洗
- 日期时间拼接
- 重名处理
- 输出 relative_path

## 5. 标题规则

### 5.1 LLM 负责什么
- 负责生成核心主题标题，如：
  - 导数的几何意义
  - 虚拟语气基础
  - 牛顿第二定律

### 5.2 系统负责什么
- 拼接日期时间
- 过滤非法字符
- 长度截断
- 重名处理

## 6. Frontmatter 设计
建议最终 frontmatter 至少包含：
- title
- subject
- subject_slug
- source_asset_id
- source_path
- source_type
- generated_at
- retrieval_summary（简版）
- warnings（如有）

## 7. 数据库设计影响
当前 `Note` 表未强制需要新增 subject 字段也可先落地：
- 先写入 `frontmatter_json.subject`
- 同时 `title` 写最终标题
- `relative_path` 写最终路径

后续如果要支持更强查询，再考虑显式加列。

## 8. 风险与对策

### 风险 1：学科分类漂移
对策：
- 系统规范化映射
- fallback 到未分类

### 风险 2：文件名非法字符
对策：
- path builder 做 sanitize

### 风险 3：同一分钟重复冲突
对策：
- 自动追加计数后缀

## 9. 验收标准
1. 最终标题符合 `标题-日期-时间`
2. relative_path 按学科目录落库
3. 学科分类有稳定规范化策略
4. 重名与非法路径问题有明确处理

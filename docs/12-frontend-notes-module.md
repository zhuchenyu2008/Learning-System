# 12-前端笔记模块实现细节文档

## 1. 页面范围
- 笔记 / 总览
- 笔记 / 笔记生成
- 笔记 / 笔记库
- 笔记详情渲染

## 2. 页面细节
### 2.1 总览
- 工作目录状态卡
- 最近扫描资产
- 最近生成笔记
- 最近 Job
- CTA：去扫描、去生成

### 2.2 笔记生成
- 扫描工作目录按钮
- 资产列表（按文件类型筛选）
- 生成按钮
- 生成状态提示
- 普通用户按钮禁用

### 2.3 笔记库
- 左侧树状目录
- 右侧列表/详情切换
- 支持 note_type/source 筛选

### 2.4 笔记详情
- Markdown 渲染
- 支持 HTML 白名单渲染
- 支持 Mermaid code block 渲染
- 展示来源文件、更新时间

## 3. API 对接
- `GET /api/v1/sources`
- `POST /api/v1/sources/scan`
- `GET /api/v1/notes`
- `GET /api/v1/notes/tree`
- `GET /api/v1/notes/{id}`
- `POST /api/v1/notes/generate`
- `GET /api/v1/jobs`

## 4. 验收标准
- 页面链路可访问
- 管理员可扫描与触发生成
- 普通用户显示禁用态
- Markdown / HTML / Mermaid 显示正常

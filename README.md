# learning-system

面向本地 Markdown 文件夹 + Obsidian 生态的 AI 笔记与复习系统。

## 项目定位
learning-system 是一个**以前后端分离架构实现**的本地学习系统，围绕用户指定的本地 Markdown / 多媒体资料目录工作，完成以下闭环：

- 录音 / 视频 / 图片 / 文本 / Markdown / PDF 导入
- 基于 OpenAI 兼容模型、多模态模型、STT、Embedding 生成 Markdown 笔记
- 将笔记写回本地工作目录 / Obsidian Vault
- 基于 FSRS 生成复习任务
- 生成知识点总结与 Mermaid 思维导图
- 提供管理员 / 普通用户权限体系、任务可见性、活动统计、数据库导入导出

## 当前状态
当前版本已完成：
- 可交付骨架
- 工程化收尾（路线 A）
- 第一轮体验增强（路线 B）

### 已完成主功能
#### 后端
- auth / health
- sources / notes / jobs
- review / FSRS / summaries / mindmaps
- settings / admin
- Celery app / worker / beat 基础闭环
- Obsidian 增强同步基础接口
- PDF / 多模态处理增强
- KnowledgePoint 抽取增强
- 用户活动快照与管理侧统计基础

#### 前端
- Notes 模块
- Review 模块
- Settings 模块
- Markdown + HTML + Mermaid 渲染
- 管理员 / 普通用户禁用态
- Jobs 可见性增强
- UI / 交互第一轮 polish

#### 工程化
- Dockerfile / docker-compose / .env.example / deployment 文档
- backend / worker / beat / frontend / postgres / redis 容器可起
- backend health 与 frontend 代理链路可达
- 前端 lint warning 清零
- 路由级拆包、Mermaid 动态加载、manualChunks 优化

## 技术栈
### 前端
- React
- Vite
- TypeScript
- React Router
- TanStack Query
- Zustand
- Tailwind / 自定义织物质感样式
- react-markdown / remark-gfm / rehype-raw / rehype-sanitize
- Mermaid

### 后端
- FastAPI
- SQLAlchemy
- Alembic
- Pydantic
- PostgreSQL
- Redis
- Celery

## 目录说明
```text
backend/      后端应用、模型、API、服务、worker、迁移
frontend/     前端应用、页面、组件、样式
docs/         总控文档、模块文档、路线文档、交付总结
```

## 本地开发
### 1. Python 环境
```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e '.[dev]'
```

### 2. 启动后端
```bash
cd backend
PYTHONPATH=../backend ../.venv/bin/uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. 启动前端
```bash
cd frontend
npm install
npm run dev -- --host 0.0.0.0 --port 18794
```

## Docker 运行
### 1. 准备环境变量
```bash
cp .env.example .env
```

如默认宿主机端口冲突，请修改 `.env` 中端口，例如：
- `FRONTEND_PORT=18080`
- `BACKEND_PORT=18000`
- `POSTGRES_PORT=15432`
- `REDIS_PORT=16379`

### 2. 构建与启动
```bash
docker compose build
docker compose up -d
```

### 3. 核验
```bash
docker compose ps
curl http://127.0.0.1:18000/api/v1/health
curl http://127.0.0.1:18080/api/v1/health
```

## Obsidian 同步方案
当前按增强方案实现：
- 本地 Vault 直写
- `obsidian-headless` 配置入口与同步触发接口

## 已知低风险遗留项
1. `watch_seconds` 上报会顺带重复累计 `page_view_count / note_view_count`，属于统计口径问题
2. Mermaid 懒加载 chunk 仍较大，属于性能优化项
3. backend recreate 后 frontend 可能短暂 502，重启 frontend 可恢复，属于部署层小尾项

## 文档索引
- `docs/24-route-a-final-report.md`
- `docs/29-final-delivery-summary.md`
- `docs/deployment.md`

## 下一步建议
如果继续下一轮迭代，优先级建议：
1. 修正 watch_seconds 统计口径
2. 继续优化 Mermaid 包体
3. 增强 PDF / 多模态质量
4. 继续增强活动分析与产品体验

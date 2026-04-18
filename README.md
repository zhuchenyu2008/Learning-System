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

### 3. 配置文件说明
#### `.env.example` / `.env`
建议先执行：
```bash
cp .env.example .env
```

常用配置项说明：

| 配置项 | 作用 | 何时需要修改 |
| --- | --- | --- |
| `APP_NAME` | 应用显示名称 | 一般无需修改 |
| `ENVIRONMENT` | 运行环境标识 | 区分开发/生产时修改 |
| `DEBUG` | 是否开启调试模式 | 生产环境应保持 `false` |
| `API_V1_PREFIX` | 后端 API 前缀 | 接口路径需要统一调整时修改 |
| `FRONTEND_PORT` | 前端宿主机端口 | 8080 被占用时修改 |
| `BACKEND_PORT` | 后端宿主机端口 | 8000 被占用时修改 |
| `POSTGRES_PORT` | PostgreSQL 宿主机端口 | 5432 被占用时修改 |
| `REDIS_PORT` | Redis 宿主机端口 | 6379 被占用时修改 |
| `VITE_API_BASE_URL` | 前端请求 API 的基础路径 | 反向代理或接口前缀变化时修改 |
| `POSTGRES_DB` / `POSTGRES_USER` / `POSTGRES_PASSWORD` | 数据库名、用户名、密码 | 首次部署或安全加固时应修改，尤其是密码 |
| `DATABASE_URL` | 后端数据库连接串 | 自定义数据库地址、账号或库名时同步修改 |
| `REDIS_URL` | Redis 连接地址 | Redis 地址或端口变化时修改 |
| `CELERY_BROKER_URL` | Celery Broker 地址 | 队列中间件变化时修改 |
| `CELERY_RESULT_BACKEND` | Celery 结果存储地址 | 结果后端变化时修改 |
| `JWT_SECRET_KEY` | JWT 签名密钥 | 生产环境必须改为高强度随机字符串 |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | 访问令牌有效期（分钟） | 登录安全策略调整时修改 |
| `REFRESH_TOKEN_EXPIRE_DAYS` | 刷新令牌有效期（天） | 登录安全策略调整时修改 |
| `INITIAL_ADMIN_USERNAME` / `INITIAL_ADMIN_PASSWORD` / `INITIAL_ADMIN_EMAIL` | 初始化管理员账号 | 首次部署前建议改成自己的值 |
| `WORKSPACE_HOST_PATH` | 宿主机学习资料目录映射路径 | 想把工作区放到其他目录时修改 |
| `WORKSPACE_ROOT` | 容器内工作区路径 | 一般无需修改 |
| `OBSIDIAN_HEADLESS_PATH` | `obsidian-headless` 可执行程序路径 | 命令不在系统 PATH 或路径不同的时候修改 |
| `OBSIDIAN_VAULT` | Obsidian Vault 路径 | 使用 Obsidian 同步时填写 |
| `OBSIDIAN_CONFIG_DIR` | Obsidian 配置目录 | 使用独立配置目录时填写 |
| `OBSIDIAN_DEVICE_NAME` | Obsidian 设备名称 | 多设备同步区分设备时填写 |

> 建议至少修改：数据库密码、`JWT_SECRET_KEY`、初始管理员账号密码。

#### `docker-compose.yml`
`docker-compose.yml` 负责定义容器编排关系，默认包含：
- `postgres`：PostgreSQL 数据库
- `redis`：缓存与队列
- `backend`：FastAPI 后端
- `worker`：Celery worker
- `beat`：Celery beat 定时任务
- `frontend`：前端静态站点 / 代理入口

通常只需要配合 `.env` 调整端口、密码、路径；除非你要改服务拓扑、镜像来源或挂载方式，否则一般不需要直接修改 compose 文件。

### 4. 核验
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

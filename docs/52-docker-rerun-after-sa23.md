# 52-回退后 Docker 普通流程重启文档

## 1. 目标
在 SA-23 回退 SA-22A 后，重新按普通 Docker 流程启动 `learning-system`，供用户直观看效果。

## 2. 普通流程
1. `docker compose down -v --remove-orphans`
2. `docker compose build`
3. `docker compose up -d`
4. `docker compose ps`
5. 验证 frontend / backend / proxy 可达

## 3. 验收标准
- 回退后的最新代码在 Docker 中成功启动
- 用户可直接访问前端查看效果

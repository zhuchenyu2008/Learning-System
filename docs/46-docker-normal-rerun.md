# 46-Docker 普通流程重启文档

## 1. 用户要求
删除当前 `learning-system` 的现有 Docker 运行实例，并按普通流程重新在 Docker 中启动最新代码。

## 2. 普通流程定义
1. `docker compose down -v --remove-orphans`
2. `docker compose build`
3. `docker compose up -d`
4. `docker compose ps`
5. `health / 页面 / 代理` 验证

## 3. 目标
- 清空当前项目 compose 范围内资源
- 按标准流程重新构建与启动
- 验证 frontend / backend / worker / beat / postgres / redis 状态
- 返回可访问地址

## 4. 范围
- 仅操作当前项目 compose 资源
- 默认沿用当前 `.env` 端口配置：18080 / 18000 / 15432 / 16379
- 不扩展新功能

## 5. 验收标准
- 普通流程成功执行
- 当前最新代码成功运行在 Docker 中
- 用户可直接开始人工测试

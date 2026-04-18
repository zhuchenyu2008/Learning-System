# 17-最终验证计划文档

## 1. 目标
在主要实现收口后进行最终整体验证，覆盖：
- 后端测试
- 前端构建
- Docker Compose 静态校验
- 关键 API 抽样
- 前后端页面/接口主链抽样

## 2. 抽样范围
### 后端
- auth
- sources / notes
- review / summaries / mindmaps
- settings / admin（若已完成）

### 前端
- notes 模块
- review 模块
- settings 模块
- 权限禁用态

### 部署
- `docker compose config`
- 环境变量说明

## 3. 输出要求
- completed / blocked / failed 分类
- 证据：命令、结果、关键文件抽样
- 问题清单与建议

## 4. 进入条件
- SA-10（后端 settings/admin）完成后再启动最终验证

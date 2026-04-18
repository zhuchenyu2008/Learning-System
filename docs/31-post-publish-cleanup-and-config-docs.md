# 31-发布后清理与配置说明文档

## 1. 用户要求
1. 删除误上传到 GitHub 的 `UNKNOWN.egg-info`
2. 将配置文件说明补入 README
3. 把配置文件中的英文注释改成中文

## 2. 当前确认
- 仓库中存在 `UNKNOWN.egg-info`
- 主要用户配置文件为：
  - `.env.example`
  - `docker-compose.yml`
- README 目前有启动方式，但缺少逐项配置字段说明

## 3. 本轮目标
- 清理误上传元数据目录并提交推送
- 为 README 增加配置文件说明章节
- 将 `.env.example` 中关键英文注释改为中文
- 必要时补 `.gitignore` 以避免再次提交 egg-info 噪声

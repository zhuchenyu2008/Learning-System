# 10-后端密码哈希兼容修整文档

## 1. 背景
在基础盘验证中，标准 `.venv` 已恢复可用，依赖可安装，后端最小导入成功。但 backend tests 在 setup 阶段被密码哈希依赖兼容问题阻塞。

## 2. 已确认现象
- `.venv` 创建成功
- `.venv` 内依赖安装成功
- `from app.main import app` 成功
- `pytest backend/tests -q` 可执行
- 测试失败集中在认证相关 setup

## 3. 当前阻塞
核心错误：
- `ValueError: password cannot be longer than 72 bytes, truncate manually if necessary`
- `AttributeError: module 'bcrypt' has no attribute '__about__'`

## 4. 修整目标
- 修复 `passlib + bcrypt` 或等效密码哈希实现兼容问题
- 不扩展业务功能
- 让 backend tests 恢复通过

## 5. 边界
- 允许修改：
  - `backend/app/core/security.py`
  - 相关依赖版本约束
  - 测试中必要但最小的兼容调整
- 不允许进入 SA-02/SA-03 功能开发
- 不改前端

## 6. 验收标准
- backend tests 通过
- 认证主链不被破坏
- 依赖版本与当前 Python 3.10 环境兼容

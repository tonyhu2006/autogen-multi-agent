# 代码风格和约定

## Python代码风格
- **遵循PEP 8标准**: 使用标准Python代码风格指南
- **编码声明**: 所有文件开头包含 `# -*- coding: utf-8 -*-`
- **Shebang**: Python脚本使用 `#!/usr/bin/env python3`

## 文档字符串
- **模块级文档**: 每个模块开头包含详细的三引号文档字符串
- **格式**: 使用标准的docstring格式，包含模块描述和功能说明
- **示例格式**:
```python
"""
模块名称 - 简短描述
==================

详细的模块功能描述和用途说明。
"""
```

## 类型注解
- **强制使用类型注解**: 所有函数参数和返回值都有类型注解
- **导入类型**: 使用 `from typing import Dict, List, Any, Optional` 等
- **示例**:
```python
async def create_agent(name: str, agent_type: str = "email") -> EnhancedEmailAgent:
```

## 命名约定
- **类名**: 使用PascalCase (如 `EnhancedEmailAgent`)
- **函数名**: 使用snake_case (如 `create_email_agent`)
- **常量**: 使用UPPER_CASE (如 `MAX_RETRIES`)
- **私有方法**: 使用单下划线前缀 (如 `_build_system_message`)

## 导入规范
- **标准库导入**: 放在最前面
- **第三方库导入**: 放在中间
- **本地模块导入**: 放在最后
- **相对导入**: 使用绝对路径，避免相对导入

## 异步编程
- **异步函数**: 大量使用 `async/await` 模式
- **异步客户端**: 使用 `aiohttp` 进行HTTP请求
- **错误处理**: 使用try/except包装异步操作

## 日志记录
- **日志配置**: 使用标准logging模块
- **日志级别**: 默认INFO级别，支持DEBUG模式
- **日志格式**: 包含时间戳、模块名、级别和消息

## 环境配置
- **环境变量**: 使用 `.env` 和 `.env.local` 文件
- **配置优先级**: `.env.local` 覆盖 `.env`
- **敏感信息**: API密钥等敏感信息不提交到版本控制
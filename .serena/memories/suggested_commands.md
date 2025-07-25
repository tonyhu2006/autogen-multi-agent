# 建议的开发命令

## Windows系统命令
由于项目运行在Windows环境，以下是常用的系统命令：

### 基本文件操作
- `dir` - 列出目录内容
- `powershell -Command "Get-ChildItem"` - PowerShell方式列出文件
- `powershell -Command "Get-Content filename"` - 查看文件内容
- `type filename` - 查看文件内容（CMD方式）
- `cd directory` - 切换目录
- `mkdir directory` - 创建目录

### Git操作
- `git status` - 查看仓库状态
- `git add .` - 添加所有更改
- `git commit -m "message"` - 提交更改
- `git push` - 推送到远程仓库
- `git pull` - 拉取远程更改
- `git branch` - 查看分支
- `git checkout -b branch-name` - 创建并切换分支

## Python环境管理
### 虚拟环境
```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境 (Windows)
venv\Scripts\activate

# 停用虚拟环境
deactivate
```

### 依赖管理
```bash
# 安装依赖
pip install -r requirements.txt

# 更新依赖
pip install --upgrade package-name

# 查看已安装包
pip list

# 生成requirements文件
pip freeze > requirements.txt
```

## 项目运行命令
### 主要启动方式
```bash
# 交互式模式
python main_v4.py
python run_v4.py --interactive

# 批量任务模式
python run_v4.py --batch tasks.json

# 演示模式
python run_v4.py --demo

# 测试模式
python run_v4.py --test

# 查看帮助
python run_v4.py --help
```

### 定时邮件服务
```bash
# 启动定时邮件服务
python scheduled_email_service.py

# 启动研究服务
python scheduled_research.py
```

### 测试和诊断
```bash
# SMTP测试
python test_direct_smtp.py

# 快速系统测试
python quick_test.py

# 调试特定问题
python debug_401_precise.py
```

## 开发工具命令
### 代码质量
```bash
# 代码格式化
black .
black filename.py

# 代码检查
flake8 .
flake8 filename.py

# 类型检查
mypy .
mypy filename.py
```

### 测试
```bash
# 运行所有测试
pytest

# 运行特定测试文件
pytest test_filename.py

# 运行异步测试
pytest -v --asyncio-mode=auto

# 生成测试覆盖率报告
pytest --cov=.
```

## 环境配置
### 环境变量设置
```bash
# 复制环境配置模板
copy .env.example .env.local

# 编辑环境配置 (使用记事本)
notepad .env.local

# 编辑环境配置 (使用VS Code)
code .env.local
```

### 配置验证
```bash
# 检查环境变量
python -c "import os; print(os.getenv('OPENAI_API_KEY')[:10] + '...')"

# 验证配置完整性
python run_v4.py --test
```

## 日志和监控
### 查看日志
```bash
# 查看所有日志文件
dir *.log

# 查看特定日志
type autogen_system_v4.log
type scheduled_email_simple.log

# 实时监控日志 (PowerShell)
powershell -Command "Get-Content -Path 'autogen_system_v4.log' -Wait"
```

## 项目维护
### 清理操作
```bash
# 清理Python缓存
powershell -Command "Get-ChildItem -Path . -Recurse -Name '__pycache__' | Remove-Item -Recurse -Force"

# 清理日志文件
del *.log

# 清理临时文件
del *.tmp
del *.temp
```

### 备份操作
```bash
# 备份配置文件
copy .env.local .env.local.backup

# 备份邮件调度配置
copy email_schedules.json email_schedules.json.backup
```
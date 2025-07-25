# 技术栈和依赖

## 核心技术栈
- **Python**: 3.8+ (推荐3.10+)
- **AutoGen**: v0.4+ (Microsoft AutoGen框架)
- **AI模型**: Gemini Balance API (通过OpenAI兼容接口)
- **异步编程**: asyncio, aiohttp
- **环境管理**: python-dotenv
- **数据验证**: pydantic v2.0+

## 主要依赖包
### AutoGen相关
- `autogen-agentchat>=0.4.0` - 核心多代理聊天功能
- `autogen-ext[openai]>=0.4.0` - OpenAI扩展
- `autogen-core>=0.4.0` - 核心功能
- `openai>=1.0.0` - OpenAI API客户端

### 外部API集成
- `google-auth>=2.0.0` - Google认证
- `google-api-python-client>=2.0.0` - Google API客户端
- `requests>=2.28.0` - HTTP请求

### 定时任务
- `schedule>=1.2.0` - 任务调度
- `pytz>=2023.3` - 时区处理

### 数据处理
- `pandas>=1.5.0` - 数据分析
- `numpy>=1.24.0` - 数值计算
- `beautifulsoup4>=4.11.0` - HTML解析
- `lxml>=4.9.0` - XML处理

### 认知工具
- `scikit-learn>=1.3.0` - 机器学习
- `nltk>=3.8.0` - 自然语言处理
- `spacy>=3.6.0` - 高级NLP

### 开发工具
- `pytest>=7.0.0` - 测试框架
- `pytest-asyncio>=0.21.0` - 异步测试
- `black>=23.0.0` - 代码格式化
- `flake8>=6.0.0` - 代码检查
- `mypy>=1.0.0` - 类型检查

### 日志和监控
- `structlog>=23.0.0` - 结构化日志
- `rich>=13.0.0` - 富文本输出

## 系统要求
- **操作系统**: Windows (当前环境), macOS, Linux
- **Python版本**: 3.8+ (推荐3.10+)
- **内存**: 建议4GB+
- **网络**: 需要访问Gemini Balance API和SMTP服务
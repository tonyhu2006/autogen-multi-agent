# 配置指南

## 环境配置

### 必需配置项
在 `.env.local` 文件中设置以下必需的环境变量：

```env
# Gemini Balance API配置（必需）
OPENAI_API_KEY=your_gemini_balance_api_key_here
OPENAI_BASE_URL=http://your-gemini-balance-url/v1
OPENAI_MODEL=gemini-2.5-flash

# SMTP邮件配置（必需）
SENDER_EMAIL=your-email@gmail.com
SENDER_PASSWORD=your_16_digit_app_password
SENDER_NAME=AI研究系统
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
```

### 可选配置项
```env
# 测试邮件配置
TEST_RECIPIENT_EMAIL=your-test-email@example.com

# Brave Search API配置
BRAVE_SEARCH_API_KEY=your_brave_search_api_key

# Azure OpenAI配置（如需使用Azure）
AZURE_OPENAI_API_KEY=your_azure_openai_api_key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_VERSION=2024-02-15-preview
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4

# 系统配置
LOG_LEVEL=INFO
MAX_RETRIES=3
REQUEST_TIMEOUT=30
FIELD_RESONANCE_THRESHOLD=0.8

# 认知工具配置
COGNITIVE_ANALYSIS_LEVEL=deep
ENABLE_FIELD_RESONANCE=true
ENABLE_SELF_REPAIR=true
PROTOCOL_SHELL_VERSION=1.0.0
```

## Gmail SMTP配置详解

### 1. 启用两步验证
1. 访问 [Google账户设置](https://myaccount.google.com/)
2. 选择"安全" → "两步验证"
3. 按照指引完成两步验证设置

### 2. 生成应用密码
1. 在"安全"页面选择"两步验证" → "应用密码"
2. 选择"邮件"和设备类型
3. 复制生成的16位密码
4. 在 `.env.local` 中使用此密码作为 `SENDER_PASSWORD`

### 3. 测试SMTP配置
```bash
python test_direct_smtp.py
```

## 邮件调度配置

### email_schedules.json 结构
```json
{
  "schedules": [
    {
      "topic": "AGI人工智能",
      "recipient": "recipient@example.com",
      "schedule_time": "09:00",
      "frequency": "daily",
      "subject_template": "每日AGI研究动态 - {date}",
      "enabled": true
    }
  ]
}
```

### 配置参数说明
- **topic**: 研究主题关键词
- **recipient**: 收件人邮箱地址
- **schedule_time**: 发送时间（24小时制）
- **frequency**: 发送频率（daily/weekly/monthly）
- **subject_template**: 邮件主题模板，支持{date}变量
- **enabled**: 是否启用此调度

## API配置

### Gemini Balance API
1. 获取API密钥和端点URL
2. 确认模型名称（如gemini-2.5-flash）
3. 测试API连接：
```bash
curl -H "x-goog-api-key: $OPENAI_API_KEY" $OPENAI_BASE_URL/models
```

### SearXNG搜索引擎配置（可选）
如需使用本地搜索引擎，可配置SearXNG：
```env
SEARCH_ENGINE_BASE_URL=http://localhost:8080
SEARCH_ENGINE_API_KEY=  # SearXNG不需要API Key
```

## 认知工具配置

### 认知分析级别
- **BASIC**: 基础认知分析
- **DEEP**: 深度认知分析（推荐）
- **DEEPER**: 更深层认知分析
- **ULTRA**: 超深度认知分析

### 协议Shell配置
- **ENABLE_FIELD_RESONANCE**: 启用场共振功能
- **ENABLE_SELF_REPAIR**: 启用自我修复功能
- **PROTOCOL_SHELL_VERSION**: 协议Shell版本

## 配置验证

### 环境变量检查
```python
import os
from dotenv import load_dotenv

load_dotenv('.env.local')

# 检查必需变量
required_vars = ["OPENAI_API_KEY", "OPENAI_BASE_URL", "SENDER_EMAIL", "SENDER_PASSWORD"]
for var in required_vars:
    value = os.getenv(var)
    if value:
        print(f"✓ {var}: {'*' * 10}...")
    else:
        print(f"✗ {var}: 未设置")
```

### 系统配置测试
```bash
# 完整系统测试
python run_v4.py --test

# SMTP配置测试
python test_direct_smtp.py

# 快速功能测试
python quick_test.py
```

## 故障排除

### 常见配置问题
1. **API密钥错误**: 检查密钥格式和有效性
2. **SMTP认证失败**: 确认使用应用密码而非账户密码
3. **端口被占用**: 修改SMTP_PORT或检查防火墙设置
4. **环境变量未加载**: 确认文件名为`.env.local`且格式正确

### 配置文件优先级
1. `.env.local` - 本地配置（最高优先级）
2. `.env` - 通用配置
3. 系统环境变量
4. 代码中的默认值
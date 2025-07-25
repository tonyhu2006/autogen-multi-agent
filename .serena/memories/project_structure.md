# 项目结构

## 目录结构
```
autogen-multi-agent/
├── agents/                     # 代理模块
│   ├── base_agent_v4.py       # 基础代理类
│   ├── email_agent_v4.py      # 邮件代理
│   ├── research_agent_v4.py   # 研究代理
│   └── research_agent_local.py # 本地研究代理
├── teams/                      # 团队协调模块
│   └── team_coordinator_v4.py # 团队协调器
├── cognitive_context/          # 认知增强模块
│   ├── cognitive_analysis.py  # 认知分析工具
│   └── protocol_shells.py     # 协议Shell
├── clients/                    # API客户端
│   └── gemini_client.py       # Gemini客户端
├── utils/                      # 工具模块
│   └── env_cache_manager.py   # 环境缓存管理
├── tasks/                      # 任务相关（空目录）
├── .serena/                    # Serena工具配置
│   └── memories/              # 项目记忆文件
├── main_v4.py                 # 主程序入口
├── run_v4.py                  # 启动脚本
├── scheduled_email_service.py # 定时邮件服务
├── scheduled_research.py      # 定时研究服务
├── quick_test.py              # 快速测试
├── debug_401_precise.py       # 调试脚本
├── requirements.txt           # Python依赖
├── .env.example              # 环境配置模板
├── .env.local                # 本地环境配置
├── .gitignore                # Git忽略规则
├── LICENSE                   # 许可证
└── README.md                 # 项目文档
```

## 核心模块说明

### agents/ - 代理模块
- **base_agent_v4.py**: 增强型代理基类，提供认知工具和协议Shell集成
- **email_agent_v4.py**: 邮件代理，负责智能邮件生成和SMTP发送
- **research_agent_v4.py**: 研究代理，提供智能搜索、分析和报告生成
- **research_agent_local.py**: 本地研究代理实现

### teams/ - 团队协调
- **team_coordinator_v4.py**: 智能协调器，配备AI大脑进行任务路由决策

### cognitive_context/ - 认知增强
- **cognitive_analysis.py**: 基于IBM认知工具的分析模块
- **protocol_shells.py**: 结构化代理通信协议

### clients/ - API客户端
- **gemini_client.py**: Gemini Balance API客户端封装

### utils/ - 工具模块
- **env_cache_manager.py**: 环境变量缓存管理

## 主要文件说明

### 核心程序
- **main_v4.py**: 主程序，包含AutoGenMultiAgentSystem类和交互式模式
- **run_v4.py**: 多模式启动脚本，支持交互、批量、演示、测试模式

### 服务程序
- **scheduled_email_service.py**: 定时邮件服务，提供完整的CLI管理界面
- **scheduled_research.py**: 定时研究任务执行服务

### 测试和调试
- **quick_test.py**: 快速系统测试脚本
- **debug_401_precise.py**: 专门用于调试401认证错误

### 配置文件
- **.env.example**: 环境配置模板，包含所有必需和可选配置项
- **.env.local**: 本地环境配置（不提交到版本控制）
- **email_schedules.json**: 邮件调度配置（运行时生成）

## 文件大小和复杂度
- **大型文件** (>20KB): 
  - main_v4.py (8KB)
  - README.md (24KB)
  - base_agent_v4.py (33KB)
  - team_coordinator_v4.py (32KB)
- **中型文件** (10-20KB):
  - email_agent_v4.py (27KB)
  - research_agent_v4.py (23KB)
  - protocol_shells.py (22KB)
- **小型文件** (<10KB): 其他工具和配置文件

## 模块化设计特点
- **清晰的职责分离**: 每个模块有明确的功能边界
- **统一的接口设计**: 所有代理继承自基础代理类
- **可扩展架构**: 易于添加新的代理类型和功能
- **配置驱动**: 通过环境变量和JSON文件进行配置管理
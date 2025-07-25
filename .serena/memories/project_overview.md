# AutoGen Multi-Agent AI System 项目概述

## 项目目的
AutoGen v0.4+ Multi-Agent AI System 是一个基于Microsoft AutoGen框架的智能自动化平台，专为企业级AI应用设计。系统集成了多代理协作、智能研究、定时邮件服务等功能，支持Gemini Balance API，提供完整的AI工作流解决方案。

## 核心功能
- 🤖 **多代理协作**: 基于AutoGen v0.4+的智能代理系统
- 📧 **定时邮件服务**: 自动生成和发送AI研究报告
- 🧠 **认知增强**: 集成Context-Engineering认知工具
- 🔄 **实时SMTP**: 真实邮件发送，支持Gmail等主流服务
- 🎯 **灵活调度**: 支持每日/每周/每月定时任务

## 主要组件
- **智能协调器**: `teams/team_coordinator_v4.py` - AI智能大脑，负责任务路由决策和代理调度
- **代理工厂**: `agents/base_agent_v4.py` - 创建代理并注入AI模型客户端
- **研究代理**: `agents/research_agent_v4.py` - 基于AI模型的智能搜索和分析
- **邮件代理**: `agents/email_agent_v4.py` - 基于AI模型的智能邮件生成和SMTP发送
- **认知工具**: `cognitive_context/` - 认知分析和协议Shell
- **主系统**: `main_v4.py` - 用户交互和会话管理
- **启动器**: `run_v4.py` - 多模式启动脚本

## 系统架构特点
- 统一AI模型注入：所有专业代理通过工厂函数统一获得AI模型客户端
- OpenAI兼容架构：所有AI调用统一使用OpenAI兼容格式，连接Gemini Balance API
- 深度认知能力：每个代理都配备CognitiveLevel.DEEP认知水平
- 智能任务分配：基于用户请求的复杂度、专业性和紧急程度进行智能分配
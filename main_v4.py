#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AutoGen多代理AI系统 - 主程序 (v0.4+ API)
========================================

基于Microsoft AutoGen v0.4+框架的现代化多代理AI系统，
集成认知增强、研究分析和邮件通信功能。
"""

import os
import sys
import asyncio
import logging
import json
from typing import Dict, List, Any, Optional
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# AutoGen v0.4+ imports
from autogen_agentchat.messages import TextMessage
from autogen_ext.models.openai import OpenAIChatCompletionClient

# 导入项目组件 (v0.4)
from agents.base_agent_v4 import EnhancedAssistantAgent
from agents.research_agent_v4 import EnhancedResearchAgent, create_research_agent
from agents.email_agent_v4 import EnhancedEmailAgent, create_email_agent
from teams.team_coordinator_v4 import TeamCoordinator, TaskType, TaskPriority
from cognitive_context.cognitive_analysis import CognitiveTools, CognitiveLevel
from cognitive_context.protocol_shells import ProtocolShellManager, ProtocolType

# 环境配置
from dotenv import load_dotenv
# 优先加载 .env.local，然后是 .env
load_dotenv('.env.local')
load_dotenv('.env')

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('autogen_system_v4.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class AutoGenMultiAgentSystem:
    """AutoGen多代理AI系统 (v0.4)"""
    
    def __init__(self):
        """初始化多代理系统"""
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.base_url = os.getenv("OPENAI_BASE_URL")
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o")
        self.brave_api_key = os.getenv("BRAVE_API_KEY")
        self.search_engine_url = os.getenv("SEARCH_ENGINE_BASE_URL")
        self.search_engine_api_key = os.getenv("SEARCH_ENGINE_API_KEY")
        
        # 邮件配置
        self.sender_email = os.getenv("SENDER_EMAIL")
        self.sender_password = os.getenv("SENDER_PASSWORD")
        self.sender_name = os.getenv("SENDER_NAME", "AI研究系统")
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        
        # 其他配置
        self.cognitive_level = os.getenv("COGNITIVE_ANALYSIS_LEVEL", "standard")
        self.enable_field_resonance = os.getenv("ENABLE_FIELD_RESONANCE", "false").lower() == "true"
        self.max_retries = int(os.getenv("MAX_RETRIES", "3"))
        self.default_recipients = os.getenv("DEFAULT_RECIPIENTS", "").split(",") if os.getenv("DEFAULT_RECIPIENTS") else []
        
        # 验证API密钥
        if not self.api_key:
            raise ValueError("未找到OPENAI_API_KEY环境变量")
        
        # 初始化组件
        self.coordinator = None
        self.cognitive_tools = CognitiveTools()
        self.protocol_shell_manager = ProtocolShellManager()
        
        # 系统状态
        self.is_initialized = False
        self.session_history = []
        
        logger.info("AutoGen多代理AI系统 (v0.4) 初始化开始")

    async def initialize(self):
        """初始化系统组件"""
        try:
            logger.info("正在初始化系统组件...")
            
            # 初始化协议Shell管理器
            await self.protocol_shell_manager.initialize_protocols()
            
            # 创建团队协调器
            self.coordinator = TeamCoordinator(
                name="AI系统协调器",
                api_key=self.api_key,
                base_url=self.base_url,
                model=self.model,
                max_agents=20
            )
            
            # 创建核心代理
            await self._create_core_agents()
            
            # 创建默认团队
            await self._create_default_teams()
            
            self.is_initialized = True
            logger.info("系统初始化完成")
            
        except Exception as e:
            logger.error(f"系统初始化失败: {e}")
            raise

    async def _create_core_agents(self):
        """创建核心代理"""
        try:
            # 创建研究代理
            await self.coordinator.create_agent(
                agent_type="research",
                name="AI研究专家",
                brave_api_key=self.brave_api_key,
                search_engine_url=self.search_engine_url,
                search_engine_api_key=self.search_engine_api_key,
                cognitive_level=CognitiveLevel.DEEP
            )
            
            # 创建邮件代理
            await self.coordinator.create_agent(
                agent_type="email",
                name="智能邮件助手",
                sender_email=self.sender_email,
                sender_password=self.sender_password,
                sender_name=self.sender_name,
                smtp_server=self.smtp_server,
                smtp_port=self.smtp_port,
                default_recipients=self.default_recipients,
                cognitive_level=CognitiveLevel.BASIC
            )
            
            # 创建通用助手代理
            await self.coordinator.create_agent(
                agent_type="assistant",
                name="通用AI助手",
                cognitive_level=CognitiveLevel.BASIC
            )
            
            # 创建分析代理
            await self.coordinator.create_agent(
                agent_type="assistant",
                name="数据分析专家",
                cognitive_level=CognitiveLevel.DEEP
            )
            
            logger.info("核心代理创建完成")
            
        except Exception as e:
            logger.error(f"创建核心代理失败: {e}")
            raise

    async def _create_default_teams(self):
        """创建默认团队"""
        try:
            # 创建研究团队
            await self.coordinator.create_team(
                team_name="研究团队",
                agent_names=["AI研究专家", "数据分析专家"],
                team_type="round_robin"
            )
            
            # 创建通信团队
            await self.coordinator.create_team(
                team_name="通信团队",
                agent_names=["智能邮件助手", "通用AI助手"],
                team_type="round_robin"
            )
            
            # 创建综合团队
            await self.coordinator.create_team(
                team_name="综合团队",
                agent_names=["AI研究专家", "智能邮件助手", "通用AI助手", "数据分析专家"],
                team_type="round_robin"
            )
            
            logger.info("默认团队创建完成")
            
        except Exception as e:
            logger.error(f"创建默认团队失败: {e}")
            raise

    async def process_user_request(self, user_input: str) -> Dict[str, Any]:
        """处理用户请求"""
        try:
            if not self.is_initialized:
                await self.initialize()
            
            logger.info(f"处理用户请求: {user_input[:100]}...")
            
            # 分析用户请求
            request_analysis = await self._analyze_user_request(user_input)
            
            # 根据分析结果路由任务
            result = await self._route_and_execute_task(user_input, request_analysis)
            
            # 记录会话历史
            session_record = {
                "timestamp": datetime.now().isoformat(),
                "user_input": user_input,
                "analysis": request_analysis,
                "result": result
            }
            self.session_history.append(session_record)
            
            return result
            
        except Exception as e:
            logger.error(f"处理用户请求失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "处理请求时发生错误"
            }

    async def _analyze_user_request(self, user_input: str) -> Dict[str, Any]:
        """分析用户请求"""
        try:
            # 使用认知工具分析
            cognitive_analysis = self.cognitive_tools.analyze_text(
                user_input,
                level=CognitiveLevel.BASIC
            )
            
            # 确定任务类型
            task_type = self._determine_task_type(user_input, cognitive_analysis)
            
            # 确定优先级
            priority = self._determine_priority(user_input, cognitive_analysis)
            
            # 选择最佳执行者
            executor = self._select_executor(task_type, user_input)
            
            return {
                "task_type": task_type,
                "priority": priority,
                "executor": executor,
                "cognitive_analysis": cognitive_analysis,
                "requires_team": self._requires_team_collaboration(user_input)
            }
            
        except Exception as e:
            logger.error(f"请求分析失败: {e}")
            return {
                "task_type": TaskType.GENERAL,
                "priority": TaskPriority.MEDIUM,
                "executor": "通用AI助手",
                "error": str(e)
            }

    def _determine_task_type(self, user_input: str, analysis: Dict[str, Any]) -> TaskType:
        """确定任务类型"""
        user_input_lower = user_input.lower()
        key_concepts = analysis.get("key_concepts", [])
        
        # 研究相关关键词
        research_keywords = ["研究", "调查", "分析", "搜索", "查找", "了解", "research", "investigate", "analyze"]
        if any(keyword in user_input_lower for keyword in research_keywords):
            return TaskType.RESEARCH
        
        # 邮件相关关键词
        email_keywords = ["邮件", "发送", "写信", "通知", "email", "send", "write", "notify"]
        if any(keyword in user_input_lower for keyword in email_keywords):
            return TaskType.EMAIL
        
        # 分析相关关键词
        analysis_keywords = ["分析", "统计", "计算", "评估", "analyze", "calculate", "evaluate"]
        if any(keyword in user_input_lower for keyword in analysis_keywords):
            return TaskType.ANALYSIS
        
        return TaskType.GENERAL

    def _determine_priority(self, user_input: str, analysis: Dict[str, Any]) -> TaskPriority:
        """确定任务优先级"""
        user_input_lower = user_input.lower()
        
        # 紧急关键词
        urgent_keywords = ["紧急", "立即", "马上", "urgent", "immediate", "asap"]
        if any(keyword in user_input_lower for keyword in urgent_keywords):
            return TaskPriority.URGENT
        
        # 高优先级关键词
        high_keywords = ["重要", "优先", "关键", "important", "priority", "critical"]
        if any(keyword in user_input_lower for keyword in high_keywords):
            return TaskPriority.HIGH
        
        # 低优先级关键词
        low_keywords = ["稍后", "有时间", "不急", "later", "when possible", "low priority"]
        if any(keyword in user_input_lower for keyword in low_keywords):
            return TaskPriority.LOW
        
        return TaskPriority.MEDIUM

    def _select_executor(self, task_type: TaskType, user_input: str) -> str:
        """选择执行者"""
        if task_type == TaskType.RESEARCH:
            return "AI研究专家"
        elif task_type == TaskType.EMAIL:
            return "智能邮件助手"
        elif task_type == TaskType.ANALYSIS:
            return "数据分析专家"
        else:
            return "通用AI助手"

    def _requires_team_collaboration(self, user_input: str) -> bool:
        """判断是否需要团队协作"""
        collaboration_keywords = [
            "复杂", "多方面", "综合", "协作", "团队",
            "complex", "comprehensive", "collaborate", "team"
        ]
        
        user_input_lower = user_input.lower()
        return any(keyword in user_input_lower for keyword in collaboration_keywords)

    async def _route_and_execute_task(
        self,
        user_input: str,
        analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """路由并执行任务"""
        try:
            task_type = analysis["task_type"]
            priority = analysis["priority"]
            executor = analysis["executor"]
            requires_team = analysis.get("requires_team", False)
            
            if requires_team:
                # 团队协作执行
                result = await self._execute_team_task(user_input, analysis)
            else:
                # 单个代理执行
                result = await self._execute_single_agent_task(user_input, analysis)
            
            return {
                "success": True,
                "task_type": task_type.value if hasattr(task_type, 'value') else str(task_type),
                "executor": executor,
                "requires_team": requires_team,
                "result": result
            }
            
        except Exception as e:
            logger.error(f"任务执行失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def _execute_single_agent_task(
        self,
        user_input: str,
        analysis: Dict[str, Any]
    ) -> str:
        """执行单个代理任务"""
        try:
            executor = analysis["executor"]
            
            # 创建任务ID
            task_id = f"task_{int(datetime.now().timestamp())}"
            
            # 添加任务到协调器
            await self.coordinator.add_task(
                task_id=task_id,
                description=user_input,
                task_type=analysis["task_type"],
                priority=analysis["priority"],
                assigned_agent=executor
            )
            
            # 执行任务
            task_result = await self.coordinator.execute_next_task()
            
            if task_result and task_result["status"] == "completed":
                return task_result["result"]["result"]
            else:
                error_msg = task_result.get("error", "任务执行失败") if task_result else "任务执行失败"
                return f"任务执行失败: {error_msg}"
                
        except Exception as e:
            logger.error(f"单个代理任务执行失败: {e}")
            return f"任务执行失败: {str(e)}"

    async def _execute_team_task(
        self,
        user_input: str,
        analysis: Dict[str, Any]
    ) -> str:
        """执行团队协作任务"""
        try:
            # 选择合适的团队
            team_name = self._select_team(analysis["task_type"])
            
            # 执行协调会话
            session_result = await self.coordinator.coordinate_session(
                session_description=user_input,
                participants=[team_name],
                max_rounds=5
            )
            
            if session_result["success"]:
                return session_result["data"]["result"]
            else:
                return f"团队协作失败: {session_result['error']}"
                
        except Exception as e:
            logger.error(f"团队任务执行失败: {e}")
            return f"团队任务执行失败: {str(e)}"

    def _select_team(self, task_type: TaskType) -> str:
        """选择合适的团队"""
        if task_type == TaskType.RESEARCH:
            return "研究团队"
        elif task_type == TaskType.EMAIL:
            return "通信团队"
        else:
            return "综合团队"

    async def get_system_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        if not self.coordinator:
            return {"status": "not_initialized"}
        
        return {
            "status": "active" if self.is_initialized else "initializing",
            "coordination_metrics": self.coordinator.get_coordination_metrics(),
            "session_count": len(self.session_history),
            "last_activity": self.session_history[-1]["timestamp"] if self.session_history else None
        }

    async def shutdown(self):
        """关闭系统"""
        try:
            logger.info("正在关闭AutoGen多代理AI系统...")
            
            if self.coordinator:
                await self.coordinator.shutdown()
            
            # 保存会话历史
            await self._save_session_history()
            
            logger.info("系统已关闭")
            
        except Exception as e:
            logger.error(f"系统关闭失败: {e}")

    async def _save_session_history(self):
        """保存会话历史"""
        try:
            if self.session_history:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"session_history_{timestamp}.json"
                
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(self.session_history, f, ensure_ascii=False, indent=2)
                
                logger.info(f"会话历史已保存到: {filename}")
                
        except Exception as e:
            logger.error(f"保存会话历史失败: {e}")


async def interactive_mode():
    """交互式模式"""
    system = AutoGenMultiAgentSystem()
    
    try:
        print("🤖 AutoGen多代理AI系统 (v0.4) 启动中...")
        await system.initialize()
        print("✅ 系统初始化完成！")
        print("💡 输入 'help' 查看帮助，输入 'quit' 退出系统")
        print("-" * 50)
        
        while True:
            try:
                user_input = input("\n👤 您: ").strip()
                
                if not user_input:
                    continue
                
                if user_input.lower() in ['quit', 'exit', '退出']:
                    break
                
                if user_input.lower() == 'help':
                    print_help()
                    continue
                
                if user_input.lower() == 'status':
                    status = await system.get_system_status()
                    print(f"📊 系统状态: {json.dumps(status, indent=2, ensure_ascii=False)}")
                    continue
                
                print("🔄 处理中...")
                result = await system.process_user_request(user_input)
                
                if result["success"]:
                    print(f"🤖 AI: {result['result']}")
                else:
                    print(f"❌ 错误: {result.get('message', result.get('error', '未知错误'))}")
                
            except KeyboardInterrupt:
                print("\n\n👋 收到中断信号，正在退出...")
                break
            except Exception as e:
                print(f"❌ 处理错误: {e}")
        
    finally:
        await system.shutdown()
        print("👋 再见！")


def print_help():
    """打印帮助信息"""
    help_text = """
🤖 AutoGen多代理AI系统 (v0.4) - 帮助信息

📋 可用命令:
  help     - 显示此帮助信息
  status   - 显示系统状态
  quit     - 退出系统

🎯 支持的任务类型:
  🔍 研究任务 - 使用关键词: 研究、调查、分析、搜索
  📧 邮件任务 - 使用关键词: 邮件、发送、写信、通知
  📊 分析任务 - 使用关键词: 分析、统计、计算、评估
  💬 通用对话 - 其他所有类型的对话

🚀 示例用法:
  "研究人工智能在医疗领域的应用"
  "帮我写一封项目进度汇报邮件"
  "分析这个数据集的特征"
  "你好，请介绍一下你的功能"

💡 提示: 使用"紧急"、"重要"等词汇可以调整任务优先级
"""
    print(help_text)


async def main():
    """主函数"""
    try:
        await interactive_mode()
    except Exception as e:
        logger.error(f"主程序错误: {e}")
        print(f"❌ 系统错误: {e}")


if __name__ == "__main__":
    # 运行主程序
    asyncio.run(main())

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
团队协调器 - AutoGen v0.4+ API版本
=================================

基于AutoGen v0.4+的现代化团队协调器实现，
管理多个AI代理的协作和任务分配。
"""

import os
import asyncio
import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from enum import Enum

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.base import ChatAgent
from autogen_agentchat.teams import RoundRobinGroupChat, Swarm
from autogen_agentchat.messages import TextMessage
from autogen_ext.models.openai import OpenAIChatCompletionClient

# 导入自定义 Gemini 客户端
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from clients.gemini_client import create_gemini_client

from dotenv import load_dotenv

# 导入代理
from agents.base_agent_v4 import EnhancedAssistantAgent
from agents.research_agent_v4 import EnhancedResearchAgent, create_research_agent
from agents.email_agent_v4 import EnhancedEmailAgent, create_email_agent
from cognitive_context.cognitive_analysis import CognitiveLevel

# 加载环境变量
load_dotenv()

# 配置日志
logger = logging.getLogger(__name__)


class TaskType(Enum):
    """任务类型枚举"""
    RESEARCH = "research"
    EMAIL = "email"
    ANALYSIS = "analysis"
    COORDINATION = "coordination"
    GENERAL = "general"


class TaskPriority(Enum):
    """任务优先级枚举"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    URGENT = 4


class TaskStatus(Enum):
    """任务状态枚举"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TeamCoordinator:
    """团队协调器 - 管理多个AI代理的协作"""
    
    def __init__(
        self,
        name: str = "团队协调器",
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: str = "gpt-4o",
        max_agents: int = 10
    ):
        """
        初始化团队协调器。
        
        Args:
            name: 协调器名称
            api_key: OpenAI API密钥
            model: 使用的模型
            max_agents: 最大代理数量
        """
        self.name = name
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.base_url = base_url or os.getenv("OPENAI_BASE_URL")
        self.model = model or os.getenv("OPENAI_MODEL", "gemini-2.5-flash")
        self.max_agents = max_agents
        
        # AI智能大脑 - 使 Team Coordinator 成为智能 AI 代理
        self.ai_brain = None
        self._initialize_ai_brain()
        
        # 代理管理
        self.agents: Dict[str, ChatAgent] = {}
        self.agent_capabilities: Dict[str, List[str]] = {}
        self.agent_status: Dict[str, str] = {}
        
        # 团队管理
        self.teams: Dict[str, Union[RoundRobinGroupChat, Swarm]] = {}
        self.active_team: Optional[str] = None
        
        # 任务管理
        self.tasks: Dict[str, Dict[str, Any]] = {}
        self.task_queue: List[str] = []
        self.task_history: List[Dict[str, Any]] = []
        
        # 协调指标
        self.coordination_metrics = {
            "tasks_completed": 0,
            "tasks_failed": 0,
            "agents_created": 0,
            "teams_created": 0,
            "coordination_sessions": 0
        }
        
        logger.info(f"团队协调器 '{name}' 初始化完成")
        if self.ai_brain:
            logger.info(f"AI智能大脑已启用，使用模型: {self.model}")
    
    def _initialize_ai_brain(self):
        """初始化 AI 智能大脑"""
        try:
            if self.api_key and self.base_url:
                # 使用 Gemini 客户端作为 AI 大脑
                self.ai_brain = create_gemini_client(
                    api_key=self.api_key,
                    base_url=self.base_url,
                    model=self.model
                )
                logger.info("Team Coordinator AI大脑初始化成功")
            else:
                logger.warning("AI大脑初始化失败：缺少 API 密钥或 Base URL")
        except Exception as e:
            logger.error(f"AI大脑初始化错误: {e}")
            self.ai_brain = None
    
    async def _intelligent_task_routing(self, user_request: str) -> Dict[str, Any]:
        """使用 AI 大脑进行智能任务路由决策"""
        if not self.ai_brain:
            # 如果没有 AI 大脑，使用简单的关键词匹配
            return self._fallback_routing(user_request)
        
        try:
            # 构建智能路由提示
            routing_prompt = f"""作为一个智能的团队协调器，请分析以下用户请求并决定最适合的任务类型和执行者。

用户请求：{user_request}

可用的任务类型和执行者：
1. RESEARCH - AI研究专家：适用于复杂研究任务、深度分析、学术调查
2. EMAIL - 智能邮件助手：适用于邮件发送、通知、沟通任务
3. ANALYSIS - 数据分析专家：适用于数据分析、统计计算、评估任务
4. GENERAL - 通用AI助手：适用于简单对话、实时信息查询、日常问题

请考虑以下因素：
- 任务的复杂度和专业性
- 是否需要实时信息或搜索
- 用户期望的回答风格（简洁 vs 详细）
- 任务的紧急程度

请以JSON格式返回决策：
{{
    "task_type": "任务类型",
    "executor": "执行者名称",
    "priority": "优先级(LOW/MEDIUM/HIGH/URGENT)",
    "reasoning": "决策理由",
    "expected_response_style": "期望的回答风格"
}}"""
            
            # 调用 AI 大脑进行智能决策（使用 OpenAI 兼容格式）
            import aiohttp
            import json
            
            api_url = f"{self.base_url}/v1/chat/completions"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            
            payload = {
                "model": self.model,
                "messages": [{
                    "role": "user",
                    "content": routing_prompt
                }],
                "temperature": 0.3,  # 低温度保证决策稳定性
                "max_tokens": 1000
            }
            
            # 设置30秒超时保护
            timeout = aiohttp.ClientTimeout(total=30)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(api_url, headers=headers, json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        # 使用 OpenAI 兼容格式解析响应
                        ai_response = data['choices'][0]['message']['content']
                        
                        # 解析 AI 的 JSON 回答
                        try:
                            # 提取 JSON 部分
                            json_start = ai_response.find('{')
                            json_end = ai_response.rfind('}') + 1
                            if json_start != -1 and json_end != -1:
                                json_str = ai_response[json_start:json_end]
                                routing_decision = json.loads(json_str)
                                
                                logger.info(f"AI智能路由决策: {routing_decision}")
                                return routing_decision
                        except json.JSONDecodeError:
                            logger.warning("AI返回的JSON格式解析失败，使用备用路由")
                    else:
                        logger.error(f"AI智能路由API调用失败: {response.status}")
                        response_text = await response.text()
                        logger.error(f"错误响应: {response_text[:200]}...")
                    
        except Exception as e:
            logger.error(f"AI智能路由错误: {e}")
        
        # 如果 AI 路由失败，使用备用路由
        return self._fallback_routing(user_request)
    
    def _fallback_routing(self, user_request: str) -> Dict[str, Any]:
        """备用路由逻辑（关键词匹配）"""
        user_input_lower = user_request.lower()
        
        # 研究相关关键词
        if any(keyword in user_input_lower for keyword in [
            "研究", "调查", "分析", "搜索", "查找", "了解", 
            "research", "investigate", "analyze", "study", "深入"
        ]):
            return {
                "task_type": "RESEARCH",
                "executor": "AI研究专家",
                "priority": "MEDIUM",
                "reasoning": "检测到研究相关关键词",
                "expected_response_style": "详细研究报告"
            }
        
        # 邮件相关关键词
        if any(keyword in user_input_lower for keyword in [
            "邮件", "发送", "写信", "通知", 
            "email", "send", "write", "notify"
        ]):
            return {
                "task_type": "EMAIL",
                "executor": "智能邮件助手",
                "priority": "HIGH",
                "reasoning": "检测到邮件相关关键词",
                "expected_response_style": "简洁直接"
            }
        
        # 分析相关关键词
        if any(keyword in user_input_lower for keyword in [
            "统计", "计算", "评估", "数据", 
            "calculate", "evaluate", "statistics", "data"
        ]):
            return {
                "task_type": "ANALYSIS",
                "executor": "数据分析专家",
                "priority": "MEDIUM",
                "reasoning": "检测到分析相关关键词",
                "expected_response_style": "结构化分析"
            }
        
        # 默认使用通用助手
        return {
            "task_type": "GENERAL",
            "executor": "通用AI助手",
            "priority": "MEDIUM",
            "reasoning": "默认路由到通用助手",
            "expected_response_style": "简洁直接"
        }

    async def create_agent(
        self,
        agent_type: str,
        name: str,
        **kwargs
    ) -> ChatAgent:
        """创建新代理"""
        try:
            if len(self.agents) >= self.max_agents:
                raise ValueError(f"已达到最大代理数量限制: {self.max_agents}")
            
            if name in self.agents:
                raise ValueError(f"代理名称 '{name}' 已存在")
            
            # 根据类型创建代理
            if agent_type == "research":
                agent = await create_research_agent(
                    name=name,
                    api_key=self.api_key,
                    base_url=self.base_url,
                    model=self.model,
                    **kwargs
                )
                capabilities = ["research", "search", "analysis", "reporting"]
                
            elif agent_type == "email":
                agent = await create_email_agent(
                    name=name,
                    api_key=self.api_key,
                    base_url=self.base_url,
                    model=self.model,
                    **kwargs
                )
                capabilities = ["email", "communication", "drafting", "sending"]
                
            elif agent_type == "assistant":
                # 创建通用助手代理 - 使用 Gemini 客户端
                if self.base_url and "gemini" in self.model.lower():
                    # 使用 Gemini 客户端
                    model_client = create_gemini_client(
                        model=self.model,
                        api_key=self.api_key,
                        base_url=self.base_url
                    )
                else:
                    # 使用 OpenAI 客户端
                    client_kwargs = {
                        "model": self.model,
                        "api_key": self.api_key
                    }
                    if self.base_url:
                        client_kwargs["base_url"] = self.base_url
                        
                    # 为非标准模型（如 Gemini）提供 model_info
                    if "gemini" in self.model.lower() or "gpt" not in self.model.lower():
                        try:
                            from autogen_ext.models.openai import ModelInfo
                            client_kwargs["model_info"] = ModelInfo(
                                family="gemini",  # AutoGen v0.4.7+ 必需字段
                                vision=False,
                                function_calling=False,
                                json_output=True
                            )
                        except ImportError:
                            # 如果无法导入ModelInfo，使用字典格式
                            client_kwargs["model_info"] = {
                                "family": "gemini",
                                "vision": False,
                                "function_calling": False,
                                "json_output": True
                            }
                    
                    model_client = OpenAIChatCompletionClient(**client_kwargs)
                agent = EnhancedAssistantAgent(
                    name=name,
                    model_client=model_client,
                    agent_type="assistant",
                    **kwargs
                )
                capabilities = ["general", "assistance", "conversation"]
                
            else:
                raise ValueError(f"不支持的代理类型: {agent_type}")
            
            # 注册代理
            self.agents[name] = agent
            self.agent_capabilities[name] = capabilities
            self.agent_status[name] = "active"
            
            self.coordination_metrics["agents_created"] += 1
            
            logger.info(f"代理 '{name}' (类型: {agent_type}) 创建成功")
            return agent
            
        except Exception as e:
            logger.error(f"创建代理错误: {e}")
            raise

    async def create_team(
        self,
        team_name: str,
        agent_names: List[str],
        team_type: str = "round_robin"
    ) -> Union[RoundRobinGroupChat, Swarm]:
        """创建代理团队"""
        try:
            if team_name in self.teams:
                raise ValueError(f"团队名称 '{team_name}' 已存在")
            
            # 验证代理存在
            team_agents = []
            for agent_name in agent_names:
                if agent_name not in self.agents:
                    raise ValueError(f"代理 '{agent_name}' 不存在")
                team_agents.append(self.agents[agent_name])
            
            # 创建团队
            if team_type == "round_robin":
                team = RoundRobinGroupChat(team_agents)
            elif team_type == "swarm":
                team = Swarm(team_agents)
            else:
                raise ValueError(f"不支持的团队类型: {team_type}")
            
            self.teams[team_name] = team
            self.coordination_metrics["teams_created"] += 1
            
            logger.info(f"团队 '{team_name}' (类型: {team_type}) 创建成功，包含 {len(team_agents)} 个代理")
            return team
            
        except Exception as e:
            logger.error(f"创建团队错误: {e}")
            raise

    async def add_task(
        self,
        task_id: str,
        description: str,
        task_type: TaskType = TaskType.GENERAL,
        priority: TaskPriority = TaskPriority.MEDIUM,
        assigned_agent: Optional[str] = None,
        assigned_team: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        use_ai_routing: bool = True
    ) -> str:
        """添加新任务（支持AI智能路由）"""
        try:
            if task_id in self.tasks:
                raise ValueError(f"任务ID '{task_id}' 已存在")
            
            # 使用 AI 智能路由决策（如果启用且未指定代理）
            routing_decision = None
            if use_ai_routing and not assigned_agent and not assigned_team:
                logger.info(f"使用AI智能大脑进行任务路由决策: {description}")
                routing_decision = await self._intelligent_task_routing(description)
                
                # 根据 AI 决策更新任务参数
                if routing_decision:
                    task_type_str = routing_decision.get("task_type", "GENERAL")
                    try:
                        task_type = TaskType(task_type_str.lower())
                    except ValueError:
                        task_type = TaskType.GENERAL
                    
                    priority_str = routing_decision.get("priority", "MEDIUM")
                    try:
                        priority = TaskPriority[priority_str]
                    except KeyError:
                        priority = TaskPriority.MEDIUM
                    
                    assigned_agent = routing_decision.get("executor")
                    
                    logger.info(f"AI路由决策结果: 任务类型={task_type.value}, 优先级={priority.name}, 执行者={assigned_agent}")
                    logger.info(f"AI决策理由: {routing_decision.get('reasoning', '未提供')}")
            
            # 创建任务
            task = {
                "id": task_id,
                "description": description,
                "type": task_type.value,
                "priority": priority.value,
                "status": TaskStatus.PENDING.value,
                "assigned_agent": assigned_agent,
                "assigned_team": assigned_team,
                "metadata": metadata or {},
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "result": None,
                "error": None,
                "ai_routing_decision": routing_decision  # 保存 AI 决策信息
            }
            
            # 自动分配代理（如果仍未指定）
            if not assigned_agent and not assigned_team:
                assigned_agent = await self._auto_assign_agent(task_type)
                task["assigned_agent"] = assigned_agent
            
            self.tasks[task_id] = task
            
            # 添加到队列（按优先级排序）
            self._insert_task_to_queue(task_id, priority)
            
            logger.info(f"任务 '{task_id}' 添加成功，分配给: {assigned_agent or assigned_team}")
            return task_id
            
        except Exception as e:
            logger.error(f"添加任务错误: {e}")
            raise

    async def _auto_assign_agent(self, task_type: TaskType) -> Optional[str]:
        """自动分配代理"""
        try:
            # 根据任务类型和代理能力匹配
            capability_map = {
                TaskType.RESEARCH: "research",
                TaskType.EMAIL: "email",
                TaskType.ANALYSIS: "analysis",
                TaskType.GENERAL: "general"
            }
            
            required_capability = capability_map.get(task_type, "general")
            
            # 查找具备相应能力的代理
            for agent_name, capabilities in self.agent_capabilities.items():
                if (required_capability in capabilities and 
                    self.agent_status[agent_name] == "active"):
                    return agent_name
            
            # 如果没有找到专门的代理，返回第一个可用的代理
            for agent_name, status in self.agent_status.items():
                if status == "active":
                    return agent_name
            
            return None
            
        except Exception as e:
            logger.error(f"自动分配代理错误: {e}")
            return None

    def _insert_task_to_queue(self, task_id: str, priority: TaskPriority):
        """按优先级插入任务到队列"""
        task_priority = priority.value
        
        # 找到插入位置
        insert_index = 0
        for i, existing_task_id in enumerate(self.task_queue):
            existing_priority = self.tasks[existing_task_id]["priority"]
            if task_priority > existing_priority:
                insert_index = i
                break
            insert_index = i + 1
        
        self.task_queue.insert(insert_index, task_id)

    async def execute_next_task(self) -> Optional[Dict[str, Any]]:
        """执行下一个任务"""
        try:
            if not self.task_queue:
                logger.info("任务队列为空")
                return None
            
            # 获取下一个任务
            task_id = self.task_queue.pop(0)
            task = self.tasks[task_id]
            
            logger.info(f"开始执行任务: {task_id}")
            
            # 更新任务状态
            task["status"] = TaskStatus.IN_PROGRESS.value
            task["updated_at"] = datetime.now().isoformat()
            
            # 执行任务
            result = await self._execute_task(task)
            
            # 更新任务结果
            if result["success"]:
                task["status"] = TaskStatus.COMPLETED.value
                task["result"] = result["data"]
                self.coordination_metrics["tasks_completed"] += 1
            else:
                task["status"] = TaskStatus.FAILED.value
                task["error"] = result["error"]
                self.coordination_metrics["tasks_failed"] += 1
            
            task["updated_at"] = datetime.now().isoformat()
            
            # 添加到历史
            self.task_history.append(task.copy())
            
            logger.info(f"任务 {task_id} 执行完成，状态: {task['status']}")
            return task
            
        except Exception as e:
            logger.error(f"执行任务错误: {e}")
            return None

    async def _execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """执行具体任务"""
        try:
            task_id = task["id"]
            description = task["description"]
            assigned_agent = task["assigned_agent"]
            assigned_team = task["assigned_team"]
            
            # 创建任务消息
            message = TextMessage(
                content=description,
                source="coordinator"
            )
            
            # 执行任务
            if assigned_team:
                # 团队执行
                team = self.teams[assigned_team]
                result = await team.run(task=description)
                
                return {
                    "success": True,
                    "data": {
                        "executor": assigned_team,
                        "type": "team",
                        "result": str(result)
                    }
                }
                
            elif assigned_agent:
                # 单个代理执行
                agent = self.agents[assigned_agent]
                
                if hasattr(agent, 'on_messages'):
                    result = await agent.on_messages([message], None)
                    
                    return {
                        "success": True,
                        "data": {
                            "executor": assigned_agent,
                            "type": "agent",
                            "result": result.content if hasattr(result, 'content') else str(result)
                        }
                    }
                else:
                    return {
                        "success": False,
                        "error": f"代理 {assigned_agent} 不支持消息处理"
                    }
            else:
                return {
                    "success": False,
                    "error": "没有分配执行者"
                }
                
        except Exception as e:
            logger.error(f"任务执行错误: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def execute_all_tasks(self) -> List[Dict[str, Any]]:
        """执行所有待处理任务"""
        results = []
        
        while self.task_queue:
            result = await self.execute_next_task()
            if result:
                results.append(result)
            
            # 避免无限循环
            await asyncio.sleep(0.1)
        
        return results

    async def coordinate_session(
        self,
        session_description: str,
        participants: List[str],
        max_rounds: int = 10
    ) -> Dict[str, Any]:
        """协调会话 - 多代理协作"""
        try:
            self.coordination_metrics["coordination_sessions"] += 1
            
            logger.info(f"开始协调会话: {session_description}")
            
            # 验证参与者
            session_agents = []
            for participant in participants:
                if participant in self.agents:
                    session_agents.append(self.agents[participant])
                elif participant in self.teams:
                    # 如果是团队，添加团队中的所有代理
                    team = self.teams[participant]
                    if hasattr(team, 'participants'):
                        session_agents.extend(team.participants)
                else:
                    logger.warning(f"参与者 '{participant}' 不存在")
            
            if not session_agents:
                return {
                    "success": False,
                    "error": "没有有效的参与者"
                }
            
            # 创建临时团队
            temp_team = RoundRobinGroupChat(session_agents)
            
            # 执行协调会话
            session_result = await temp_team.run(
                task=session_description,
                max_turns=max_rounds
            )
            
            # 记录会话结果
            session_record = {
                "description": session_description,
                "participants": participants,
                "result": str(session_result),
                "timestamp": datetime.now().isoformat(),
                "rounds": max_rounds
            }
            
            logger.info("协调会话完成")
            return {
                "success": True,
                "data": session_record
            }
            
        except Exception as e:
            logger.error(f"协调会话错误: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def get_agent_status(self) -> Dict[str, Any]:
        """获取代理状态"""
        return {
            "total_agents": len(self.agents),
            "active_agents": sum(1 for status in self.agent_status.values() if status == "active"),
            "agents": {
                name: {
                    "type": type(agent).__name__,
                    "capabilities": self.agent_capabilities.get(name, []),
                    "status": self.agent_status.get(name, "unknown")
                }
                for name, agent in self.agents.items()
            }
        }

    def get_team_status(self) -> Dict[str, Any]:
        """获取团队状态"""
        return {
            "total_teams": len(self.teams),
            "active_team": self.active_team,
            "teams": {
                name: {
                    "type": type(team).__name__,
                    "participants": len(team.participants) if hasattr(team, 'participants') else 0
                }
                for name, team in self.teams.items()
            }
        }

    def get_task_status(self) -> Dict[str, Any]:
        """获取任务状态"""
        status_counts = {}
        for task in self.tasks.values():
            status = task["status"]
            status_counts[status] = status_counts.get(status, 0) + 1
        
        return {
            "total_tasks": len(self.tasks),
            "queue_length": len(self.task_queue),
            "status_distribution": status_counts,
            "completed_tasks": self.coordination_metrics["tasks_completed"],
            "failed_tasks": self.coordination_metrics["tasks_failed"]
        }

    def get_coordination_metrics(self) -> Dict[str, Any]:
        """获取协调指标"""
        return {
            **self.coordination_metrics,
            "agent_status": self.get_agent_status(),
            "team_status": self.get_team_status(),
            "task_status": self.get_task_status()
        }

    async def shutdown(self):
        """关闭协调器"""
        try:
            logger.info("正在关闭团队协调器...")
            
            # 关闭所有代理的模型客户端
            for agent in self.agents.values():
                if hasattr(agent, 'model_client') and hasattr(agent.model_client, 'close'):
                    await agent.model_client.close()
            
            # 清理资源
            self.agents.clear()
            self.teams.clear()
            self.tasks.clear()
            self.task_queue.clear()
            
            logger.info("团队协调器已关闭")
            
        except Exception as e:
            logger.error(f"关闭协调器错误: {e}")


# 使用示例
if __name__ == "__main__":
    async def main():
        try:
            # 创建团队协调器
            coordinator = TeamCoordinator(name="AI团队协调器")
            
            # 创建代理
            research_agent = await coordinator.create_agent(
                "research", "研究专家",
                brave_api_key=os.getenv("BRAVE_API_KEY")
            )
            
            email_agent = await coordinator.create_agent(
                "email", "邮件助手"
            )
            
            assistant_agent = await coordinator.create_agent(
                "assistant", "通用助手"
            )
            
            # 创建团队
            team = await coordinator.create_team(
                "研究团队",
                ["研究专家", "邮件助手"],
                "round_robin"
            )
            
            # 添加任务
            await coordinator.add_task(
                "task_1",
                "研究人工智能在医疗领域的应用",
                TaskType.RESEARCH,
                TaskPriority.HIGH
            )
            
            await coordinator.add_task(
                "task_2", 
                "生成项目进度报告邮件",
                TaskType.EMAIL,
                TaskPriority.MEDIUM
            )
            
            # 执行任务
            results = await coordinator.execute_all_tasks()
            
            print("任务执行结果:")
            for result in results:
                print(f"- {result['id']}: {result['status']}")
            
            # 显示指标
            metrics = coordinator.get_coordination_metrics()
            print(f"\n协调指标: {json.dumps(metrics, indent=2, ensure_ascii=False)}")
            
            # 关闭协调器
            await coordinator.shutdown()
            
        except Exception as e:
            logger.error(f"示例运行错误: {e}")
    
    # 运行示例
    asyncio.run(main())

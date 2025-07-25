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
        self.model = model
        self.max_agents = max_agents
        
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
                        # 为非标准模型提供model_info
                        try:
                            from autogen_ext.models.openai import ModelInfo
                            client_kwargs["model_info"] = ModelInfo(
                                vision=True,
                                function_calling=True,
                                json_output=True
                            )
                        except ImportError:
                            # 如果无法导入ModelInfo，使用简单的字典
                            client_kwargs["model_info"] = {
                                "vision": True,
                                "function_calling": True,
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
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """添加新任务"""
        try:
            if task_id in self.tasks:
                raise ValueError(f"任务ID '{task_id}' 已存在")
            
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
                "error": None
            }
            
            # 自动分配代理（如果未指定）
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

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基础代理类 - AutoGen v0.4+ API版本
=====================================

基于AutoGen v0.4+的现代化多代理实现，
集成认知工具和协议Shell的增强型代理基类。
"""

import os
import asyncio
import logging
from typing import Dict, List, Any, Optional, Callable, Union
from abc import ABC, abstractmethod
import json
import time

# AutoGen v0.4+ imports
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.base import TaskRunner
from autogen_agentchat.messages import ChatMessage, TextMessage
from autogen_agentchat.teams import RoundRobinGroupChat, SelectorGroupChat
from autogen_agentchat.conditions import TextMentionTermination, MaxMessageTermination
from autogen_ext.models.openai import OpenAIChatCompletionClient

from dotenv import load_dotenv

# 导入认知增强模块
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cognitive_context.cognitive_analysis import CognitiveTools, CognitiveLevel
from cognitive_context.protocol_shells import (
    ProtocolShellManager, CommunicationProtocol, ErrorHandlingProtocol,
    FieldResonanceProtocol, ProtocolShellConfig, ProtocolType
)

# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(level=getattr(logging, os.getenv("LOG_LEVEL", "INFO")))
logger = logging.getLogger(__name__)


class EnhancedAssistantAgent(AssistantAgent):
    """增强型AutoGen v0.4助手代理"""
    
    def __init__(
        self,
        name: str,
        model_client: OpenAIChatCompletionClient,
        agent_type: str = "assistant",
        cognitive_level: CognitiveLevel = CognitiveLevel.DEEP,
        enable_protocol_shells: bool = True,
        system_message: Optional[str] = None,
        **kwargs
    ):
        """
        初始化增强型助手代理。
        
        Args:
            name (str): 代理名称
            model_client: OpenAI模型客户端
            agent_type (str): 代理类型
            cognitive_level: 认知水平
            enable_protocol_shells (bool): 启用协议Shell
            system_message (str): 系统消息
        """
        # 构建系统消息
        if system_message is None:
            system_message = self._build_system_message(agent_type, cognitive_level)
        
        # 初始化父类
        super().__init__(
            name=name,
            model_client=model_client,
            system_message=system_message,
            **kwargs
        )
        
        # 增强功能
        self.model_client = model_client  # 保存模型客户端引用
        self.agent_type = agent_type
        self.cognitive_level = cognitive_level
        self.enable_protocol_shells = enable_protocol_shells
        
        # 初始化认知工具
        self.cognitive_tools = CognitiveTools()
        
        # 初始化协议Shell管理器
        if enable_protocol_shells:
            self.protocol_manager = ProtocolShellManager()
            # 注意: initialize_protocols 是异步方法，在 on_messages 中调用
            self._protocols_initialized = False
        else:
            self.protocol_manager = None
            self._protocols_initialized = True
        
        # 代理状态
        self.conversation_history = []
        self.cognitive_state = {}
        self.performance_metrics = {
            "messages_processed": 0,
            "cognitive_analyses": 0,
            "protocol_activations": 0
        }
        
        logger.info(f"增强型助手代理 '{name}' 初始化完成 (v0.4 API)")

    def _build_system_message(self, agent_type: str, cognitive_level: CognitiveLevel) -> str:
        """构建系统消息"""
        base_message = f"""你是一个{agent_type}代理，具备以下增强能力：

1. **认知增强**: 使用{cognitive_level.value}级认知分析
2. **协议Shell**: 支持字段共振和自修复机制
3. **Context Engineering**: 基于最新研究的认知工具

请在回应中展现深度思考和结构化推理能力。"""
        
        return base_message

    async def on_messages(self, messages: List[ChatMessage], cancellation_token) -> ChatMessage:
        """处理消息的增强版本"""
        try:
            # 更新性能指标
            self.performance_metrics["messages_processed"] += 1
            
            # 认知分析
            if len(messages) > 0:
                last_message = messages[-1]
                cognitive_analysis = await self._perform_cognitive_analysis(last_message)
                self.performance_metrics["cognitive_analyses"] += 1
            
            # 协议Shell处理
            if self.enable_protocol_shells and self.protocol_manager:
                # 确保协议已初始化
                if not self._protocols_initialized:
                    await self.protocol_manager.initialize_protocols()
                    self._protocols_initialized = True
                
                # 应用协议Shell处理
                processed_messages = await self._apply_protocol_shells(messages)
                self.performance_metrics["protocol_activations"] += 1
            else:
                processed_messages = messages
            
            # 模型推理 - 直接使用 Gemini API 如果是 Gemini 模型
            if (hasattr(self, 'model_client') and 
                hasattr(self.model_client, 'model') and 
                'gemini' in str(self.model_client.model).lower()):
                response = await self._direct_gemini_call(processed_messages)
            else:
                response = await super().on_messages(processed_messages, cancellation_token)
            
            # 记录对话历史
            self.conversation_history.extend(messages)
            self.conversation_history.append(response)
            
            return response
            
        except Exception as e:
            logger.error(f"消息处理错误: {e}")
            # 返回错误处理消息
            return TextMessage(
                content=f"抱歉，处理消息时遇到错误: {str(e)}",
                source=self.name
            )
    
    async def _direct_gemini_call(self, messages: List[ChatMessage]) -> ChatMessage:
        """直接调用 Gemini API，绕过 AutoGen 客户端接口问题"""
        try:
            import aiohttp
            import os
            
            # 提取消息内容
            prompt_parts = []
            for msg in messages:
                if hasattr(msg, 'content'):
                    prompt_parts.append(str(msg.content))
                else:
                    prompt_parts.append(str(msg))
            
            prompt = "\n\n".join(prompt_parts)
            
            # 从环境变量读取配置，确保安全性
            api_key = os.getenv('OPENAI_API_KEY')
            base_url = os.getenv('OPENAI_BASE_URL')
            model = os.getenv('OPENAI_MODEL', 'gemini-2.5-flash')
            
            # 验证必需的环境变量
            if not api_key or not base_url:
                raise ValueError("缺少必需的环境变量: OPENAI_API_KEY 和 OPENAI_BASE_URL")
            
            api_url = f"{base_url}/v1beta/models/{model}:generateContent"
            headers = {
                "Content-Type": "application/json",
                "x-goog-api-key": api_key
            }
            
            payload = {
                "contents": [{
                    "role": "user",
                    "parts": [{
                        "text": prompt
                    }]
                }],
                "generationConfig": {
                    "temperature": 0.7,
                    "maxOutputTokens": 1000,
                    "topP": 0.8,
                    "topK": 10
                }
            }
            
            # 使用简化的、验证过的 API 调用方式
            try:
                async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
                    logger.info(f"直接调用 Gemini API: {api_url}")
                    async with session.post(api_url, json=payload, headers=headers) as response:
                        status = response.status
                        response_text = await response.text()
                        
                        logger.info(f"API 响应状态: {status}, 响应长度: {len(response_text)}")
                        
                        if status == 200:
                            try:
                                result = await response.json()
                                if 'candidates' in result and len(result['candidates']) > 0:
                                    content = result['candidates'][0]['content']['parts'][0]['text']
                                    logger.info("直接 Gemini 调用成功")
                                    return TextMessage(
                                        content=content,
                                        source=self.name
                                    )
                                else:
                                    logger.error(f"Gemini 响应格式异常: {result}")
                                    return TextMessage(
                                        content="无法解析 AI 响应结果",
                                        source=self.name
                                    )
                            except Exception as parse_error:
                                logger.error(f"解析响应错误: {parse_error}")
                                logger.error(f"原始响应: {response_text[:500]}")
                                return TextMessage(
                                    content=f"响应解析错误: {parse_error}",
                                    source=self.name
                                )
                        else:
                            logger.error(f"直接 Gemini API 调用失败: {status}")
                            logger.error(f"错误响应: {response_text}")
                            return TextMessage(
                                content=f"无法获取 AI 分析结果 (状态码: {status})",
                                source=self.name
                            )
            except Exception as session_error:
                logger.error(f"会话错误: {session_error}")
                return TextMessage(
                    content=f"网络连接错误: {session_error}",
                    source=self.name
                )
                        
        except Exception as e:
            logger.error(f"直接 Gemini 调用错误: {e}")
            return TextMessage(
                content=f"分析错误: {str(e)}",
                source=self.name
            )

    async def _perform_cognitive_analysis(self, message: ChatMessage) -> Dict[str, Any]:
        """执行认知分析"""
        try:
            if hasattr(message, 'content') and message.content:
                analysis = self.cognitive_tools.analyze_text(
                    message.content,
                    level=self.cognitive_level
                )
                
                # 更新认知状态
                self.cognitive_state.update({
                    "last_analysis": analysis,
                    "timestamp": time.time()
                })
                
                return analysis
            
        except Exception as e:
            logger.error(f"认知分析错误: {e}")
            return {}

    async def _apply_protocol_shells(self, messages: List[ChatMessage]) -> List[ChatMessage]:
        """应用协议Shell处理"""
        try:
            if not self.protocol_manager:
                return messages
            
            processed_messages = []
            
            for message in messages:
                # 应用通信协议
                comm_result = await self.protocol_manager.apply_protocol(
                    ProtocolType.COMMUNICATION,
                    {"message": message.content if hasattr(message, 'content') else str(message)}
                )
                
                # 创建处理后的消息
                if comm_result.get("success", False):
                    enhanced_content = comm_result.get("enhanced_message", message.content)
                    if hasattr(message, 'content'):
                        message.content = enhanced_content
                
                processed_messages.append(message)
            
            return processed_messages
            
        except Exception as e:
            logger.error(f"协议Shell处理错误: {e}")
            return messages

    def get_performance_metrics(self) -> Dict[str, Any]:
        """获取性能指标"""
        return {
            **self.performance_metrics,
            "cognitive_level": self.cognitive_level.value,
            "protocol_shells_enabled": self.enable_protocol_shells,
            "conversation_length": len(self.conversation_history)
        }

    async def reset_state(self):
        """重置代理状态"""
        self.conversation_history.clear()
        self.cognitive_state.clear()
        self.performance_metrics = {
            "messages_processed": 0,
            "cognitive_analyses": 0,
            "protocol_activations": 0
        }
        logger.info(f"代理 '{self.name}' 状态已重置")


class EnhancedGroupChatTeam:
    """增强的群聊团队管理器 (v0.4)"""
    
    def __init__(
        self,
        agents: List[EnhancedAssistantAgent],
        model_client: OpenAIChatCompletionClient,
        team_type: str = "round_robin",
        max_turns: int = 10,
        enable_cognitive_coordination: bool = True
    ):
        """
        初始化增强的群聊团队。
        
        Args:
            agents: 代理列表
            model_client: 模型客户端
            team_type: 团队类型 ("round_robin" 或 "selector")
            max_turns: 最大轮次
            enable_cognitive_coordination: 启用认知协调
        """
        self.agents = agents
        self.model_client = model_client
        self.team_type = team_type
        self.max_turns = max_turns
        self.enable_cognitive_coordination = enable_cognitive_coordination
        
        # 创建终止条件
        self.termination_condition = MaxMessageTermination(max_turns)
        
        # 创建团队
        if team_type == "round_robin":
            self.team = RoundRobinGroupChat(
                participants=agents,
                termination_condition=self.termination_condition
            )
        elif team_type == "selector":
            # 使用第一个代理作为选择器
            self.team = SelectorGroupChat(
                participants=agents,
                model_client=model_client,
                termination_condition=self.termination_condition
            )
        else:
            raise ValueError(f"不支持的团队类型: {team_type}")
        
        logger.info(f"增强群聊团队初始化完成 ({team_type}, {len(agents)}个代理)")

    async def run_task(self, task: str) -> Any:
        """运行任务"""
        try:
            logger.info(f"开始执行任务: {task}")
            
            # 如果启用认知协调，先进行团队分析
            if self.enable_cognitive_coordination:
                await self._perform_team_coordination(task)
            
            # 运行团队任务
            result = await self.team.run(task=task)
            
            logger.info("任务执行完成")
            return result
            
        except Exception as e:
            logger.error(f"任务执行错误: {e}")
            raise

    async def _perform_team_coordination(self, task: str):
        """执行团队认知协调"""
        try:
            logger.info("执行团队认知协调...")
            
            # 分析任务复杂度
            for agent in self.agents:
                if hasattr(agent, 'cognitive_tools'):
                    analysis = agent.cognitive_tools.analyze_text(task)
                    logger.debug(f"代理 {agent.name} 任务分析: {analysis}")
            
        except Exception as e:
            logger.error(f"团队协调错误: {e}")

    def get_team_metrics(self) -> Dict[str, Any]:
        """获取团队指标"""
        metrics = {
            "team_type": self.team_type,
            "agent_count": len(self.agents),
            "max_turns": self.max_turns,
            "cognitive_coordination": self.enable_cognitive_coordination,
            "agents": []
        }
        
        for agent in self.agents:
            if hasattr(agent, 'get_performance_metrics'):
                metrics["agents"].append({
                    "name": agent.name,
                    "metrics": agent.get_performance_metrics()
                })
        
        return metrics


# 工厂函数
async def create_enhanced_agent(
    name: str,
    agent_type: str,
    api_key: str,
    model: str = "gpt-4o",
    cognitive_level: CognitiveLevel = CognitiveLevel.DEEP,
    **kwargs
) -> EnhancedAssistantAgent:
    """创建增强型代理的工厂函数"""
    
    # 创建模型客户端
    model_client = OpenAIChatCompletionClient(
        model=model,
        api_key=api_key
    )
    
    # 创建代理
    agent = EnhancedAssistantAgent(
        name=name,
        model_client=model_client,
        agent_type=agent_type,
        cognitive_level=cognitive_level,
        **kwargs
    )
    
    return agent


# 使用示例
if __name__ == "__main__":
    async def main():
        # 示例：创建增强型代理
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.error("请设置OPENAI_API_KEY环境变量")
            return
        
        try:
            # 创建代理
            research_agent = await create_enhanced_agent(
                name="研究代理",
                agent_type="research",
                api_key=api_key
            )
            
            email_agent = await create_enhanced_agent(
                name="邮件代理", 
                agent_type="email",
                api_key=api_key
            )
            
            # 创建团队
            model_client = OpenAIChatCompletionClient(model="gpt-4o", api_key=api_key)
            team = EnhancedGroupChatTeam(
                agents=[research_agent, email_agent],
                model_client=model_client
            )
            
            # 运行任务
            result = await team.run_task("研究人工智能的最新发展并准备邮件报告")
            print(f"任务结果: {result}")
            
            # 关闭客户端
            await model_client.close()
            
        except Exception as e:
            logger.error(f"示例运行错误: {e}")
    
    # 运行示例
    asyncio.run(main())

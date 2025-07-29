#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强型代理基类 v0.4
支持 AutoGen v0.4+ API
集成认知增强、协议Shell和Context Engineering
"""

import os
import time
import asyncio
import logging
from typing import List, Dict, Any, Optional, Union
from enum import Enum
from dataclasses import dataclass
from datetime import datetime

# 注意：由于AutoGen框架与Gemini Balance API存在深层兼容性问题，
# 本系统已完全绕过AutoGen标准流程，直接使用稳定的Gemini API调用

# AutoGen v0.4+ imports
from autogen_agentchat.agents import AssistantAgent
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
        
        # 搜索功能配置（用于简单实时信息查询）
        self.brave_api_key = os.getenv("BRAVE_API_KEY")
        self.search_engine_url = os.getenv("SEARCH_ENGINE_BASE_URL")
        self.enable_simple_search = bool(self.brave_api_key or self.search_engine_url)
        
        # 代理状态
        self.conversation_history = []
        self.cognitive_state = {}
        self.performance_metrics = {
            "messages_processed": 0,
            "cognitive_analyses": 0,
            "protocol_activations": 0,
            "simple_searches": 0
        }
        
        logger.info(f"增强型助手代理 '{name}' 初始化完成 (v0.4 API)")
        if self.enable_simple_search:
            logger.info(f"简单搜索功能已启用 ({'Brave' if self.brave_api_key else 'SearXNG'})")
    
    def _needs_real_time_info(self, query: str) -> bool:
        """判断查询是否需要实时信息"""
        # 扩展实时信息关键词，包括更多类型的实时查询
        realtime_keywords = [
            # 时间相关
            "今天", "现在", "当前", "最新", "实时", "日期", "时间",
            "today", "now", "current", "latest", "real-time", "date", "time",
            # 新闻与事件
            "新闻", "事件", "发生", "最近", "刚刚", "刚才",
            "news", "event", "happened", "recent", "just", "breaking",
            # 市场与经济
            "股价", "汇率", "价格", "市场", "行情",
            "stock", "price", "market", "exchange", "rate",
            # 天气与环境
            "天气", "温度", "气温", "降雨", "风速",
            "weather", "temperature", "rain", "wind", "forecast",
            # 体育与赛事
            "比赛", "赛事", "比分", "结果", "排名",
            "match", "game", "score", "result", "ranking",
            # 交通与出行
            "交通", "堵车", "航班", "列车", "公交",
            "traffic", "flight", "train", "bus", "delay"
        ]
        query_lower = query.lower()
        return any(keyword in query_lower for keyword in realtime_keywords)
    
    async def _simple_search(self, query: str) -> str:
        """执行简单搜索，获取实时信息"""
        # 优先使用配置的搜索引擎获取实时信息
        if self.enable_simple_search:
            try:
                import aiohttp
                
                if self.search_engine_url:  # 使用 SearXNG
                    result = await self._search_with_searxng(query)
                    if result:
                        return result
                elif self.brave_api_key:  # 使用 Brave Search
                    result = await self._search_with_brave(query)
                    if result:
                        return result
                        
            except Exception as e:
                logger.error(f"搜索引擎查询失败: {e}")
        
        # 如果搜索引擎不可用或失败，尝试简单的HTTP搜索作为备用
        try:
            result = await self._fallback_http_search(query)
            if result:
                return result
        except Exception as e:
            logger.error(f"备用HTTP搜索失败: {e}")
        
        # 对于日期时间查询提供本地备用
        if self._is_datetime_query(query):
            return self._get_local_datetime_info(query)
            
        # 其他实时信息查询无法处理
        return None
    
    def _is_datetime_query(self, query: str) -> bool:
        """判断是否为日期时间查询"""
        datetime_keywords = [
            "日期", "今天", "时间", "现在", "当前时间",
            "date", "today", "time", "now", "current time"
        ]
        query_lower = query.lower()
        return any(keyword in query_lower for keyword in datetime_keywords)
    
    def _get_local_datetime_info(self, query: str) -> str:
        """获取本地日期时间信息（仅作为备用）"""
        try:
            from datetime import datetime
            
            now = datetime.now()
            query_lower = query.lower()
            
            if any(keyword in query_lower for keyword in ["日期", "date", "今天"]):
                return f"今天的日期是: {now.strftime('%Y年%m月%d日')} (星期{['', '一', '二', '三', '四', '五', '六', '日'][now.weekday() + 1]})"
            elif any(keyword in query_lower for keyword in ["时间", "time", "现在"]):
                return f"现在的时间是: {now.strftime('%Y年%m月%d日 %H:%M:%S')}"
            else:
                return f"当前日期时间: {now.strftime('%Y年%m月%d日 %H:%M:%S')} (星期{['', '一', '二', '三', '四', '五', '六', '日'][now.weekday() + 1]})"
                
        except Exception as e:
            logger.error(f"获取本地日期时间失败: {e}")
            return None
    
    async def _search_with_searxng(self, query: str) -> str:
        """使用 SearXNG 搜索"""
        try:
            import aiohttp
            
            async with aiohttp.ClientSession() as session:
                params = {
                    'q': query,
                    'format': 'json',
                    'engines': 'google,bing',
                    'safesearch': '1'
                }
                
                # 直接使用配置的 URL，不再添加 /search
                async with session.get(self.search_engine_url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        results = data.get('results', [])
                        
                        if results:
                            # 提取前3个结果的标题和内容
                            search_info = []
                            for result in results[:3]:
                                title = result.get('title', '')
                                content = result.get('content', '')
                                if title or content:
                                    search_info.append(f"{title}: {content}")
                            
                            self.performance_metrics["simple_searches"] += 1
                            return "\n".join(search_info)
                            
        except Exception as e:
            logger.error(f"SearXNG 搜索错误: {e}")
            return None
    
    async def _search_with_brave(self, query: str) -> str:
        """使用 Brave Search 搜索"""
        try:
            import aiohttp
            
            headers = {
                "Accept": "application/json",
                "Accept-Encoding": "gzip",
                "X-Subscription-Token": self.brave_api_key
            }
            
            params = {
                "q": query,
                "count": 3,
                "offset": 0,
                "mkt": "zh-CN"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    "https://api.search.brave.com/res/v1/web/search",
                    headers=headers,
                    params=params
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        results = data.get('web', {}).get('results', [])
                        
                        if results:
                            # 提取前3个结果的标题和描述
                            search_info = []
                            for result in results[:3]:
                                title = result.get('title', '')
                                description = result.get('description', '')
                                if title or description:
                                    search_info.append(f"{title}: {description}")
                            
                            self.performance_metrics["simple_searches"] += 1
                            return "\n".join(search_info)
                            
        except Exception as e:
            logger.error(f"Brave Search 搜索错误: {e}")
            return None
    
    async def _fallback_http_search(self, query: str) -> str:
        """备用HTTP搜索功能，使用免费的搜索API"""
        try:
            import aiohttp
            import urllib.parse
            
            # 使用DuckDuckGo Instant Answer API作为备用
            encoded_query = urllib.parse.quote(query)
            url = f"https://api.duckduckgo.com/?q={encoded_query}&format=json&no_html=1&skip_disambig=1"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # 尝试获取即时答案
                        instant_answer = data.get('AbstractText', '')
                        if instant_answer:
                            self.performance_metrics["simple_searches"] += 1
                            return f"搜索结果: {instant_answer}"
                        
                        # 尝试获取相关主题
                        related_topics = data.get('RelatedTopics', [])
                        if related_topics:
                            results = []
                            for topic in related_topics[:3]:
                                if isinstance(topic, dict) and 'Text' in topic:
                                    results.append(topic['Text'])
                            
                            if results:
                                self.performance_metrics["simple_searches"] += 1
                                return "搜索结果:\n" + "\n".join(results)
                        
                        # 尝试获取答案
                        answer = data.get('Answer', '')
                        if answer:
                            self.performance_metrics["simple_searches"] += 1
                            return f"搜索结果: {answer}"
                            
        except Exception as e:
            logger.error(f"备用HTTP搜索错误: {e}")
            
        return None

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
            
            # 获取最新消息内容
            last_message = messages[-1]
            query = last_message.content if hasattr(last_message, 'content') else str(last_message)
            
            # 检查是否需要实时信息搜索（仅限通用助手）
            if (self.agent_type == "assistant" and 
                self.enable_simple_search and 
                self._needs_real_time_info(query)):
                
                logger.info(f"通用助手检测到实时信息查询，执行简单搜索: {query}")
                search_result = await self._simple_search(query)
                
                if search_result:
                    # 将搜索结果添加到查询中
                    enhanced_query = f"用户问题: {query}\n\n最新搜索信息:\n{search_result}\n\n请基于以上搜索信息简洁直接地回答用户问题。不要生成研究报告格式。"
                    # 创建增强的消息
                    enhanced_message = TextMessage(content=enhanced_query, source="system")
                    messages = messages[:-1] + [enhanced_message]
                    logger.info("已将搜索结果集成到查询中")
            
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
            
            # 模型推理 - 直接使用稳定的Gemini API调用，绕过AutoGen兼容性问题
            # 由于AutoGen框架与Gemini Balance API存在深层兼容性问题，
            # 直接使用经过验证的直接API调用方式确保稳定性
            try:
                # 直接使用经过验证的Gemini API调用
                response = await self._direct_gemini_call(processed_messages)
                logger.info("✅ 使用稳定的直接Gemini API调用")
                
            except Exception as direct_error:
                logger.error(f"直接Gemini API调用失败: {direct_error}")
                # 返回错误消息
                response = TextMessage(
                    content=f"抱歉，处理您的请求时出现错误: {str(direct_error)}",
                    source=self.name
                )
            
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
    
    def _validate_messages_for_autogen(self, messages: List[ChatMessage]) -> List[ChatMessage]:
        """
        验证并修复消息格式，确保符合AutoGen框架期望
        解决"No model result was produced"警告的根本原因
        """
        validated_messages = []
        
        for msg in messages:
            try:
                # 确保消息有正确的content属性
                if hasattr(msg, 'content'):
                    content = msg.content
                else:
                    content = str(msg)
                
                # 确保content不为空且为字符串
                if not content or not isinstance(content, str):
                    content = str(content) if content else "空消息"
                
                # 创建符合AutoGen期望的TextMessage
                validated_msg = TextMessage(
                    content=content,
                    source=getattr(msg, 'source', 'user')
                )
                
                validated_messages.append(validated_msg)
                
            except Exception as e:
                logger.warning(f"消息验证失败，使用默认格式: {e}")
                # 创建默认消息
                default_msg = TextMessage(
                    content=str(msg),
                    source='user'
                )
                validated_messages.append(default_msg)
        
        logger.info(f"消息验证完成，处理了{len(validated_messages)}条消息")
        return validated_messages
    
    async def _direct_gemini_call(self, messages: List[ChatMessage]) -> ChatMessage:
        """直接调用 Gemini API，使用 OpenAI 兼容格式和缓存的环境变量"""
        try:
            import aiohttp
            import sys
            import os
            
            # 添加 utils 目录到路径
            utils_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'utils')
            if utils_path not in sys.path:
                sys.path.append(utils_path)
            
            # 使用缓存的环境变量管理器
            try:
                from env_cache_manager import get_cached_api_config, validate_cached_config
                
                # 验证缓存的配置
                if not validate_cached_config():
                    raise ValueError("缓存的环境变量配置无效")
                
                # 获取缓存的API配置
                config = get_cached_api_config()
                api_key = config['api_key']
                base_url = config['base_url']
                model = config['model']
                
                logger.info(f"使用缓存的环境变量: API Key长度={len(api_key)}, Base URL={base_url}")
                
            except ImportError:
                # 回退到直接读取环境变量
                logger.warning("无法导入环境变量缓存管理器，回退到直接读取")
                api_key = os.getenv('OPENAI_API_KEY')
                base_url = os.getenv('OPENAI_BASE_URL')
                model = os.getenv('OPENAI_MODEL', 'gemini-2.5-flash')
                
                # 验证必需的环境变量
                if not api_key or not base_url:
                    raise ValueError("缺少必需的环境变量: OPENAI_API_KEY 和 OPENAI_BASE_URL")
            
            # 提取消息内容
            prompt_parts = []
            for msg in messages:
                if hasattr(msg, 'content'):
                    prompt_parts.append(str(msg.content))
                else:
                    prompt_parts.append(str(msg))
            
            prompt = "\n\n".join(prompt_parts)
            
            # 使用 OpenAI 兼容格式
            api_url = f"{base_url}/v1/chat/completions"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            }
            
            payload = {
                "model": model,
                "messages": [{
                    "role": "user",
                    "content": prompt
                }],
                "temperature": 0.7,
                "max_tokens": 1000,
                "top_p": 0.8
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
                                # 处理 OpenAI 兼容格式的响应
                                if 'choices' in result and len(result['choices']) > 0:
                                    content = result['choices'][0]['message']['content']
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
    base_url: Optional[str] = None,
    model: str = "gpt-4o",
    cognitive_level: CognitiveLevel = CognitiveLevel.DEEP,
    **kwargs
) -> EnhancedAssistantAgent:
    """创建增强型代理的工厂函数"""
    
    # 创建模型客户端
    client_kwargs = {
        "model": model,
        "api_key": api_key
    }
    
    # 添加 base_url 如果提供了
    if base_url:
        client_kwargs["base_url"] = base_url
    
    # 为非标准模型（如 Gemini）添加 model_info
    if "gemini" in model.lower() or "gpt" not in model.lower():
        try:
            from autogen_ext.models.openai import ModelInfo
            client_kwargs["model_info"] = ModelInfo(
                family="gemini",  # AutoGen v0.4.7+ 必需字段
                vision=False,
                function_calling=False,
                json_output=True
            )
        except ImportError:
            client_kwargs["model_info"] = {
                "family": "gemini",
                "vision": False,
                "function_calling": False,
                "json_output": True
            }
    
    model_client = OpenAIChatCompletionClient(**client_kwargs)
    
    # 创建代理
    agent = EnhancedAssistantAgent(
        name=name,
        model_client=model_client,
        agent_type=agent_type,
        cognitive_level=cognitive_level,
        **kwargs
    )
    
    return agent


async def create_enhanced_assistant_agent(
    name: str,
    system_message: str = "你是一个智能助手代理",
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    model: str = "gemini-2.5-flash",
    **kwargs
) -> EnhancedAssistantAgent:
    """
    创建增强型助手代理的便捷工厂函数
    
    Args:
        name: 代理名称
        system_message: 系统消息
        api_key: API密钥
        base_url: API基础URL
        model: 模型名称
        **kwargs: 其他参数
    
    Returns:
        EnhancedAssistantAgent: 创建的代理实例
    """
    return await create_enhanced_agent(
        name=name,
        agent_type="assistant",
        system_message=system_message,
        api_key=api_key,
        base_url=base_url,
        model=model,
        **kwargs
    )


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

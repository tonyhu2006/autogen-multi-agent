#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gemini Balance 代理客户端
========================

用于通过 gemini balance 代理调用 gemini-2.5-flash 模型的客户端
"""
# 导入必要的库
import os
import asyncio
import aiohttp
import json
import logging
from typing import Dict, Any, List, Optional, Union, AsyncGenerator
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_agentchat.messages import ChatMessage, TextMessage

# 配置日志
logger = logging.getLogger(__name__)


class GeminiClient:
    """Gemini Balance 代理客户端"""
    
    def __init__(
        self,
        api_key: str,
        base_url: str,
        model: str = "gemini-2.5-flash",
        timeout: int = 30
    ):
        """
        初始化 Gemini 客户端
        
        Args:
            api_key: API 密钥
            base_url: 代理服务器基础URL
            model: 模型名称
            timeout: 请求超时时间
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.model = model
        self.timeout = timeout
        self.session = None
        
        logger.info(f"初始化 Gemini 客户端: {base_url}, 模型: {model}")
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.timeout)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        if self.session:
            await self.session.close()
    
    async def close(self):
        """关闭客户端"""
        if self.session:
            await self.session.close()
    
    async def generate_content(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_output_tokens: int = 1000,
        top_p: float = 0.8,
        top_k: int = 10
    ) -> str:
        """
        生成内容
        
        Args:
            prompt: 输入提示
            temperature: 温度参数
            max_output_tokens: 最大输出token数
            top_p: top_p参数
            top_k: top_k参数
            
        Returns:
            生成的内容
        """
        try:
            if not self.session:
                self.session = aiohttp.ClientSession(
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                )
            
            # 构建 OpenAI 兼容 API URL
            api_url = f"{self.base_url}/v1/chat/completions"
            
            # 构建请求头（OpenAI 兼容格式）
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            
            # 构建请求体（OpenAI 兼容格式）
            payload = {
                "model": self.model,
                "messages": [{
                    "role": "user",
                    "content": prompt
                }],
                "temperature": temperature,
                "max_tokens": max_output_tokens,
                "top_p": top_p
            }
            
            logger.info(f"调用 Gemini API: {api_url}")
            
            async with self.session.post(api_url, json=payload, headers=headers) as response:
                if response.status == 200:
                    result = await response.json()
                    
                    # OpenAI 兼容格式的响应解析
                    if 'choices' in result and len(result['choices']) > 0:
                        content = result['choices'][0]['message']['content']
                        logger.info("AI分析成功")
                        return content
                    else:
                        logger.error(f"Gemini响应格式异常: {result}")
                        return "无法解析AI响应结果"
                else:
                    response_text = await response.text()
                    logger.error(f"Gemini API调用失败: {response.status}, 响应: {response_text}")
                    return f"无法获取AI分析结果 (状态码: {response.status})"
                    
        except Exception as e:
            logger.error(f"Gemini API 调用错误: {e}")
            return f"分析错误: {str(e)}"
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> str:
        """
        聊天完成（兼容 OpenAI 格式的接口）
        
        Args:
            messages: 消息列表，格式为 [{"role": "user", "content": "..."}]
            temperature: 温度参数
            max_tokens: 最大token数
            
        Returns:
            AI 回复内容
        """
        try:
            # 将 OpenAI 格式的消息转换为单个提示
            prompt_parts = []
            for message in messages:
                role = message.get("role", "user")
                content = message.get("content", "")
                
                if role == "system":
                    prompt_parts.append(f"系统指令: {content}")
                elif role == "user":
                    prompt_parts.append(f"用户: {content}")
                elif role == "assistant":
                    prompt_parts.append(f"助手: {content}")
            
            prompt = "\n\n".join(prompt_parts)
            
            # 调用 generate_content
            return await self.generate_content(
                prompt=prompt,
                temperature=temperature,
                max_output_tokens=max_tokens
            )
            
        except Exception as e:
            logger.error(f"聊天完成错误: {e}")
            return f"聊天完成失败: {str(e)}"


class GeminiModelClient:
    """
    兼容 AutoGen v0.4+ 的 Gemini 模型客户端
    模拟 OpenAIChatCompletionClient 的接口
    """
    
    def __init__(
        self,
        model: str,
        api_key: str,
        base_url: str,
        **kwargs
    ):
        """
        初始化 Gemini 模型客户端
        
        Args:
            model: 模型名称
            api_key: API 密钥
            base_url: 基础URL
        """
        self.model = model
        self.api_key = api_key
        self.base_url = base_url
        self.gemini_client = None
        
        # 添加 model_info 属性以兼容 AutoGen
        self.model_info = {
            "vision": True,
            "function_calling": True,
            "json_output": True
        }
        
        logger.info(f"初始化 Gemini 模型客户端: {model}")
    
    async def create(
        self,
        messages: List[Dict[str, Any]],
        **kwargs
    ) -> Dict[str, Any]:
        """
        创建聊天完成（兼容 AutoGen 接口）
        
        Args:
            messages: 消息列表
            
        Returns:
            响应字典
        """
        try:
            if not self.gemini_client:
                self.gemini_client = GeminiClient(
                    api_key=self.api_key,
                    base_url=self.base_url,
                    model=self.model
                )
                # 不需要手动调用 __aenter__，直接使用
            
            # 简化消息处理 - 直接提取内容
            prompt_parts = []
            for msg in messages:
                if hasattr(msg, 'content'):
                    # AutoGen v0.4+ 消息对象
                    prompt_parts.append(str(msg.content))
                elif isinstance(msg, dict) and 'content' in msg:
                    # 字典格式消息
                    prompt_parts.append(str(msg['content']))
                else:
                    # 字符串消息
                    prompt_parts.append(str(msg))
            
            # 合并为单个提示
            prompt = "\n\n".join(prompt_parts)
            
            # 直接调用 generate_content
            response_content = await self.gemini_client.generate_content(
                prompt=prompt,
                temperature=kwargs.get('temperature', 0.7),
                max_output_tokens=kwargs.get('max_tokens', 1000)
            )
            
            # 返回 AutoGen v0.4+ 兼容的 TextMessage 格式
            return TextMessage(
                content=response_content,
                source="assistant"
            )
            
        except Exception as e:
            logger.error(f"Gemini 模型客户端错误: {e}")
            raise
    
    async def close(self):
        """关闭客户端"""
        if self.gemini_client:
            await self.gemini_client.close()


# 工厂函数
def create_gemini_client(
    model: str = None,
    api_key: str = None,
    base_url: str = None,
    **kwargs
) -> GeminiModelClient:
    """
    创建 Gemini 模型客户端的工厂函数
    
    Args:
        model: 模型名称
        api_key: API 密钥
        base_url: 基础URL
        
    Returns:
        GeminiModelClient 实例
    """
    model = model or os.getenv("OPENAI_MODEL", "gemini-2.5-flash")
    api_key = api_key or os.getenv("OPENAI_API_KEY")
    base_url = base_url or os.getenv("OPENAI_BASE_URL")
    
    if not api_key:
        raise ValueError("需要提供 API 密钥")
    
    if not base_url:
        raise ValueError("需要提供基础 URL")
    
    return GeminiModelClient(
        model=model,
        api_key=api_key,
        base_url=base_url,
        **kwargs
    )


# 使用示例
if __name__ == "__main__":
    async def test_gemini_client():
        try:
            # 从环境变量加载配置
            from dotenv import load_dotenv
            load_dotenv('.env.local')
            
            client = create_gemini_client()
            
            # 测试消息
            messages = [
                {"role": "user", "content": "你好，请简单介绍一下自己"}
            ]
            
            response = await client.create(messages)
            print(f"Gemini 响应: {response['choices'][0]['message']['content']}")
            
            await client.close()
            
        except Exception as e:
            logger.error(f"测试失败: {e}")
    
    # 运行测试
    asyncio.run(test_gemini_client())

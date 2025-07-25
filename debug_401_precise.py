#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
精确定位401错误的调试脚本
对比独立测试成功 vs 主系统运行时失败的差异
"""

import os
import sys
import asyncio
import logging
import aiohttp
import json
from dotenv import load_dotenv

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 模拟主系统的环境变量加载
load_dotenv('.env.local')
load_dotenv('.env')

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger(__name__)

async def test_independent_api_call():
    """独立API调用测试（已知成功）"""
    print("🚀 测试 1: 独立API调用（已知成功）")
    
    api_key = os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("OPENAI_BASE_URL")
    model = os.getenv("OPENAI_MODEL", "gemini-2.5-flash")
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": "你好"}]
    }
    
    print(f"📍 URL: {base_url}/v1/chat/completions")
    print(f"📋 API Key (前10字符): {api_key[:10]}...")
    print(f"📦 Model: {model}")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{base_url}/v1/chat/completions",
                headers=headers,
                json=payload
            ) as response:
                print(f"📊 响应状态: {response.status}")
                
                if response.status == 200:
                    print("✅ 独立API调用成功！")
                    return True
                else:
                    response_text = await response.text()
                    print(f"❌ 独立API调用失败: {response.status}")
                    print(f"📝 错误响应: {response_text}")
                    return False
                    
    except Exception as e:
        print(f"❌ 独立API调用异常: {e}")
        return False

async def test_agent_direct_call():
    """模拟代理的_direct_gemini_call方法"""
    print("\n🚀 测试 2: 模拟代理_direct_gemini_call方法")
    
    try:
        # 导入代理类
        from agents.base_agent_v4 import create_enhanced_assistant_agent
        from autogen_agentchat.messages import TextMessage
        
        # 获取环境变量
        api_key = os.getenv("OPENAI_API_KEY")
        base_url = os.getenv("OPENAI_BASE_URL")
        model = os.getenv("OPENAI_MODEL", "gemini-2.5-flash")
        
        print(f"📋 创建代理前环境变量:")
        print(f"  API Key: '{api_key}' (长度: {len(api_key)})")
        print(f"  Base URL: '{base_url}'")
        print(f"  Model: '{model}'")
        
        # 创建代理
        agent = await create_enhanced_assistant_agent(
            name="测试代理",
            system_message="你是一个测试代理",
            api_key=api_key,
            base_url=base_url,
            model=model
        )
        print("✅ 代理创建成功")
        
        # 检查代理创建后的环境变量
        api_key_after = os.getenv("OPENAI_API_KEY")
        if api_key != api_key_after:
            print(f"⚠️  代理创建后API Key发生变化!")
            print(f"  原始: '{api_key}'")
            print(f"  现在: '{api_key_after}'")
        
        # 创建测试消息
        test_message = TextMessage(content="你好", source="user")
        
        # 直接调用_direct_gemini_call方法
        print("📞 调用_direct_gemini_call方法...")
        result = await agent._direct_gemini_call([test_message])
        
        if result and hasattr(result, 'content') and "无法获取" not in result.content:
            print(f"✅ 代理直接调用成功: {result.content[:50]}...")
            return True
        else:
            print(f"❌ 代理直接调用失败: {result.content if result else 'None'}")
            return False
            
    except Exception as e:
        print(f"❌ 代理直接调用异常: {e}")
        return False

async def test_system_runtime_simulation():
    """模拟主系统运行时的完整环境"""
    print("\n🚀 测试 3: 模拟主系统运行时环境")
    
    try:
        # 模拟主系统的完整初始化流程
        from teams.team_coordinator_v4 import TeamCoordinator
        from agents.base_agent_v4 import create_enhanced_assistant_agent
        from cognitive_context.protocol_shells import ProtocolShellManager
        from cognitive_context.cognitive_analysis import CognitiveTools
        from autogen_agentchat.messages import TextMessage
        
        # 获取环境变量
        api_key = os.getenv("OPENAI_API_KEY")
        base_url = os.getenv("OPENAI_BASE_URL")
        model = os.getenv("OPENAI_MODEL", "gemini-2.5-flash")
        
        print(f"📋 系统初始化前环境变量:")
        print(f"  API Key: '{api_key}' (长度: {len(api_key)})")
        
        # 1. 初始化系统组件
        protocol_manager = ProtocolShellManager()
        cognitive_tools = CognitiveTools()
        print("✅ 系统组件初始化完成")
        
        # 2. 初始化团队协调器
        coordinator = TeamCoordinator(
            name="测试协调器",
            api_key=api_key,
            base_url=base_url,
            model=model
        )
        print("✅ 团队协调器初始化完成")
        
        # 3. 创建代理
        agent = create_enhanced_assistant_agent(
            name="测试代理",
            system_message="你是一个测试代理",
            api_key=api_key,
            base_url=base_url,
            model=model
        )
        print("✅ 代理创建完成")
        
        # 检查环境变量是否被修改
        api_key_final = os.getenv("OPENAI_API_KEY")
        if api_key != api_key_final:
            print(f"⚠️  系统初始化后API Key发生变化!")
            print(f"  原始: '{api_key}'")
            print(f"  最终: '{api_key_final}'")
        else:
            print("✅ API Key在系统初始化后保持不变")
        
        # 4. 测试消息处理
        test_message = TextMessage(content="你好", source="user")
        print("📞 在完整系统环境中调用_direct_gemini_call...")
        
        result = await agent._direct_gemini_call([test_message])
        
        if result and hasattr(result, 'content') and "无法获取" not in result.content:
            print(f"✅ 系统运行时调用成功: {result.content[:50]}...")
            return True
        else:
            print(f"❌ 系统运行时调用失败: {result.content if result else 'None'}")
            return False
            
    except Exception as e:
        print(f"❌ 系统运行时模拟异常: {e}")
        return False

async def main():
    """主测试函数"""
    print("🔍 精确定位401错误调试")
    print("=" * 60)
    
    # 运行三个测试
    test1_result = await test_independent_api_call()
    test2_result = await test_agent_direct_call()
    test3_result = await test_system_runtime_simulation()
    
    print("\n" + "=" * 60)
    print("📊 测试结果总结:")
    print(f"  独立API调用: {'✅ 成功' if test1_result else '❌ 失败'}")
    print(f"  代理直接调用: {'✅ 成功' if test2_result else '❌ 失败'}")
    print(f"  系统运行时模拟: {'✅ 成功' if test3_result else '❌ 失败'}")
    
    if test1_result and test2_result and test3_result:
        print("\n🎉 所有测试都成功！问题可能在于特定的运行时条件")
    elif test1_result and not (test2_result or test3_result):
        print("\n💡 独立API调用成功，但代理调用失败，问题在于代理实现")
    elif test1_result and test2_result and not test3_result:
        print("\n💡 代理调用成功，但系统运行时失败，问题在于系统初始化流程")
    else:
        print("\n❌ 需要进一步排查API调用的基础问题")

if __name__ == "__main__":
    asyncio.run(main())

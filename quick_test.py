#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速测试修复后的系统
"""

import asyncio
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv('.env')
load_dotenv('.env.local', override=True)

from clients.gemini_client import GeminiClient

async def quick_test():
    """快速测试"""
    try:
        api_key = os.getenv('OPENAI_API_KEY')
        base_url = os.getenv('OPENAI_BASE_URL')
        
        print("🚀 快速测试 GeminiClient...")
        
        client = GeminiClient(api_key=api_key, base_url=base_url)
        result = await client.generate_content("简单回复：你好")
        
        print(f"📝 结果: {result}")
        
        await client.close()
        return "success" in result.lower() or len(result) > 10
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(quick_test())
    print(f"🎯 测试结果: {'成功' if success else '失败'}")

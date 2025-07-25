#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
环境变量缓存管理器
确保API调用的环境变量一致性，解决401错误问题
"""

import os
import logging
from typing import Dict, Optional
from dotenv import load_dotenv

# 确保环境变量已加载
load_dotenv('.env.local')
load_dotenv('.env')

logger = logging.getLogger(__name__)

class EnvironmentCacheManager:
    """环境变量缓存管理器 - 确保一致性和可靠性"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        """单例模式确保全局唯一"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """初始化环境变量缓存"""
        if self._initialized:
            return
        
        # 缓存关键环境变量
        self._cached_env = {
            'api_key': os.getenv('OPENAI_API_KEY'),
            'base_url': os.getenv('OPENAI_BASE_URL'),
            'model': os.getenv('OPENAI_MODEL', 'gemini-2.5-flash'),
            'brave_api_key': os.getenv('BRAVE_API_KEY'),
            'search_engine_url': os.getenv('SEARCH_ENGINE_BASE_URL'),
            'search_engine_api_key': os.getenv('SEARCH_ENGINE_API_KEY'),
        }
        
        # 验证必需的环境变量
        if not self._cached_env['api_key']:
            raise ValueError("OPENAI_API_KEY 环境变量未设置")
        if not self._cached_env['base_url']:
            raise ValueError("OPENAI_BASE_URL 环境变量未设置")
        
        # 清理API密钥（去除可能的空格和换行符）
        self._cached_env['api_key'] = self._cached_env['api_key'].strip()
        if self._cached_env['base_url']:
            self._cached_env['base_url'] = self._cached_env['base_url'].strip()
        
        self._initialized = True
        logger.info(f"环境变量缓存管理器初始化完成: API Key长度={len(self._cached_env['api_key'])}")
    
    def get_api_key(self) -> str:
        """获取缓存的API密钥"""
        return self._cached_env['api_key']
    
    def get_base_url(self) -> str:
        """获取缓存的基础URL"""
        return self._cached_env['base_url']
    
    def get_model(self) -> str:
        """获取缓存的模型名称"""
        return self._cached_env['model']
    
    def get_api_config(self) -> Dict[str, str]:
        """获取完整的API配置"""
        return {
            'api_key': self._cached_env['api_key'],
            'base_url': self._cached_env['base_url'],
            'model': self._cached_env['model']
        }
    
    def get_search_config(self) -> Dict[str, Optional[str]]:
        """获取搜索引擎配置"""
        return {
            'brave_api_key': self._cached_env['brave_api_key'],
            'search_engine_url': self._cached_env['search_engine_url'],
            'search_engine_api_key': self._cached_env['search_engine_api_key']
        }
    
    def validate_config(self) -> bool:
        """验证配置的有效性"""
        try:
            if not self._cached_env['api_key'] or len(self._cached_env['api_key']) < 5:
                logger.error("API密钥无效或过短")
                return False
            
            if not self._cached_env['base_url'] or not self._cached_env['base_url'].startswith('http'):
                logger.error("基础URL无效")
                return False
            
            if not self._cached_env['model']:
                logger.error("模型名称未设置")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"配置验证失败: {e}")
            return False
    
    def refresh_cache(self):
        """刷新缓存（重新读取环境变量）"""
        logger.info("刷新环境变量缓存")
        self._initialized = False
        self.__init__()
    
    def get_debug_info(self) -> Dict[str, str]:
        """获取调试信息"""
        return {
            'api_key_length': str(len(self._cached_env['api_key'])),
            'api_key_prefix': self._cached_env['api_key'][:10] + '...' if len(self._cached_env['api_key']) > 10 else self._cached_env['api_key'],
            'base_url': self._cached_env['base_url'],
            'model': self._cached_env['model'],
            'initialized': str(self._initialized)
        }

# 全局实例
env_cache = EnvironmentCacheManager()

# 便捷函数
def get_cached_api_key() -> str:
    """获取缓存的API密钥"""
    return env_cache.get_api_key()

def get_cached_base_url() -> str:
    """获取缓存的基础URL"""
    return env_cache.get_base_url()

def get_cached_model() -> str:
    """获取缓存的模型名称"""
    return env_cache.get_model()

def get_cached_api_config() -> Dict[str, str]:
    """获取缓存的API配置"""
    return env_cache.get_api_config()

def validate_cached_config() -> bool:
    """验证缓存的配置"""
    return env_cache.validate_config()

def get_debug_info() -> Dict[str, str]:
    """获取调试信息"""
    return env_cache.get_debug_info()

if __name__ == "__main__":
    # 测试环境变量缓存管理器
    print("🔍 测试环境变量缓存管理器")
    print("=" * 50)
    
    try:
        manager = EnvironmentCacheManager()
        
        print("✅ 管理器创建成功")
        print(f"📋 调试信息: {manager.get_debug_info()}")
        print(f"✅ 配置验证: {manager.validate_config()}")
        
        config = manager.get_api_config()
        print(f"📦 API配置: {config}")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")

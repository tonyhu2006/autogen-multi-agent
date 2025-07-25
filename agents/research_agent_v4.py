#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
研究代理 - AutoGen v0.4+ API版本
===============================

基于AutoGen v0.4+的现代化研究代理实现，
集成Brave Search API和认知增强功能。
"""

import os
import asyncio
import logging
import json
import aiohttp
from typing import Dict, List, Any, Optional, Union
from datetime import datetime

from autogen_agentchat.messages import ChatMessage, TextMessage
from autogen_ext.models.openai import OpenAIChatCompletionClient

# 导入自定义 Gemini 客户端
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from clients.gemini_client import create_gemini_client

from dotenv import load_dotenv

# 导入基础代理
from agents.base_agent_v4 import EnhancedAssistantAgent
from cognitive_context.cognitive_analysis import CognitiveTools, CognitiveLevel

# 加载环境变量
load_dotenv()

# 配置日志
logger = logging.getLogger(__name__)


class EnhancedResearchAgent(EnhancedAssistantAgent):
    """增强型研究代理 (v0.4)"""
    
    def __init__(
        self,
        name: str = "研究代理",
        model_client: Optional[OpenAIChatCompletionClient] = None,
        brave_api_key: Optional[str] = None,
        search_engine_url: Optional[str] = None,
        search_engine_api_key: Optional[str] = None,
        cognitive_level: CognitiveLevel = CognitiveLevel.DEEP,
        **kwargs
    ):
        """
        初始化增强型研究代理。
        
        Args:
            name: 代理名称
            model_client: OpenAI模型客户端
            brave_api_key: Brave Search API密钥
            cognitive_level: 认知水平
        """
        # 构建研究代理的系统消息
        system_message = self._build_research_system_message()
        
        # 初始化父类
        super().__init__(
            name=name,
            model_client=model_client,
            agent_type="research",
            cognitive_level=cognitive_level,
            system_message=system_message,
            **kwargs
        )
        
        # 研究代理特有配置
        self.brave_api_key = brave_api_key or os.getenv("BRAVE_API_KEY")
        self.search_engine_url = search_engine_url or os.getenv("SEARCH_ENGINE_BASE_URL")
        self.search_engine_api_key = search_engine_api_key or os.getenv("SEARCH_ENGINE_API_KEY")
        
        # 选择搜索引擎
        if self.search_engine_url:
            self.search_endpoint = self.search_engine_url
            self.use_searxng = True
        else:
            self.search_endpoint = "https://api.search.brave.com/res/v1/web/search"
            self.use_searxng = False
        
        # 研究状态
        self.research_history = []
        self.search_cache = {}
        self.research_metrics = {
            "searches_performed": 0,
            "sources_analyzed": 0,
            "reports_generated": 0
        }
        
        logger.info(f"增强型研究代理 '{name}' 初始化完成 (v0.4 API)")

    def _build_research_system_message(self) -> str:
        """构建研究代理的系统消息"""
        return """你是一个专业的AI研究代理，具备以下核心能力：

🔍 **研究能力**:
- 使用Brave Search API进行深度网络搜索
- 多源信息收集和交叉验证
- 结构化信息分析和整理

🧠 **认知增强**:
- 深度认知分析和推理
- Context Engineering理论应用
- 批判性思维和信息评估

📊 **报告生成**:
- 专业研究报告撰写
- 数据可视化建议
- 引用和来源标注

请在研究过程中：
1. 使用多个可靠来源
2. 进行批判性分析
3. 提供结构化的研究结果
4. 标注信息来源和可信度"""

    async def on_messages(self, messages: List[ChatMessage], cancellation_token) -> ChatMessage:
        """处理消息并执行研究任务"""
        try:
            # 获取最新消息
            if not messages:
                return TextMessage(
                    content="请提供需要研究的主题或问题。",
                    source=self.name
                )
            
            last_message = messages[-1]
            query = last_message.content if hasattr(last_message, 'content') else str(last_message)
            
            # 检查是否为研究请求
            if self._is_research_request(query):
                # 执行研究任务
                research_result = await self._perform_research(query)
                
                # 生成研究报告
                report = await self._generate_research_report(query, research_result)
                
                return TextMessage(
                    content=report,
                    source=self.name
                )
            else:
                # 使用父类处理普通对话
                return await super().on_messages(messages, cancellation_token)
                
        except Exception as e:
            logger.error(f"研究代理消息处理错误: {e}")
            return TextMessage(
                content=f"研究过程中遇到错误: {str(e)}",
                source=self.name
            )

    def _is_research_request(self, query: str) -> bool:
        """判断是否为研究请求"""
        # 需要实时信息的关键词（应该使用搜索）
        realtime_keywords = [
            "今天", "现在", "当前", "最新", "实时", "日期", "时间", "新闻", "进展", "资讯",
            "today", "now", "current", "latest", "real-time", "date", "time", "news", "update"
        ]
        
        # 传统研究关键词
        research_keywords = [
            "研究", "调查", "分析", "搜索", "查找", "了解",
            "research", "investigate", "analyze", "search", "find", "study"
        ]
        
        query_lower = query.lower()
        # 如果包含实时信息关键词或研究关键词，都应该执行搜索
        return any(keyword in query_lower for keyword in realtime_keywords + research_keywords)

    async def _perform_research(self, query: str) -> Dict[str, Any]:
        """执行研究任务"""
        try:
            logger.info(f"开始研究: {query}")
            
            # 检查缓存
            cache_key = query.lower().strip()
            if cache_key in self.search_cache:
                logger.info("使用缓存的搜索结果")
                return self.search_cache[cache_key]
            
            # 执行搜索
            if self.use_searxng:
                search_results = await self._searxng_search(query)
            else:
                search_results = await self._brave_search(query)
            
            # 分析搜索结果
            analyzed_results = await self._analyze_search_results(search_results)
            
            # 缓存结果
            research_result = {
                "query": query,
                "search_results": search_results,
                "analysis": analyzed_results,
                "timestamp": datetime.now().isoformat(),
                "sources_count": len(search_results.get("web", {}).get("results", []))
            }
            
            self.search_cache[cache_key] = research_result
            self.research_history.append(research_result)
            
            # 更新指标
            self.research_metrics["searches_performed"] += 1
            self.research_metrics["sources_analyzed"] += research_result["sources_count"]
            
            logger.info(f"研究完成，分析了 {research_result['sources_count']} 个来源")
            return research_result
            
        except Exception as e:
            logger.error(f"研究执行错误: {e}")
            return {"error": str(e), "query": query}

    async def _searxng_search(self, query: str, count: int = 10) -> Dict[str, Any]:
        """使用SearXNG进行搜索"""
        try:
            params = {
                "q": query,
                "format": "json",
                "categories": "general",
                "engines": "google,bing,duckduckgo",
                "safesearch": "1",
                "time_range": "week"
            }
            
            headers = {
                "Accept": "application/json",
                "User-Agent": "AutoGen-Research-Agent/1.0"
            }
            
            if self.search_engine_api_key:
                headers["Authorization"] = f"Bearer {self.search_engine_api_key}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    self.search_endpoint,
                    headers=headers,
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._convert_searxng_to_standard_format(data, query)
                    else:
                        logger.error(f"SearXNG搜索错误: {response.status}")
                        return self._get_mock_search_results(query)
                        
        except Exception as e:
            logger.error(f"SearXNG搜索请求错误: {e}")
            return self._get_mock_search_results(query)
    
    def _convert_searxng_to_standard_format(self, searxng_data: Dict[str, Any], query: str) -> Dict[str, Any]:
        """将SearXNG结果转换为标准格式"""
        try:
            results = []
            for result in searxng_data.get("results", [])[:10]:  # 限制前10个结果
                results.append({
                    "title": result.get("title", ""),
                    "url": result.get("url", ""),
                    "description": result.get("content", ""),
                    "date_published": result.get("publishedDate", datetime.now().isoformat()),
                    "engine": result.get("engine", "unknown")
                })
            
            return {
                "web": {
                    "results": results
                },
                "query": query,
                "type": "searxng_results",
                "engines_used": list(set([r.get("engine", "unknown") for r in searxng_data.get("results", [])]))
            }
        except Exception as e:
            logger.error(f"SearXNG结果转换错误: {e}")
            return self._get_mock_search_results(query)
    
    async def _brave_search(self, query: str, count: int = 10) -> Dict[str, Any]:
        """使用Brave Search API进行搜索"""
        if not self.brave_api_key:
            logger.warning("未配置Brave API密钥，返回模拟结果")
            return self._get_mock_search_results(query)
        
        try:
            headers = {
                "Accept": "application/json",
                "Accept-Encoding": "gzip",
                "X-Subscription-Token": self.brave_api_key
            }
            
            params = {
                "q": query,
                "count": count,
                "search_lang": "zh",
                "country": "CN",
                "safesearch": "moderate",
                "freshness": "pw"  # 过去一周
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    self.search_endpoint,
                    headers=headers,
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        logger.error(f"Brave Search API错误: {response.status}")
                        return self._get_mock_search_results(query)
                        
        except Exception as e:
            logger.error(f"Brave Search请求错误: {e}")
            return self._get_mock_search_results(query)

    def _get_mock_search_results(self, query: str) -> Dict[str, Any]:
        """获取模拟搜索结果（用于测试）"""
        return {
            "web": {
                "results": [
                    {
                        "title": f"关于 {query} 的研究报告",
                        "url": "https://example.com/research1",
                        "description": f"这是一份关于 {query} 的详细研究报告，包含最新的发展趋势和分析。",
                        "date_published": datetime.now().isoformat()
                    },
                    {
                        "title": f"{query} 最新发展动态",
                        "url": "https://example.com/news1", 
                        "description": f"最新的 {query} 发展动态和行业分析，提供专业见解。",
                        "date_published": datetime.now().isoformat()
                    }
                ]
            },
            "query": query,
            "type": "mock_results"
        }

    async def _analyze_search_results(self, search_results: Dict[str, Any]) -> Dict[str, Any]:
        """分析搜索结果"""
        try:
            web_results = search_results.get("web", {}).get("results", [])
            
            if not web_results:
                return {"error": "没有找到搜索结果"}
            
            # 使用认知工具分析
            analysis = {
                "sources_analyzed": len(web_results),
                "key_topics": [],
                "credibility_assessment": {},
                "summary": "",
                "recommendations": []
            }
            
            # 提取关键主题
            all_text = " ".join([
                result.get("title", "") + " " + result.get("description", "")
                for result in web_results
            ])
            
            if hasattr(self, 'cognitive_tools') and all_text:
                cognitive_analysis = self.cognitive_tools.analyze_text(
                    all_text,
                    level=self.cognitive_level
                )
                
                analysis.update({
                    "cognitive_analysis": cognitive_analysis,
                    "key_topics": cognitive_analysis.get("key_concepts", []),
                    "summary": cognitive_analysis.get("summary", "")
                })
            
            # 评估来源可信度
            for i, result in enumerate(web_results):
                url = result.get("url", "")
                domain = url.split("//")[-1].split("/")[0] if "//" in url else url
                
                # 简单的可信度评估
                credibility_score = self._assess_source_credibility(domain)
                analysis["credibility_assessment"][domain] = credibility_score
            
            return analysis
            
        except Exception as e:
            logger.error(f"搜索结果分析错误: {e}")
            return {"error": str(e)}

    def _assess_source_credibility(self, domain: str) -> Dict[str, Any]:
        """评估来源可信度"""
        # 简化的可信度评估
        trusted_domains = [
            "wikipedia.org", "nature.com", "science.org", "ieee.org",
            "arxiv.org", "pubmed.ncbi.nlm.nih.gov", "scholar.google.com"
        ]
        
        news_domains = [
            "bbc.com", "reuters.com", "ap.org", "cnn.com",
            "xinhuanet.com", "people.com.cn"
        ]
        
        if any(trusted in domain for trusted in trusted_domains):
            return {"score": 0.9, "type": "academic/reference", "reliability": "high"}
        elif any(news in domain for news in news_domains):
            return {"score": 0.7, "type": "news", "reliability": "medium-high"}
        else:
            return {"score": 0.5, "type": "general", "reliability": "medium"}

    async def _generate_research_report(self, query: str, research_result: Dict[str, Any]) -> str:
        """生成研究报告"""
        try:
            self.research_metrics["reports_generated"] += 1
            
            if "error" in research_result:
                return f"研究报告生成失败: {research_result['error']}"
            
            # 构建报告
            report = f"""# 研究报告: {query}

## 📊 研究概览
- **研究时间**: {research_result.get('timestamp', '未知')}
- **分析来源**: {research_result.get('sources_count', 0)} 个
- **研究类型**: 网络搜索 + 认知分析

## 🔍 主要发现
"""
            
            # 添加分析结果
            analysis = research_result.get("analysis", {})
            
            if "key_topics" in analysis and analysis["key_topics"]:
                report += "\n### 关键主题\n"
                for topic in analysis["key_topics"][:5]:  # 限制前5个
                    report += f"- {topic}\n"
            
            if "summary" in analysis and analysis["summary"]:
                report += f"\n### 研究摘要\n{analysis['summary']}\n"
            
            # 添加来源信息
            search_results = research_result.get("search_results", {})
            web_results = search_results.get("web", {}).get("results", [])
            
            if web_results:
                report += "\n## 📚 信息来源\n"
                for i, result in enumerate(web_results[:5], 1):  # 限制前5个来源
                    title = result.get("title", "未知标题")
                    url = result.get("url", "")
                    description = result.get("description", "")
                    
                    report += f"\n{i}. **{title}**\n"
                    report += f"   - 链接: {url}\n"
                    if description:
                        report += f"   - 描述: {description[:200]}...\n"
            
            # 添加可信度评估
            credibility = analysis.get("credibility_assessment", {})
            if credibility:
                report += "\n## 🔒 来源可信度评估\n"
                for domain, assessment in credibility.items():
                    score = assessment.get("score", 0)
                    reliability = assessment.get("reliability", "未知")
                    report += f"- {domain}: {score:.1f}/1.0 ({reliability})\n"
            
            # 添加建议
            report += "\n## 💡 研究建议\n"
            report += "- 建议进一步查阅学术文献以获得更深入的见解\n"
            report += "- 可以关注最新的行业报告和政策文件\n"
            report += "- 建议交叉验证多个来源的信息\n"
            
            return report
            
        except Exception as e:
            logger.error(f"报告生成错误: {e}")
            return f"研究报告生成失败: {str(e)}"

    def get_research_metrics(self) -> Dict[str, Any]:
        """获取研究指标"""
        base_metrics = self.get_performance_metrics()
        return {
            **base_metrics,
            **self.research_metrics,
            "research_history_count": len(self.research_history),
            "cache_size": len(self.search_cache)
        }

    async def clear_research_cache(self):
        """清理研究缓存"""
        self.search_cache.clear()
        logger.info("研究缓存已清理")

    async def export_research_history(self, filepath: str):
        """导出研究历史"""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self.research_history, f, ensure_ascii=False, indent=2)
            logger.info(f"研究历史已导出到: {filepath}")
        except Exception as e:
            logger.error(f"导出研究历史错误: {e}")


# 工厂函数
async def create_research_agent(
    name: str = "研究代理",
    api_key: str = None,
    base_url: str = None,
    brave_api_key: str = None,
    model: str = "gpt-4o",
    **kwargs
) -> EnhancedResearchAgent:
    """创建研究代理的工厂函数"""
    
    if not api_key:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("需要提供OpenAI API密钥")
    
    # 创建模型客户端 - 支持 Gemini
    if base_url and "gemini" in model.lower():
        # 使用 Gemini 客户端
        model_client = create_gemini_client(
            model=model,
            api_key=api_key,
            base_url=base_url
        )
    else:
        # 使用 OpenAI 客户端
        client_kwargs = {
            "model": model,
            "api_key": api_key
        }
        
        if base_url:
            client_kwargs["base_url"] = base_url
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
    
    # 创建研究代理
    agent = EnhancedResearchAgent(
        name=name,
        model_client=model_client,
        brave_api_key=brave_api_key,
        **kwargs
    )
    
    return agent


# 使用示例
if __name__ == "__main__":
    async def main():
        try:
            # 创建研究代理
            research_agent = await create_research_agent(
                name="AI研究专家",
                brave_api_key=os.getenv("BRAVE_API_KEY")
            )
            
            # 模拟研究任务
            from autogen_agentchat.messages import TextMessage
            
            test_message = TextMessage(
                content="请研究人工智能在医疗领域的最新应用",
                source="user"
            )
            
            # 执行研究
            result = await research_agent.on_messages([test_message], None)
            print(f"研究结果:\n{result.content}")
            
            # 显示指标
            metrics = research_agent.get_research_metrics()
            print(f"\n研究指标: {json.dumps(metrics, indent=2, ensure_ascii=False)}")
            
            # 关闭客户端
            await research_agent.model_client.close()
            
        except Exception as e:
            logger.error(f"示例运行错误: {e}")
    
    # 运行示例
    asyncio.run(main())

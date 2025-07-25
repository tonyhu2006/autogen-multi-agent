#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
本地研究代理 - 使用SearXNG搜索引擎
==================================

使用本地SearXNG搜索引擎的研究代理
"""

import asyncio
import aiohttp
import json
import logging
import os
from typing import Dict, Any, List, Optional
from datetime import datetime
from urllib.parse import quote

logger = logging.getLogger(__name__)

class LocalResearchAgent:
    """使用本地SearXNG搜索引擎的研究代理"""
    
    def __init__(self, name: str = "local_research_agent"):
        self.name = name
        self.search_base_url = os.getenv("SEARCH_ENGINE_BASE_URL", "http://127.0.0.1:8081/search")
        self.ai_model_url = os.getenv("OPENAI_BASE_URL", "http://84.8.145.89:8000")
        self.session = None
        
    async def __aenter__(self):
        """异步上下文管理器"""
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def _call_ai_model(self, prompt: str) -> str:
        """调用Gemini Balance代理服务器"""
        try:
            # 使用Gemini原生API格式
            ai_url = f"{self.ai_model_url}/v1beta/models/{os.getenv('OPENAI_MODEL', 'gemini-2.5-flash')}:generateContent"
            headers = {
                "Content-Type": "application/json",
                "x-goog-api-key": os.getenv('OPENAI_API_KEY', 'Hjd-961207hjd')
            }
            
            # Gemini Balance代理所需的格式
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
            
            logger.info(f"调用Gemini API: {ai_url}")
            async with self.session.post(ai_url, json=payload, headers=headers) as response:
                if response.status == 200:
                    result = await response.json()
                    # Gemini API响应格式
                    if 'candidates' in result and len(result['candidates']) > 0:
                        content = result['candidates'][0]['content']['parts'][0]['text']
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
            logger.error(f"Gemini API调用错误: {e}")
            return f"分析错误: {str(e)}"
    
    async def _translate_to_chinese(self, text: str) -> str:
        """使用AI模型将文本翻译为中文"""
        if not text or len(text.strip()) == 0:
            return text
        
        # 检查是否已经是中文
        chinese_chars = sum(1 for char in text if '\u4e00' <= char <= '\u9fff')
        if chinese_chars / len(text) > 0.5:  # 如果中文字符超过50%，认为已经是中文
            return text
        
        translate_prompt = f"""请将以下文本翻译为中文，保持原意和专业性：

{text}

请只返回翻译结果，不要包含其他解释。"""
        
        try:
            translated = await self._call_ai_model(translate_prompt)
            return translated.strip()
        except Exception as e:
            logger.error(f"翻译错误: {e}")
            return text  # 翻译失败时返回原文
    
    async def search_web(self, query: str, max_results: int = 10) -> Dict[str, Any]:
        """使用SearXNG进行网络搜索"""
        try:
            if not self.session:
                self.session = aiohttp.ClientSession()
            
            # 构建搜索URL
            encoded_query = quote(query)
            search_url = f"{self.search_base_url}?q={encoded_query}&format=json"
            
            logger.info(f"正在搜索: {query}")
            logger.info(f"搜索URL: {search_url}")
            
            async with self.session.get(search_url) as response:
                if response.status == 200:
                    search_data = await response.json()
                    
                    # 处理SearXNG响应格式
                    results = []
                    if 'results' in search_data:
                        for idx, item in enumerate(search_data['results'][:max_results]):
                            results.append({
                                "title": item.get("title", ""),
                                "url": item.get("url", ""),
                                "description": item.get("content", ""),
                                "relevance_score": round(1.0 - (idx * 0.1), 2),
                                "source": item.get("engine", "SearXNG")
                            })
                    
                    summary_text = ""
                    for result in results:
                        summary_text += result.get("description", "") + " "
                    
                    return {
                        "query": query,
                        "total_results": len(results),
                        "web_results": results,
                        "search_timestamp": str(datetime.now()),
                        "search_engine": "SearXNG (local)",
                        "status": "success",
                        "summary": summary_text
                    }
                else:
                    return {
                        "query": query,
                        "total_results": 0,
                        "web_results": [],
                        "error": f"搜索失败，状态码: {response.status}",
                        "search_timestamp": str(datetime.now()),
                        "status": "error"
                    }
                    
        except aiohttp.ClientConnectorError:
            return {
                "query": query,
                "total_results": 0,
                "web_results": [],
                "error": "无法连接到本地SearXNG服务，请确保服务已启动",
                "search_timestamp": str(datetime.now()),
                "status": "error"
            }
        except Exception as e:
            logger.error(f"搜索错误: {e}")
            return {
                "query": query,
                "total_results": 0,
                "web_results": [],
                "error": str(e),
                "search_timestamp": str(datetime.now()),
                "status": "error"
            }
    
    async def analyze_search_results(self, search_results: Dict[str, Any]) -> Dict[str, Any]:
        """使用AI模型分析搜索结果"""
        if search_results.get("status") != "success":
            return search_results
            
        results = search_results["web_results"]
        query = search_results.get("query", "")
        
        # 构建分析提示词
        content_text = "\n".join([
            f"标题: {result.get('title', '')}"
            f"描述: {result.get('description', '')}"
            f"来源: {result.get('url', '')}"
            for result in results[:5]  # 只分析前5个结果
        ])
        
        analysis_prompt = f"""作为一个专业的研究分析师，请对以下搜索结果进行深度分析：

查询主题: {query}

搜索结果:
{content_text}

请提供：
1. 关键概念和主题（中文）
2. 主要发现和见解（中文）
3. 信息可信度评估
4. 建议的后续行动（中文）

请用中文回复，保持专业和客观。"""
        
        try:
            # 调用AI模型进行分析
            ai_analysis = await self._call_ai_model(analysis_prompt)
            
            return {
                "analysis_metadata": {
                    "query": query,
                    "analyzed_at": str(datetime.now()),
                    "agent": self.name,
                    "ai_model": "gemini-2.5-flash"
                },
                "ai_analysis": ai_analysis,
                "content_summary": f"使用AI模型对{len(results)}个搜索结果进行了深度分析",
                "total_sources": len(results)
            }
        except Exception as e:
            logger.error(f"AI分析错误: {e}")
            # 回退到基本分析
            return {
                "analysis_metadata": {
                    "query": query,
                    "analyzed_at": str(datetime.now()),
                    "agent": self.name
                },
                "content_summary": f"从{len(results)}个搜索结果中提取了基本信息",
                "total_sources": len(results),
                "error": f"AI分析失败: {str(e)}"
            }
    
    async def generate_research_report(self, search_results: Dict[str, Any], 
                                     analysis: Dict[str, Any]) -> Dict[str, Any]:
        """基于搜索结果和AI分析生成研究报告"""
        query = search_results.get("query", "研究主题")
        results = search_results.get("web_results", [])
        ai_analysis = analysis.get("ai_analysis", "未进行AI分析")
        
        if not results:
            return {
                "report_metadata": {
                    "title": f"研究报告: {query}",
                    "generated_at": str(datetime.now()),
                    "agent": self.name,
                    "status": "no_results"
                },
                "executive_summary": f"未能找到关于{query}的足够信息",
                "key_findings": [],
                "recommendations": ["尝试不同的搜索关键词", "检查SearXNG服务状态"]
            }
        
        # 构建详细的中文研究报告
        detailed_sources = []
        key_findings = []
        
        for idx, result in enumerate(results[:8]):  # 增加到8个结果
            # 提取每条消息的详细内容
            original_title = result.get("title", "无标题")
            original_description = result.get("description", "")
            url = result.get("url", "")
            source = result.get("source", "未知")
            
            # 使用AI翻译标题和描述为中文
            title = await self._translate_to_chinese(original_title)
            description = await self._translate_to_chinese(original_description)
            
            # 生成关键要点
            key_points = []
            if description:
                # 提取前3个关键句子
                sentences = description.split('。')  # 使用中文句号
                if len(sentences) <= 1:
                    sentences = description.split('.')  # 如果没有中文句号，使用英文句号
                key_points = [s.strip() + ('。' if not s.strip().endswith('。') else '') 
                             for s in sentences[:3] if s.strip()]
            
            # 生成详细发现
            key_findings.append({
                "title": title,
                "url": url,
                "key_points": key_points,
                "summary": description[:200] + "..." if len(description) > 200 else description,
                "relevance": result.get("relevance_score", 0.0),
                "source": source,
                "timestamp": str(datetime.now())
            })
            
            # 添加到详细来源
            detailed_sources.append({
                "id": idx + 1,
                "title": title,
                "url": url,
                "description": description,
                "source": source,
                "relevance": result.get("relevance_score", 0.0),
                "domain": result.get("domain", "unknown")
            })
        
        # 生成包含AI分析的详细报告
        return {
            "report_metadata": {
                "title": f"🔍 研究报告：{query}",
                "generated_at": str(datetime.now()),
                "agent": self.name,
                "status": "success",
                "search_engine": "SearXNG (本地)",
                "ai_model": "Gemini-2.5-flash",
                "total_sources": len(results),
                "confidence_score": round(sum([r.get("relevance_score", 0.0) for r in results]) / len(results) if results else 0.75, 2)
            },
            "executive_summary": f"基于本地SearXNG搜索引擎和Gemini-2.5-flash AI模型，成功找到{len(detailed_sources)}个高质量信息源，涵盖{query}的各个方面",
            "ai_analysis": ai_analysis,
            "key_findings": key_findings,
            "sources": detailed_sources,
            "detailed_analysis": {
                "search_query": query,
                "total_results": len(results),
                "unique_sources": len(set([r.get("source", "unknown") for r in results])),
                "average_relevance": round(sum([r.get("relevance_score", 0.0) for r in results]) / len(results), 2),
                "top_domains": list(set([r.get("domain", "unknown") for r in results]))[:5]
            },
            "recommendations": [
                "优先查看高相关性(>0.7)的信息源",
                "验证关键信息的多个来源以确保准确性",
                "关注权威域名(.edu, .gov, .org)的信息",
                "定期重新搜索以获取最新发展",
                "结合多个信息源形成全面观点"
            ],
            "raw_data": {
                "total_searched": len(results),
                "processed_results": len(detailed_sources),
                "search_timestamp": str(datetime.now()),
                "query_processed": query
            }
        }
    
    async def search_and_analyze(self, query: str) -> Dict[str, Any]:
        """完整的搜索和分析流程"""
        try:
            # 1. 搜索
            search_results = await self.search_web(query)
            
            if search_results.get("status") == "error":
                return search_results
            
            # 2. 分析
            analysis = await self.analyze_search_results(search_results)
            
            # 3. 生成报告
            report = await self.generate_research_report(search_results, analysis)
            
            return {
                "query": query,
                "search_results": search_results,
                "analysis": analysis,
                "research_report": report,
                "workflow_status": "success",
                "timestamp": str(datetime.now())
            }
            
        except Exception as e:
            logger.error(f"搜索分析流程错误: {e}")
            return {
                "query": query,
                "error": str(e),
                "workflow_status": "error",
                "timestamp": str(datetime.now())
            }

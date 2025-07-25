#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
邮件代理 - AutoGen v0.4+ API版本
===============================

基于AutoGen v0.4+的现代化邮件代理实现，
集成Gmail API和智能邮件生成功能。
"""

import os
import asyncio
import logging
import json
import base64
import smtplib
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Gmail API imports
try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    GMAIL_AVAILABLE = True
except ImportError:
    GMAIL_AVAILABLE = False
    logging.warning("Gmail API依赖未安装，邮件功能将受限")

from autogen_agentchat.agents import AssistantAgent
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


class EnhancedEmailAgent(EnhancedAssistantAgent):
    """增强型邮件代理 (v0.4)"""
    
    def __init__(
        self,
        name: str = "邮件代理",
        model_client: Optional[OpenAIChatCompletionClient] = None,
        gmail_credentials_path: Optional[str] = None,
        gmail_token_path: Optional[str] = None,
        sender_email: Optional[str] = None,
        sender_password: Optional[str] = None,
        sender_name: Optional[str] = None,
        smtp_server: Optional[str] = None,
        smtp_port: Optional[int] = None,
        default_recipients: Optional[List[str]] = None,
        cognitive_level: CognitiveLevel = CognitiveLevel.DEEP,
        **kwargs
    ):
        """
        初始化增强型邮件代理。
        
        Args:
            name: 代理名称
            model_client: OpenAI模型客户端
            gmail_credentials_path: Gmail凭据文件路径
            gmail_token_path: Gmail令牌文件路径
            cognitive_level: 认知水平
        """
        # 构建邮件代理的系统消息
        system_message = self._build_email_system_message()
        
        # 初始化父类
        super().__init__(
            name=name,
            model_client=model_client,
            agent_type="email",
            cognitive_level=cognitive_level,
            system_message=system_message,
            **kwargs
        )
        
        # 邮件代理特有配置
        self.gmail_credentials_path = gmail_credentials_path or "credentials.json"
        self.gmail_token_path = gmail_token_path or "token.json"
        self.gmail_scopes = ['https://www.googleapis.com/auth/gmail.send']
        self.gmail_service = None
        
        # SMTP配置
        self.sender_email = sender_email or os.getenv("SENDER_EMAIL")
        self.sender_password = sender_password or os.getenv("SENDER_PASSWORD")
        self.sender_name = sender_name or os.getenv("SENDER_NAME", "AI研究系统")
        self.smtp_server = smtp_server or os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = smtp_port or int(os.getenv("SMTP_PORT", "587"))
        self.default_recipients = default_recipients or []
        
        # 选择邮件发送方式
        self.use_smtp = bool(self.sender_email and self.sender_password)
        self.use_gmail_api = GMAIL_AVAILABLE and not self.use_smtp
        
        # 邮件状态
        self.email_history = []
        self.draft_emails = {}
        self.email_metrics = {
            "emails_generated": 0,
            "emails_sent": 0,
            "drafts_created": 0
        }
        
        # 初始化邮件服务
        if self.use_gmail_api:
            asyncio.create_task(self._initialize_gmail_service())
        elif self.use_smtp:
            logger.info(f"使用SMTP发送邮件: {self.sender_email}")
        else:
            logger.warning("未配置邮件发送方式，邮件功能将受限")
        
        logger.info(f"增强型邮件代理 '{name}' 初始化完成 (v0.4 API)")

    def _build_email_system_message(self) -> str:
        """构建邮件代理的系统消息"""
        return """你是一个专业的AI邮件代理，具备以下核心能力：

📧 **邮件生成**:
- 智能邮件内容生成和格式化
- 多种邮件类型支持（商务、学术、个人）
- 自动主题行生成和优化

🎯 **个性化定制**:
- 根据收件人和场景定制邮件风格
- 语调和正式程度自动调整
- 文化敏感性和礼仪考虑

🔧 **技术集成**:
- Gmail API集成发送邮件
- 邮件模板管理和重用
- 批量邮件处理能力

📊 **质量保证**:
- 邮件内容质量检查
- 语法和拼写检查
- 专业性和清晰度评估

请在生成邮件时：
1. 确保内容专业且清晰
2. 适应收件人的背景和需求
3. 遵循邮件礼仪和最佳实践
4. 提供结构化和易读的格式"""

    async def on_messages(self, messages: List[ChatMessage], cancellation_token) -> ChatMessage:
        """处理消息并执行邮件任务"""
        try:
            # 获取最新消息
            if not messages:
                return TextMessage(
                    content="请提供邮件生成或发送的要求。",
                    source=self.name
                )
            
            last_message = messages[-1]
            request = last_message.content if hasattr(last_message, 'content') else str(last_message)
            
            # 解析邮件请求
            email_task = await self._parse_email_request(request)
            
            if email_task["type"] == "generate":
                # 生成邮件
                email_content = await self._generate_email(email_task)
                response = f"📧 **邮件已生成**\n\n{email_content}"
                
            elif email_task["type"] == "send":
                # 发送邮件
                result = await self._send_email(email_task)
                response = f"📤 **邮件发送结果**\n\n{result}"
                
            elif email_task["type"] == "draft":
                # 创建草稿
                draft_id = await self._create_draft(email_task)
                response = f"📝 **邮件草稿已创建**\n\n草稿ID: {draft_id}"
                
            else:
                # 使用父类处理普通对话
                return await super().on_messages(messages, cancellation_token)
            
            return TextMessage(
                content=response,
                source=self.name
            )
                
        except Exception as e:
            logger.error(f"邮件代理消息处理错误: {e}")
            return TextMessage(
                content=f"邮件处理过程中遇到错误: {str(e)}",
                source=self.name
            )

    async def _parse_email_request(self, request: str) -> Dict[str, Any]:
        """解析邮件请求"""
        try:
            request_lower = request.lower()
            
            # 判断请求类型
            if any(keyword in request_lower for keyword in ["发送", "send"]):
                task_type = "send"
            elif any(keyword in request_lower for keyword in ["草稿", "draft"]):
                task_type = "draft"
            else:
                task_type = "generate"
            
            # 提取邮件信息
            email_task = {
                "type": task_type,
                "original_request": request,
                "subject": "",
                "recipient": "",
                "content": "",
                "email_type": "business",  # business, academic, personal
                "tone": "professional"     # professional, casual, formal
            }
            
            # 简单的信息提取（可以用更复杂的NLP方法）
            lines = request.split('\n')
            for line in lines:
                line = line.strip()
                if line.startswith(('主题:', '标题:', 'subject:')):
                    email_task["subject"] = line.split(':', 1)[1].strip()
                elif line.startswith(('收件人:', '发送给:', 'to:')):
                    email_task["recipient"] = line.split(':', 1)[1].strip()
                elif line.startswith(('内容:', 'content:')):
                    email_task["content"] = line.split(':', 1)[1].strip()
            
            return email_task
            
        except Exception as e:
            logger.error(f"邮件请求解析错误: {e}")
            return {
                "type": "generate",
                "original_request": request,
                "subject": "",
                "recipient": "",
                "content": "",
                "email_type": "business",
                "tone": "professional"
            }

    async def _generate_email(self, email_task: Dict[str, Any]) -> str:
        """生成邮件内容"""
        try:
            self.email_metrics["emails_generated"] += 1
            
            # 构建邮件生成提示
            prompt = self._build_email_generation_prompt(email_task)
            
            # 使用认知工具分析请求
            if hasattr(self, 'cognitive_tools'):
                analysis = self.cognitive_tools.analyze_text(
                    email_task["original_request"],
                    level=self.cognitive_level
                )
                
                # 根据分析调整邮件风格
                if analysis.get("sentiment", {}).get("polarity", 0) > 0.5:
                    email_task["tone"] = "friendly"
                elif "urgent" in analysis.get("key_concepts", []):
                    email_task["tone"] = "urgent"
            
            # 生成邮件内容
            email_content = await self._create_email_content(email_task)
            
            # 保存到历史
            email_record = {
                "timestamp": datetime.now().isoformat(),
                "task": email_task,
                "content": email_content,
                "status": "generated"
            }
            self.email_history.append(email_record)
            
            return email_content
            
        except Exception as e:
            logger.error(f"邮件生成错误: {e}")
            return f"邮件生成失败: {str(e)}"

    def _build_email_generation_prompt(self, email_task: Dict[str, Any]) -> str:
        """构建邮件生成提示"""
        prompt = f"""请根据以下要求生成专业邮件：

**邮件类型**: {email_task['email_type']}
**语调**: {email_task['tone']}
**原始请求**: {email_task['original_request']}
"""
        
        if email_task.get("recipient"):
            prompt += f"**收件人**: {email_task['recipient']}\n"
        
        if email_task.get("subject"):
            prompt += f"**主题**: {email_task['subject']}\n"
        
        prompt += """
请生成包含以下部分的完整邮件：
1. 合适的主题行（如果未提供）
2. 专业的开头问候
3. 清晰的邮件正文
4. 适当的结尾和签名

确保邮件内容专业、清晰且符合商务邮件规范。"""
        
        return prompt

    async def _create_email_content(self, email_task: Dict[str, Any]) -> str:
        """创建邮件内容"""
        try:
            # 这里可以集成更复杂的邮件生成逻辑
            # 目前使用模板方法
            
            # 生成主题（如果没有提供）
            if not email_task.get("subject"):
                subject = await self._generate_subject(email_task)
            else:
                subject = email_task["subject"]
            
            # 生成邮件正文
            body = await self._generate_body(email_task)
            
            # 格式化邮件
            email_content = f"""**主题**: {subject}

**收件人**: {email_task.get('recipient', '[收件人]')}

**邮件正文**:

{body}

---
*此邮件由AI邮件代理生成*"""
            
            return email_content
            
        except Exception as e:
            logger.error(f"邮件内容创建错误: {e}")
            return "邮件内容生成失败"

    async def _generate_subject(self, email_task: Dict[str, Any]) -> str:
        """生成邮件主题"""
        # 简化的主题生成逻辑
        request = email_task["original_request"]
        
        if "会议" in request or "meeting" in request.lower():
            return "会议安排确认"
        elif "报告" in request or "report" in request.lower():
            return "研究报告分享"
        elif "合作" in request or "collaboration" in request.lower():
            return "合作机会讨论"
        else:
            return "重要信息分享"

    async def _generate_body(self, email_task: Dict[str, Any]) -> str:
        """生成邮件正文"""
        tone = email_task.get("tone", "professional")
        email_type = email_task.get("email_type", "business")
        request = email_task["original_request"]
        
        # 根据语调选择开头
        if tone == "formal":
            greeting = "尊敬的先生/女士，"
        elif tone == "casual":
            greeting = "您好，"
        else:
            greeting = "您好，"
        
        # 生成主体内容
        if "研究" in request:
            body = f"""{greeting}

希望这封邮件能够找到您。我想与您分享一些重要的研究发现。

{request}

如果您需要更多详细信息或有任何问题，请随时与我联系。

期待您的回复。

此致
敬礼"""
        else:
            body = f"""{greeting}

希望您一切都好。我写这封邮件是想与您分享以下信息：

{request}

如果您有任何问题或需要进一步讨论，请随时联系我。

谢谢您的时间和关注。

最好的问候"""
        
        return body

    async def _send_email(self, email_task: Dict[str, Any]) -> str:
        """发送邮件"""
        try:
            if self.use_smtp:
                return await self._send_smtp_email(email_task)
            elif self.use_gmail_api:
                return await self._send_gmail_email(email_task)
            else:
                return "未配置邮件发送方式，无法发送邮件"
                
        except Exception as e:
            logger.error(f"邮件发送错误: {e}")
            return f"邮件发送失败: {str(e)}"
    
    async def _send_gmail_email(self, email_task: Dict[str, Any]) -> str:
        """使用Gmail API发送邮件"""
        try:
            if not self.gmail_service:
                await self._initialize_gmail_service()
                if not self.gmail_service:
                    return "Gmail服务初始化失败"
            
            # 生成邮件内容
            email_content = await self._generate_email(email_task)
            
            # 解析邮件内容
            lines = email_content.split('\n')
            subject = ""
            recipient = ""
            body_lines = []
            
            in_body = False
            for line in lines:
                if line.startswith("**主题**:"):
                    subject = line.replace("**主题**:", "").strip()
                elif line.startswith("**收件人**:"):
                    recipient = line.replace("**收件人**:", "").strip()
                elif line.startswith("**邮件正文**:"):
                    in_body = True
                elif in_body and not line.startswith("---"):
                    body_lines.append(line)
            
            body = '\n'.join(body_lines).strip()
            
            # 发送邮件
            result = await self._send_gmail(recipient, subject, body)
            
            if result["success"]:
                self.email_metrics["emails_sent"] += 1
                return f"邮件发送成功！\n消息ID: {result['message_id']}"
            else:
                return f"邮件发送失败: {result['error']}"
                
        except Exception as e:
            logger.error(f"邮件发送错误: {e}")
            return f"邮件发送失败: {str(e)}"

    async def _initialize_gmail_service(self):
        """初始化Gmail服务"""
        try:
            if not GMAIL_AVAILABLE:
                logger.warning("Gmail API不可用")
                return
            
            creds = None
            
            # 加载现有令牌
            if os.path.exists(self.gmail_token_path):
                creds = Credentials.from_authorized_user_file(
                    self.gmail_token_path, self.gmail_scopes
                )
            
            # 如果没有有效凭据，进行授权流程
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    if not os.path.exists(self.gmail_credentials_path):
                        logger.warning(f"Gmail凭据文件不存在: {self.gmail_credentials_path}")
                        return
                    
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.gmail_credentials_path, self.gmail_scopes
                    )
                    creds = flow.run_local_server(port=0)
                
                # 保存凭据
                with open(self.gmail_token_path, 'w') as token:
                    token.write(creds.to_json())
            
            # 构建服务
            self.gmail_service = build('gmail', 'v1', credentials=creds)
            logger.info("Gmail服务初始化成功")
            
        except Exception as e:
            logger.error(f"Gmail服务初始化错误: {e}")
            self.gmail_service = None

    async def _send_gmail(self, to: str, subject: str, body: str) -> Dict[str, Any]:
        """使用Gmail API发送邮件"""
        try:
            if not self.gmail_service:
                return {"success": False, "error": "Gmail服务未初始化"}
            
            # 创建邮件消息
            message = MIMEText(body)
            message['to'] = to
            message['subject'] = subject
            
            # 编码消息
            raw_message = base64.urlsafe_b64encode(
                message.as_bytes()
            ).decode()
            
            # 发送邮件
            send_result = self.gmail_service.users().messages().send(
                userId="me",
                body={'raw': raw_message}
            ).execute()
            
            return {
                "success": True,
                "message_id": send_result['id']
            }
            
        except Exception as e:
            logger.error(f"Gmail发送错误: {e}")
            return {"success": False, "error": str(e)}
    
    async def _send_smtp_email(self, email_task: Dict[str, Any]) -> str:
        """使用SMTP发送邮件"""
        try:
            # 生成邮件内容
            email_content = await self._generate_email(email_task)
            
            # 解析邮件内容
            lines = email_content.split('\n')
            subject = ""
            recipient = ""
            body_lines = []
            
            in_body = False
            for line in lines:
                if line.startswith("**主题**:"):
                    subject = line.replace("**主题**:", "").strip()
                elif line.startswith("**收件人**:"):
                    recipient = line.replace("**收件人**:", "").strip()
                elif line.startswith("**邮件正文**:"):
                    in_body = True
                elif in_body and not line.startswith("---"):
                    body_lines.append(line)
            
            body = '\n'.join(body_lines).strip()
            
            # 如果没有指定收件人，使用默认收件人
            if not recipient and self.default_recipients:
                recipient = self.default_recipients[0]
            
            if not recipient:
                return "错误：未指定收件人"
            
            # 发送邮件
            result = await self._send_smtp(recipient, subject, body)
            
            if result["success"]:
                self.email_metrics["emails_sent"] += 1
                return f"邮件发送成功！\n收件人: {recipient}"
            else:
                return f"邮件发送失败: {result['error']}"
                
        except Exception as e:
            logger.error(f"SMTP邮件发送错误: {e}")
            return f"SMTP邮件发送失败: {str(e)}"
    
    async def _send_smtp(self, to: str, subject: str, body: str) -> Dict[str, Any]:
        """使用SMTP发送邮件"""
        try:
            # 创建邮件消息
            msg = MIMEMultipart()
            msg['From'] = f"{self.sender_name} <{self.sender_email}>"
            msg['To'] = to
            msg['Subject'] = subject
            
            # 添加邮件正文
            msg.attach(MIMEText(body, 'plain', 'utf-8'))
            
            # 连接SMTP服务器并发送
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()  # 启用TLS加密
                server.login(self.sender_email, self.sender_password)
                text = msg.as_string()
                server.sendmail(self.sender_email, to, text)
            
            return {
                "success": True,
                "message_id": f"smtp_{int(datetime.now().timestamp())}"
            }
            
        except Exception as e:
            logger.error(f"SMTP发送错误: {e}")
            return {"success": False, "error": str(e)}

    async def _create_draft(self, email_task: Dict[str, Any]) -> str:
        """创建邮件草稿"""
        try:
            self.email_metrics["drafts_created"] += 1
            
            # 生成邮件内容
            email_content = await self._generate_email(email_task)
            
            # 创建草稿ID
            draft_id = f"draft_{len(self.draft_emails) + 1}_{int(datetime.now().timestamp())}"
            
            # 保存草稿
            self.draft_emails[draft_id] = {
                "content": email_content,
                "task": email_task,
                "created_at": datetime.now().isoformat(),
                "status": "draft"
            }
            
            return draft_id
            
        except Exception as e:
            logger.error(f"草稿创建错误: {e}")
            return f"草稿创建失败: {str(e)}"

    def get_email_metrics(self) -> Dict[str, Any]:
        """获取邮件指标"""
        base_metrics = self.get_performance_metrics()
        return {
            **base_metrics,
            **self.email_metrics,
            "email_history_count": len(self.email_history),
            "draft_count": len(self.draft_emails),
            "gmail_available": GMAIL_AVAILABLE,
            "gmail_service_ready": self.gmail_service is not None
        }

    async def get_draft(self, draft_id: str) -> Optional[Dict[str, Any]]:
        """获取草稿"""
        return self.draft_emails.get(draft_id)

    async def list_drafts(self) -> List[Dict[str, Any]]:
        """列出所有草稿"""
        return [
            {"id": draft_id, **draft_info}
            for draft_id, draft_info in self.draft_emails.items()
        ]


# 工厂函数
async def create_email_agent(
    name: str = "邮件代理",
    api_key: str = None,
    base_url: str = None,
    gmail_credentials_path: str = None,
    model: str = "gpt-4o",
    **kwargs
) -> EnhancedEmailAgent:
    """创建邮件代理的工厂函数"""
    
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
    
    # 创建邮件代理
    agent = EnhancedEmailAgent(
        name=name,
        model_client=model_client,
        gmail_credentials_path=gmail_credentials_path,
        **kwargs
    )
    
    return agent


# 使用示例
if __name__ == "__main__":
    async def main():
        try:
            # 创建邮件代理
            email_agent = await create_email_agent(
                name="智能邮件助手"
            )
            
            # 模拟邮件任务
            from autogen_agentchat.messages import TextMessage
            
            test_message = TextMessage(
                content="""请生成一封邮件：
主题: 项目进度更新
收件人: team@company.com
内容: 向团队汇报本周的项目进展情况""",
                source="user"
            )
            
            # 执行邮件任务
            result = await email_agent.on_messages([test_message], None)
            print(f"邮件结果:\n{result.content}")
            
            # 显示指标
            metrics = email_agent.get_email_metrics()
            print(f"\n邮件指标: {json.dumps(metrics, indent=2, ensure_ascii=False)}")
            
            # 关闭客户端
            await email_agent.model_client.close()
            
        except Exception as e:
            logger.error(f"示例运行错误: {e}")
    
    # 运行示例
    asyncio.run(main())

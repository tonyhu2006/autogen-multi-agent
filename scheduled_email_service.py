#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化定时邮件服务 - AutoGen v0.4+ 多代理 AI 系统
=============================================

基于直接 API 调用的简化版定时邮件推送功能，
避免复杂的团队协调器消息兼容性问题。
"""

import os
import sys
import asyncio
import logging
import json
import schedule
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from pathlib import Path

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入环境配置
from dotenv import load_dotenv
load_dotenv('.env.local')
load_dotenv('.env')

# 导入代理
from agents.research_agent_v4 import create_research_agent
from agents.email_agent_v4 import create_email_agent
from autogen_agentchat.messages import TextMessage

# 导入邮件发送功能
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scheduled_email_simple.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class EmailScheduleConfig:
    """邮件调度配置"""
    topic: str  # 主题关键词
    recipient: str  # 收件人邮箱
    schedule_time: str  # 发送时间 (HH:MM 格式)
    frequency: str  # 频率: daily, weekly, monthly
    subject_template: str  # 邮件主题模板
    enabled: bool = True  # 是否启用


class SimpleScheduledEmailService:
    """简化定时邮件服务"""
    
    def __init__(self, config_file: str = "email_schedules.json"):
        """初始化定时邮件服务"""
        self.config_file = config_file
        self.schedules: List[EmailScheduleConfig] = []
        self.research_agent = None
        self.email_agent = None
        self.running = False
        
        # 加载配置
        self.load_schedules()
        
    def load_schedules(self):
        """加载邮件调度配置"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.schedules = [
                        EmailScheduleConfig(**schedule) 
                        for schedule in data.get('schedules', [])
                    ]
                logger.info(f"加载了 {len(self.schedules)} 个邮件调度配置")
            else:
                # 创建默认配置
                self.create_default_config()
        except Exception as e:
            logger.error(f"加载邮件调度配置失败: {e}")
            self.create_default_config()
    
    def create_default_config(self):
        """创建默认配置"""
        default_schedules = [
            EmailScheduleConfig(
                topic="AGI人工智能",
                recipient="your-email@example.com",
                schedule_time="09:00",
                frequency="daily",
                subject_template="每日AGI研究动态 - {date}",
                enabled=False  # 默认禁用，避免意外发送
            ),
            EmailScheduleConfig(
                topic="科技新闻",
                recipient="your-email@example.com", 
                schedule_time="18:00",
                frequency="daily",
                subject_template="每日科技资讯 - {date}",
                enabled=False
            )
        ]
        
        self.schedules = default_schedules
        self.save_schedules()
        logger.info("创建了默认邮件调度配置")
    
    def save_schedules(self):
        """保存邮件调度配置"""
        try:
            data = {
                "schedules": [
                    {
                        "topic": s.topic,
                        "recipient": s.recipient,
                        "schedule_time": s.schedule_time,
                        "frequency": s.frequency,
                        "subject_template": s.subject_template,
                        "enabled": s.enabled
                    }
                    for s in self.schedules
                ]
            }
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info("邮件调度配置已保存")
        except Exception as e:
            logger.error(f"保存邮件调度配置失败: {e}")
    
    def add_schedule(self, topic: str, recipient: str, schedule_time: str, 
                    frequency: str = "daily", subject_template: str = None):
        """添加新的邮件调度"""
        if subject_template is None:
            subject_template = f"每日{topic}资讯 - {{date}}"
        
        new_schedule = EmailScheduleConfig(
            topic=topic,
            recipient=recipient,
            schedule_time=schedule_time,
            frequency=frequency,
            subject_template=subject_template,
            enabled=True
        )
        
        self.schedules.append(new_schedule)
        self.save_schedules()
        logger.info(f"添加了新的邮件调度: {topic} -> {recipient} at {schedule_time}")
        
        # 重新设置调度
        if self.running:
            self.setup_schedules()
    
    def toggle_schedule(self, index: int):
        """启用/禁用邮件调度"""
        if 0 <= index < len(self.schedules):
            self.schedules[index].enabled = not self.schedules[index].enabled
            self.save_schedules()
            status = "启用" if self.schedules[index].enabled else "禁用"
            logger.info(f"{status}了邮件调度: {self.schedules[index].topic}")
            
            # 重新设置调度
            if self.running:
                self.setup_schedules()
        else:
            logger.error(f"无效的调度索引: {index}")
    
    def edit_schedule(self, index: int, **kwargs):
        """编辑邮件调度配置"""
        if 0 <= index < len(self.schedules):
            schedule = self.schedules[index]
            old_config = {
                'topic': schedule.topic,
                'recipient': schedule.recipient,
                'schedule_time': schedule.schedule_time,
                'frequency': schedule.frequency,
                'subject_template': schedule.subject_template,
                'enabled': schedule.enabled
            }
            
            # 更新配置
            if 'topic' in kwargs:
                schedule.topic = kwargs['topic']
            if 'recipient' in kwargs:
                schedule.recipient = kwargs['recipient']
            if 'schedule_time' in kwargs:
                schedule.schedule_time = kwargs['schedule_time']
            if 'frequency' in kwargs:
                schedule.frequency = kwargs['frequency']
            if 'subject_template' in kwargs:
                schedule.subject_template = kwargs['subject_template']
            if 'enabled' in kwargs:
                schedule.enabled = kwargs['enabled']
            
            self.save_schedules()
            logger.info(f"编辑了邮件调度: {old_config['topic']} -> {schedule.topic}")
            
            # 重新设置调度
            if self.running:
                self.setup_schedules()
            
            return True
        else:
            logger.error(f"无效的调度索引: {index}")
            return False
    
    def delete_schedule(self, index: int):
        """删除邮件调度配置"""
        if 0 <= index < len(self.schedules):
            deleted_schedule = self.schedules.pop(index)
            self.save_schedules()
            logger.info(f"删除了邮件调度: {deleted_schedule.topic} -> {deleted_schedule.recipient}")
            
            # 重新设置调度
            if self.running:
                self.setup_schedules()
            
            return True
        else:
            logger.error(f"无效的调度索引: {index}")
            return False
    
    async def initialize_agents(self):
        """初始化代理"""
        try:
            logger.info("初始化研究代理...")
            self.research_agent = await create_research_agent(
                name="定时邮件研究专家",
                api_key=os.getenv("OPENAI_API_KEY"),
                base_url=os.getenv("OPENAI_BASE_URL"),
                model=os.getenv("OPENAI_MODEL", "gemini-2.5-flash")
            )
            
            logger.info("初始化邮件代理...")
            self.email_agent = await create_email_agent(
                name="定时邮件助手",
                api_key=os.getenv("OPENAI_API_KEY"),
                base_url=os.getenv("OPENAI_BASE_URL"),
                model=os.getenv("OPENAI_MODEL", "gemini-2.5-flash"),
                sender_email=os.getenv("SENDER_EMAIL"),
                sender_password=os.getenv("SENDER_PASSWORD"),
                sender_name=os.getenv("SENDER_NAME", "AI研究系统")
            )
            
            logger.info("代理初始化成功")
        except Exception as e:
            logger.error(f"代理初始化失败: {e}")
            raise
    
    async def send_scheduled_email(self, schedule: EmailScheduleConfig):
        """发送定时邮件"""
        try:
            logger.info(f"开始处理定时邮件: {schedule.topic} -> {schedule.recipient}")
            
            if not self.research_agent or not self.email_agent:
                await self.initialize_agents()
            
            # 构建研究请求
            research_query = f"请提供最新的{schedule.topic}相关信息和研究成果"
            
            # 使用研究代理获取最新信息（直接API调用）
            logger.info("正在搜索最新研究信息...")
            research_message = TextMessage(content=research_query, source="user")
            research_result = await self.research_agent._direct_gemini_call([research_message])
            
            if not research_result or not hasattr(research_result, 'content'):
                logger.warning(f"未能获取{schedule.topic}的研究结果")
                return
            
            research_content = research_result.content
            if not research_content:
                logger.warning(f"研究结果为空: {schedule.topic}")
                return
            
            # 构建邮件内容
            current_date = datetime.now().strftime("%Y年%m月%d日")
            email_subject = schedule.subject_template.format(date=current_date)
            
            email_content = f"""
# {email_subject}

## 📊 研究摘要

{research_content}

---

*本邮件由 AutoGen v0.4+ 多代理 AI 系统自动生成*  
*发送时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*  
*主题关键词: {schedule.topic}*
"""
            
            # 直接发送邮件（真正的 SMTP 发送）
            logger.info("正在发送邮件...")
            email_success = await self._send_smtp_email_direct(
                to_email=schedule.recipient,
                subject=email_subject,
                body=email_content
            )
            
            if email_success:
                logger.info(f"定时邮件发送成功: {schedule.topic} -> {schedule.recipient}")
            else:
                logger.error(f"定时邮件发送失败: {schedule.topic}")
                
        except Exception as e:
            logger.error(f"发送定时邮件时出错: {e}")
    
    async def _send_smtp_email_direct(
        self,
        to_email: str,
        subject: str,
        body: str
    ) -> bool:
        """直接发送 SMTP 邮件"""
        try:
            # 获取配置
            sender_email = os.getenv("SENDER_EMAIL")
            sender_password = os.getenv("SENDER_PASSWORD")
            sender_name = os.getenv("SENDER_NAME", "AI研究系统")
            smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
            smtp_port = int(os.getenv("SMTP_PORT", "587"))
            
            # 验证配置
            if not sender_email or not sender_password:
                logger.error("缺少发件人邮箱或密码配置")
                return False
            
            # 创建邮件消息
            msg = MIMEMultipart()
            msg['From'] = f"{sender_name} <{sender_email}>"
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # 添加邮件正文
            msg.attach(MIMEText(body, 'plain', 'utf-8'))
            
            # 连接SMTP服务器并发送
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()  # 启用TLS加密
                server.login(sender_email, sender_password)
                text = msg.as_string()
                server.sendmail(sender_email, to_email, text)
            
            logger.info(f"✅ SMTP 邮件发送成功: {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"❌ SMTP 邮件发送失败: {e}")
            return False
    
    def setup_schedules(self):
        """设置所有调度任务"""
        # 清除现有调度
        schedule.clear()
        
        for i, email_schedule in enumerate(self.schedules):
            if not email_schedule.enabled:
                continue
                
            logger.info(f"设置调度 {i}: {email_schedule.topic} at {email_schedule.schedule_time}")
            
            # 创建异步任务的包装函数
            def create_job(schedule_config):
                def job():
                    # 在新的事件循环中运行异步任务
                    try:
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        loop.run_until_complete(self.send_scheduled_email(schedule_config))
                        loop.close()
                    except Exception as e:
                        logger.error(f"调度任务执行错误: {e}")
                return job
            
            # 根据频率设置调度
            if email_schedule.frequency == "daily":
                schedule.every().day.at(email_schedule.schedule_time).do(
                    create_job(email_schedule)
                )
            elif email_schedule.frequency == "weekly":
                schedule.every().monday.at(email_schedule.schedule_time).do(
                    create_job(email_schedule)
                )
            elif email_schedule.frequency == "monthly":
                # 每月1号发送
                def monthly_job():
                    if datetime.now().day == 1:
                        create_job(email_schedule)()
                
                schedule.every().day.at(email_schedule.schedule_time).do(monthly_job)
        
        logger.info(f"设置了 {len([s for s in self.schedules if s.enabled])} 个活跃调度")
    
    async def start_service(self):
        """启动定时邮件服务"""
        logger.info("启动简化定时邮件服务...")
        
        # 初始化代理
        await self.initialize_agents()
        
        # 设置调度
        self.setup_schedules()
        self.running = True
        
        logger.info("定时邮件服务已启动，等待调度执行...")
        
        # 运行调度循环
        try:
            while self.running:
                schedule.run_pending()
                await asyncio.sleep(60)  # 每分钟检查一次
        except (KeyboardInterrupt, asyncio.CancelledError):
            logger.info("收到停止信号，正在关闭服务...")
            self.stop_service()
        except Exception as e:
            logger.error(f"调度循环出错: {e}")
            self.stop_service()
            raise
    
    def stop_service(self):
        """停止定时邮件服务"""
        logger.info("停止定时邮件服务...")
        self.running = False
        schedule.clear()
    
    def list_schedules(self):
        """列出所有邮件调度"""
        print("\n📧 邮件调度配置:")
        print("=" * 60)
        
        if not self.schedules:
            print("暂无邮件调度配置")
            return
        
        for i, schedule_config in enumerate(self.schedules):
            status = "✅ 启用" if schedule_config.enabled else "❌ 禁用"
            print(f"{i}. {status}")
            print(f"   主题: {schedule_config.topic}")
            print(f"   收件人: {schedule_config.recipient}")
            print(f"   时间: {schedule_config.schedule_time} ({schedule_config.frequency})")
            print(f"   邮件主题: {schedule_config.subject_template}")
            print()


async def main():
    """主函数 - 交互式管理界面"""
    service = SimpleScheduledEmailService()
    
    print("🤖 AutoGen v0.4+ 简化定时邮件服务")
    print("=" * 50)
    
    while True:
        print("\n📋 可用操作:")
        print("1. 查看邮件调度")
        print("2. 添加邮件调度")
        print("3. 编辑邮件调度")
        print("4. 删除邮件调度")
        print("5. 启用/禁用调度")
        print("6. 启动定时服务")
        print("7. 测试发送邮件")
        print("0. 退出")
        
        try:
            choice = input("\n请选择操作 (0-7): ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n👋 检测到退出信号，正在关闭服务...")
            service.stop_service()
            break
        
        if choice == "0":
            service.stop_service()
            break
        elif choice == "1":
            service.list_schedules()
        elif choice == "2":
            topic = input("请输入主题关键词: ").strip()
            recipient = input("请输入收件人邮箱: ").strip()
            schedule_time = input("请输入发送时间 (HH:MM): ").strip()
            frequency = input("请输入频率 (daily/weekly/monthly) [daily]: ").strip() or "daily"
            
            service.add_schedule(topic, recipient, schedule_time, frequency)
            print("✅ 邮件调度已添加")
        elif choice == "3":
            # 编辑邮件调度
            if not service.schedules:
                print("❌ 暂无邮件调度配置")
                continue
                
            service.list_schedules()
            try:
                index = int(input("请输入要编辑的调度编号: "))
                if 0 <= index < len(service.schedules):
                    schedule = service.schedules[index]
                    print(f"\n📝 编辑调度: {schedule.topic}")
                    print("直接回车保持原值，输入新值进行修改")
                    
                    # 获取新的配置值
                    new_topic = input(f"主题关键词 [{schedule.topic}]: ").strip()
                    new_recipient = input(f"收件人邮箱 [{schedule.recipient}]: ").strip()
                    new_schedule_time = input(f"发送时间 [{schedule.schedule_time}]: ").strip()
                    new_frequency = input(f"频率 [{schedule.frequency}]: ").strip()
                    new_subject_template = input(f"邮件主题模板 [{schedule.subject_template}]: ").strip()
                    
                    # 构建更新参数
                    update_params = {}
                    if new_topic:
                        update_params['topic'] = new_topic
                    if new_recipient:
                        update_params['recipient'] = new_recipient
                    if new_schedule_time:
                        update_params['schedule_time'] = new_schedule_time
                    if new_frequency:
                        update_params['frequency'] = new_frequency
                    if new_subject_template:
                        update_params['subject_template'] = new_subject_template
                    
                    if update_params:
                        if service.edit_schedule(index, **update_params):
                            print("✅ 邮件调度已更新")
                        else:
                            print("❌ 更新失败")
                    else:
                        print("🔄 未进行任何修改")
                else:
                    print("❌ 无效的编号")
            except ValueError:
                print("❌ 无效的编号")
        elif choice == "4":
            # 删除邮件调度
            if not service.schedules:
                print("❌ 暂无邮件调度配置")
                continue
                
            service.list_schedules()
            try:
                index = int(input("请输入要删除的调度编号: "))
                if 0 <= index < len(service.schedules):
                    schedule = service.schedules[index]
                    confirm = input(f"确认删除调度 '{schedule.topic} -> {schedule.recipient}' 吗? (y/N): ").strip().lower()
                    if confirm in ['y', 'yes', '是']:
                        if service.delete_schedule(index):
                            print("✅ 邮件调度已删除")
                        else:
                            print("❌ 删除失败")
                    else:
                        print("🚫 已取消删除")
                else:
                    print("❌ 无效的编号")
            except ValueError:
                print("❌ 无效的编号")
        elif choice == "5":
            service.list_schedules()
            try:
                index = int(input("请输入要切换状态的调度编号: "))
                service.toggle_schedule(index)
                print("✅ 调度状态已切换")
            except ValueError:
                print("❌ 无效的编号")
        elif choice == "6":
            print("🚀 启动定时邮件服务...")
            print("按 Ctrl+C 停止服务")
            try:
                await service.start_service()
            except (KeyboardInterrupt, asyncio.CancelledError):
                service.stop_service()
                print("\n✅ 服务已停止")
            except Exception as e:
                logger.error(f"服务运行时出错: {e}")
                service.stop_service()
                print("\n❌ 服务异常停止")
        elif choice == "7":
            if service.schedules:
                service.list_schedules()
                try:
                    index = int(input("请输入要测试的调度编号: "))
                    if 0 <= index < len(service.schedules):
                        print("📧 正在测试发送邮件...")
                        await service.send_scheduled_email(service.schedules[index])
                        print("✅ 测试邮件发送完成")
                    else:
                        print("❌ 无效的编号")
                except ValueError:
                    print("❌ 无效的编号")
            else:
                print("❌ 暂无邮件调度配置")
        else:
            print("❌ 无效的选择")


if __name__ == "__main__":
    asyncio.run(main())

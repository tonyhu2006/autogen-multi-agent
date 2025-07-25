#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
定时研究报告系统
每天定时发送预设主题的研究报告到指定邮箱
"""
import asyncio
import json
import os
import schedule
import time
import logging
from datetime import datetime, timedelta
from dotenv import load_dotenv
from main_local import LocalMultiAgentSystem

# 加载环境变量
load_dotenv('.env.local')

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scheduled_research.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ScheduledResearchSystem:
    """定时研究报告系统"""
    
    def __init__(self, config_file: str = "research_schedule.json"):
        self.config_file = config_file
        self.system = LocalMultiAgentSystem()
        self.load_config()
    
    def load_config(self):
        """加载定时任务配置"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
            else:
                # 创建默认配置
                self.config = {
                    "schedule_time": "09:00",  # 每天9点发送
                    "timezone": "Asia/Shanghai",
                    "research_topics": [
                        {
                            "id": 1,
                            "topic": "人工智能最新发展",
                            "description": "关注AI技术的最新突破和趋势",
                            "enabled": True,
                            "recipients": [
                                {
                                    "email": "your-email@example.com",
                                    "name": "研究员"
                                }
                            ]
                        },
                        {
                            "id": 2,
                            "topic": "机器学习技术进展",
                            "description": "机器学习算法和应用的最新进展",
                            "enabled": False,
                            "recipients": [
                                {
                                    "email": "your-email@example.com", 
                                    "name": "技术专家"
                                }
                            ]
                        }
                    ],
                    "email_settings": {
                        "subject_prefix": "📊 每日研究报告",
                        "include_date": True,
                        "max_retries": 3
                    }
                }
                self.save_config()
            
            logger.info(f"配置加载成功: {len(self.config['research_topics'])} 个研究主题")
        except Exception as e:
            logger.error(f"配置加载失败: {e}")
            self.config = {}
    
    def save_config(self):
        """保存配置到文件"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            logger.info("配置保存成功")
        except Exception as e:
            logger.error(f"配置保存失败: {e}")
    
    async def generate_daily_report(self, topic_config: dict):
        """生成单个主题的每日报告"""
        try:
            topic = topic_config["topic"]
            recipients = topic_config["recipients"]
            
            logger.info(f"开始生成报告: {topic}")
            
            # 为每个收件人生成报告
            for recipient in recipients:
                email = recipient["email"]
                name = recipient.get("name", "")
                
                logger.info(f"为 {email} 生成报告...")
                
                # 处理研究请求
                result = await self.system.process_research_request(
                    query=topic,
                    send_email=True,
                    recipient=email,
                    recipient_name=name
                )
                
                if "error" in result:
                    logger.error(f"报告生成失败 ({email}): {result['error']}")
                else:
                    logger.info(f"报告生成成功: {email}")
                    
                    # 检查是否有邮件草稿
                    if "email_draft" in result:
                        # 发送真实邮件
                        sender_email = os.getenv("SENDER_EMAIL")
                        sender_password = os.getenv("SENDER_PASSWORD")
                        
                        if sender_email and sender_password:
                            # 自定义邮件主题
                            date_str = datetime.now().strftime("%Y-%m-%d")
                            subject_prefix = self.config.get("email_settings", {}).get("subject_prefix", "📊 每日研究报告")
                            custom_subject = f"{subject_prefix} - {topic} ({date_str})"
                            
                            email_result = self.system.email_agent.send_real_email(
                                recipient=email,
                                subject=custom_subject,
                                body=result['email_draft']['body'],
                                sender_email=sender_email,
                                sender_password=sender_password
                            )
                            
                            if email_result.get("success"):
                                logger.info(f"✅ 邮件发送成功: {email}")
                            else:
                                logger.error(f"❌ 邮件发送失败: {email} - {email_result.get('error')}")
                        else:
                            logger.error("邮件凭据未配置，无法发送邮件")
                
                # 避免请求过于频繁
                await asyncio.sleep(2)
                
        except Exception as e:
            logger.error(f"生成报告时出错: {e}")
    
    async def run_daily_reports(self):
        """运行每日报告任务"""
        logger.info("🚀 开始执行每日研究报告任务")
        
        try:
            enabled_topics = [
                topic for topic in self.config.get("research_topics", [])
                if topic.get("enabled", False)
            ]
            
            if not enabled_topics:
                logger.warning("没有启用的研究主题")
                return
            
            logger.info(f"发现 {len(enabled_topics)} 个启用的研究主题")
            
            # 为每个启用的主题生成报告
            for topic_config in enabled_topics:
                await self.generate_daily_report(topic_config)
                # 主题间间隔
                await asyncio.sleep(5)
            
            logger.info("✅ 每日研究报告任务完成")
            
        except Exception as e:
            logger.error(f"每日报告任务执行失败: {e}")
    
    def schedule_daily_reports(self):
        """设置定时任务"""
        schedule_time = self.config.get("schedule_time", "09:00")
        
        # 设置每日定时任务
        schedule.every().day.at(schedule_time).do(
            lambda: asyncio.run(self.run_daily_reports())
        )
        
        logger.info(f"📅 定时任务已设置: 每天 {schedule_time} 执行")
        logger.info("定时任务系统启动，按 Ctrl+C 停止")
    
    def run_scheduler(self):
        """运行调度器"""
        self.schedule_daily_reports()
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # 每分钟检查一次
        except KeyboardInterrupt:
            logger.info("定时任务系统已停止")
    
    def add_research_topic(self, topic: str, description: str = "", recipients: list = None):
        """添加新的研究主题"""
        if recipients is None:
            recipients = [{"email": os.getenv("DEFAULT_RECIPIENTS", ""), "name": ""}]
        
        new_id = max([t.get("id", 0) for t in self.config.get("research_topics", [])], default=0) + 1
        
        new_topic = {
            "id": new_id,
            "topic": topic,
            "description": description,
            "enabled": True,
            "recipients": recipients
        }
        
        if "research_topics" not in self.config:
            self.config["research_topics"] = []
        
        self.config["research_topics"].append(new_topic)
        self.save_config()
        
        logger.info(f"新增研究主题: {topic}")
        return new_id
    
    def toggle_topic(self, topic_id: int, enabled: bool = None):
        """启用/禁用研究主题"""
        for topic in self.config.get("research_topics", []):
            if topic["id"] == topic_id:
                if enabled is None:
                    topic["enabled"] = not topic.get("enabled", False)
                else:
                    topic["enabled"] = enabled
                self.save_config()
                status = "启用" if topic["enabled"] else "禁用"
                logger.info(f"主题 {topic_id} 已{status}: {topic['topic']}")
                return True
        
        logger.warning(f"未找到主题 ID: {topic_id}")
        return False
    
    def list_topics(self):
        """列出所有研究主题"""
        topics = self.config.get("research_topics", [])
        if not topics:
            print("📋 暂无研究主题")
            return
        
        print("📋 研究主题列表:")
        print("-" * 80)
        for topic in topics:
            status = "✅ 启用" if topic.get("enabled", False) else "❌ 禁用"
            recipients_count = len(topic.get("recipients", []))
            print(f"ID: {topic['id']} | {status} | 收件人: {recipients_count}个")
            print(f"主题: {topic['topic']}")
            print(f"描述: {topic.get('description', '无描述')}")
            print("-" * 80)

def main():
    """主函数"""
    import sys
    
    scheduler = ScheduledResearchSystem()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "run":
            # 立即运行一次报告任务
            asyncio.run(scheduler.run_daily_reports())
        elif command == "list":
            # 列出所有主题
            scheduler.list_topics()
        elif command == "add" and len(sys.argv) > 2:
            # 添加新主题
            topic = sys.argv[2]
            description = sys.argv[3] if len(sys.argv) > 3 else ""
            topic_id = scheduler.add_research_topic(topic, description)
            print(f"✅ 已添加研究主题 (ID: {topic_id}): {topic}")
        elif command == "enable" and len(sys.argv) > 2:
            # 启用主题
            topic_id = int(sys.argv[2])
            scheduler.toggle_topic(topic_id, True)
        elif command == "disable" and len(sys.argv) > 2:
            # 禁用主题
            topic_id = int(sys.argv[2])
            scheduler.toggle_topic(topic_id, False)
        elif command == "schedule":
            # 启动定时任务
            scheduler.run_scheduler()
        else:
            print("用法:")
            print("  python scheduled_research.py run        # 立即运行一次")
            print("  python scheduled_research.py list       # 列出所有主题")
            print("  python scheduled_research.py add <主题> [描述]  # 添加主题")
            print("  python scheduled_research.py enable <ID> # 启用主题")
            print("  python scheduled_research.py disable <ID> # 禁用主题")
            print("  python scheduled_research.py schedule   # 启动定时任务")
    else:
        # 默认启动定时任务
        scheduler.run_scheduler()

if __name__ == "__main__":
    main()

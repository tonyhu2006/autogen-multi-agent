#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
直接 SMTP 邮件发送测试
====================

直接测试 SMTP 邮件发送功能，不依赖 AI 生成的指令
"""

import os
import sys
import asyncio
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入环境配置
from dotenv import load_dotenv
load_dotenv('.env.local')
load_dotenv('.env')

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def send_smtp_email_direct(
    to_email: str,
    subject: str,
    body: str,
    sender_email: str = None,
    sender_password: str = None,
    sender_name: str = None,
    smtp_server: str = None,
    smtp_port: int = None
):
    """直接发送 SMTP 邮件"""
    try:
        # 获取配置
        sender_email = sender_email or os.getenv("SENDER_EMAIL")
        sender_password = sender_password or os.getenv("SENDER_PASSWORD")
        sender_name = sender_name or os.getenv("SENDER_NAME", "AI研究系统")
        smtp_server = smtp_server or os.getenv("SMTP_SERVER", "smtp.gmail.com")
        smtp_port = smtp_port or int(os.getenv("SMTP_PORT", "587"))
        
        logger.info(f"SMTP 配置:")
        logger.info(f"  发件人: {sender_email}")
        logger.info(f"  收件人: {to_email}")
        logger.info(f"  SMTP服务器: {smtp_server}:{smtp_port}")
        logger.info(f"  发件人名称: {sender_name}")
        
        # 验证配置
        if not sender_email or not sender_password:
            raise ValueError("缺少发件人邮箱或密码配置")
        
        # 创建邮件消息
        msg = MIMEMultipart()
        msg['From'] = f"{sender_name} <{sender_email}>"
        msg['To'] = to_email
        msg['Subject'] = subject
        
        # 添加邮件正文
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        
        logger.info("正在连接 SMTP 服务器...")
        
        # 连接SMTP服务器并发送
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            logger.info("启用 TLS 加密...")
            server.starttls()  # 启用TLS加密
            
            logger.info("正在登录...")
            server.login(sender_email, sender_password)
            
            logger.info("正在发送邮件...")
            text = msg.as_string()
            server.sendmail(sender_email, to_email, text)
            
            logger.info("✅ 邮件发送成功！")
            return True
            
    except Exception as e:
        logger.error(f"❌ SMTP 邮件发送失败: {e}")
        return False


async def test_smtp_configuration():
    """测试 SMTP 配置"""
    logger.info("🔧 测试 SMTP 配置...")
    
    # 检查环境变量
    required_vars = ["SENDER_EMAIL", "SENDER_PASSWORD"]
    missing_vars = []
    
    for var in required_vars:
        value = os.getenv(var)
        if not value:
            missing_vars.append(var)
        else:
            # 隐藏密码显示
            display_value = value if var != "SENDER_PASSWORD" else "*" * len(value)
            logger.info(f"  {var}: {display_value}")
    
    if missing_vars:
        logger.error(f"❌ 缺少必要的环境变量: {missing_vars}")
        return False
    
    logger.info("✅ SMTP 配置检查通过")
    return True


async def main():
    """主测试函数"""
    logger.info("🚀 开始直接 SMTP 邮件发送测试...")
    
    # 测试配置
    if not await test_smtp_configuration():
        return
    
    # 构建测试邮件
    current_date = datetime.now().strftime("%Y年%m月%d日")
    subject = f"AutoGen v0.4+ 邮件发送测试 - {current_date}"
    
    body = f"""
# AutoGen v0.4+ 邮件发送测试

## 📧 测试信息

这是一封由 AutoGen v0.4+ 多代理 AI 系统发送的测试邮件。

**发送时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**测试目的**: 验证 SMTP 邮件发送功能  
**系统版本**: AutoGen v0.4+ with Gemini Balance  

## 🔧 技术详情

- **SMTP 服务器**: {os.getenv("SMTP_SERVER", "smtp.gmail.com")}
- **端口**: {os.getenv("SMTP_PORT", "587")}
- **加密**: TLS
- **发件人**: {os.getenv("SENDER_EMAIL")}

## 📊 测试结果

如果您收到这封邮件，说明 SMTP 邮件发送功能正常工作！

---

*本邮件由 AutoGen v0.4+ 多代理 AI 系统自动生成和发送*  
*如有问题，请检查系统日志*
"""
    
    # 发送测试邮件 - 从环境变量读取收件人
    recipient = os.getenv("TEST_RECIPIENT_EMAIL", "your-email@example.com")
    logger.info(f"📧 发送测试邮件到: {recipient}")
    
    success = await send_smtp_email_direct(
        to_email=recipient,
        subject=subject,
        body=body
    )
    
    if success:
        logger.info("🎉 SMTP 邮件发送测试成功！")
        logger.info(f"请检查您的邮箱: {recipient}")
    else:
        logger.error("💥 SMTP 邮件发送测试失败！")
        logger.error("请检查:")
        logger.error("1. 邮箱账号和密码是否正确")
        logger.error("2. 是否启用了应用专用密码（Gmail）")
        logger.error("3. 网络连接是否正常")
        logger.error("4. SMTP 服务器设置是否正确")


if __name__ == "__main__":
    asyncio.run(main())

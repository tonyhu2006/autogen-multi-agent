#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
邮件配置初始化脚本
==================

帮助用户创建个人的 email_schedules.json 配置文件
"""

import os
import json
import shutil
from pathlib import Path

def setup_email_config():
    """设置邮件配置文件"""
    config_file = "email_schedules.json"
    template_file = "email_schedules.json.template"
    
    # 检查是否已存在配置文件
    if os.path.exists(config_file):
        print(f"✅ {config_file} 已存在")
        return
    
    # 检查模板文件是否存在
    if not os.path.exists(template_file):
        print(f"❌ 模板文件 {template_file} 不存在")
        return
    
    # 复制模板文件
    try:
        shutil.copy2(template_file, config_file)
        print(f"✅ 已创建 {config_file} 配置文件")
        print(f"📝 请编辑 {config_file} 文件，配置您的邮件调度:")
        print("   1. 将 'your-email@example.com' 替换为实际收件人邮箱")
        print("   2. 根据需要调整主题、时间和频率")
        print("   3. 将需要的调度设置为 'enabled': true")
        print()
        print("⚠️  注意: 此文件包含个人邮箱信息，不会被提交到 Git")
        
    except Exception as e:
        print(f"❌ 创建配置文件失败: {e}")

if __name__ == "__main__":
    print("🚀 AutoGen v0.4+ 邮件配置初始化")
    print("=" * 50)
    setup_email_config()

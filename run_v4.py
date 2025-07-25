#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AutoGen多代理AI系统 v0.4 启动脚本
===============================

快速启动和管理AutoGen v0.4+多代理AI系统
"""

import os
import sys
import asyncio
import argparse
import logging
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 导入主程序
from main_v4 import AutoGenMultiAgentSystem, interactive_mode, print_help


def setup_environment():
    """设置环境"""
    # 加载环境变量（正确顺序：先加载通用配置，再加载本地配置）
    from dotenv import load_dotenv
    load_dotenv('.env')        # 先加载通用配置
    load_dotenv('.env.local', override=True)  # 再加载本地配置（强制覆盖，优先级更高）
    
    # 检查必要的环境变量
    required_vars = ["OPENAI_API_KEY"]
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ 缺少必要的环境变量: {', '.join(missing_vars)}")
        print("请在 .env 文件中设置这些变量")
        return False
    
    # 检查可选环境变量
    optional_vars = {
        "BRAVE_API_KEY": "Brave搜索功能",
        "SEARCH_ENGINE_BASE_URL": "SearXNG搜索功能",
        "SENDER_EMAIL": "SMTP邮件发送功能"
    }
    
    # 显示配置状态
    print("\n🔧 环境配置状态:")
    print(f"  ✅ OpenAI API: {os.getenv('OPENAI_API_KEY')[:10]}...")
    print(f"  🌐 OpenAI Base URL: {os.getenv('OPENAI_BASE_URL', '未设置')}")
    print(f"  🤖 模型: {os.getenv('OPENAI_MODEL', 'gpt-4o')}")
    
    for var, desc in optional_vars.items():
        value = os.getenv(var)
        if value:
            print(f"  ✅ {desc}: 已配置")
        else:
            print(f"  ⚠️  {desc}: 未配置")
    
    print()
    
    return True


async def run_interactive():
    """运行交互式模式"""
    print("🚀 启动交互式模式...")
    await interactive_mode()


async def run_batch_tasks(tasks_file: str):
    """批量执行任务"""
    try:
        import json
        
        print(f"📋 从文件加载任务: {tasks_file}")
        
        with open(tasks_file, 'r', encoding='utf-8') as f:
            tasks = json.load(f)
        
        system = AutoGenMultiAgentSystem()
        await system.initialize()
        
        print(f"🔄 开始执行 {len(tasks)} 个任务...")
        
        results = []
        for i, task in enumerate(tasks, 1):
            print(f"\n📝 执行任务 {i}/{len(tasks)}: {task.get('description', task)[:50]}...")
            
            if isinstance(task, dict):
                task_description = task.get('description', str(task))
            else:
                task_description = str(task)
            
            result = await system.process_user_request(task_description)
            results.append({
                "task": task,
                "result": result
            })
            
            if result["success"]:
                print(f"✅ 任务 {i} 完成")
            else:
                print(f"❌ 任务 {i} 失败: {result.get('error', '未知错误')}")
        
        # 保存结果
        output_file = f"batch_results_{int(asyncio.get_event_loop().time())}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        print(f"📊 批量执行完成，结果保存到: {output_file}")
        
        await system.shutdown()
        
    except Exception as e:
        print(f"❌ 批量执行失败: {e}")


async def run_demo():
    """运行演示模式"""
    print("🎭 启动演示模式...")
    
    demo_tasks = [
        "你好，请介绍一下AutoGen v0.4多代理系统的功能",
        "研究人工智能在教育领域的最新应用",
        "帮我写一封关于项目进展的邮件，收件人是团队成员",
        "分析当前AI技术发展的趋势"
    ]
    
    system = AutoGenMultiAgentSystem()
    await system.initialize()
    
    print("🎯 演示任务列表:")
    for i, task in enumerate(demo_tasks, 1):
        print(f"  {i}. {task}")
    
    print("\n🔄 开始执行演示任务...")
    
    for i, task in enumerate(demo_tasks, 1):
        print(f"\n{'='*60}")
        print(f"📝 演示任务 {i}: {task}")
        print("="*60)
        
        result = await system.process_user_request(task)
        
        if result["success"]:
            print(f"🤖 AI回复:\n{result['result']}")
        else:
            print(f"❌ 错误: {result.get('error', '未知错误')}")
        
        print("\n⏸️  按 Enter 继续下一个任务...")
        input()
    
    print("\n🎉 演示完成！")
    
    # 显示系统状态
    status = await system.get_system_status()
    print(f"\n📊 系统状态:")
    print(f"  - 总任务数: {status['coordination_metrics']['tasks_completed'] + status['coordination_metrics']['tasks_failed']}")
    print(f"  - 成功任务: {status['coordination_metrics']['tasks_completed']}")
    print(f"  - 失败任务: {status['coordination_metrics']['tasks_failed']}")
    print(f"  - 代理数量: {status['coordination_metrics']['agent_status']['total_agents']}")
    print(f"  - 团队数量: {status['coordination_metrics']['team_status']['total_teams']}")
    
    await system.shutdown()


async def test_system():
    """测试系统功能"""
    print("🧪 启动系统测试...")
    
    try:
        # 检查是否有真实API密钥
        import os
        api_key = os.getenv("OPENAI_API_KEY")
        base_url = os.getenv("OPENAI_BASE_URL")
        
        # 如果有base_url设置，认为是真实环境
        if not api_key or (api_key == "test_key_for_demo" and not base_url):
            print("⚠️  检测到测试环境，跳过API调用测试")
            print("1️⃣ 测试基本导入...")
            from main_v4 import AutoGenMultiAgentSystem
            print("✅ 导入测试通过")
            
            print("2️⃣ 测试类创建...")
            system = AutoGenMultiAgentSystem()
            print("✅ 类创建测试通过")
            
            print("3️⃣ 测试组件导入...")
            from agents.base_agent_v4 import EnhancedAssistantAgent
            from agents.research_agent_v4 import EnhancedResearchAgent
            from agents.email_agent_v4 import EnhancedEmailAgent
            from teams.team_coordinator_v4 import TeamCoordinator
            print("✅ 组件导入测试通过")
            
            print("\n🎉 基本系统测试通过！")
            print("📝 请配置真实API密钥后进行完整测试")
            return True
        
        # 如果有真实API密钥，进行完整测试
        from main_v4 import AutoGenMultiAgentSystem
        system = AutoGenMultiAgentSystem()
        
        print("1️⃣ 测试系统初始化...")
        await system.initialize()
        print("✅ 初始化测试通过")
        
        print("2️⃣ 测试简单对话...")
        result = await system.process_user_request("你好")
        assert result["success"], f"对话测试失败: {result}"
        print("✅ 对话测试通过")
        
        print("3️⃣ 测试研究功能...")
        result = await system.process_user_request("研究Python编程语言的特点")
        assert result["success"], f"研究测试失败: {result}"
        print("✅ 研究测试通过")
        
        print("4️⃣ 测试邮件功能...")
        result = await system.process_user_request("生成一封测试邮件")
        assert result["success"], f"邮件测试失败: {result}"
        print("✅ 邮件测试通过")
        
        print("5️⃣ 测试系统状态...")
        status = await system.get_system_status()
        assert status["status"] == "active", f"状态测试失败: {status}"
        print("✅ 状态测试通过")
        
        await system.shutdown()
        print("✅ 关闭测试通过")
        
        print("\n🎉 所有测试通过！系统运行正常")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        if "verbose" in globals():
            import traceback
            traceback.print_exc()
        return False
    
    return True


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="AutoGen多代理AI系统 v0.4 启动器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python run_v4.py                    # 交互式模式
  python run_v4.py --demo             # 演示模式
  python run_v4.py --test             # 测试模式
  python run_v4.py --batch tasks.json # 批量执行模式
        """
    )
    
    parser.add_argument(
        "--mode", "-m",
        choices=["interactive", "demo", "test", "batch"],
        default="interactive",
        help="运行模式 (默认: interactive)"
    )
    
    parser.add_argument(
        "--batch", "-b",
        type=str,
        help="批量任务文件路径 (JSON格式)"
    )
    
    parser.add_argument(
        "--demo", "-d",
        action="store_true",
        help="运行演示模式"
    )
    
    parser.add_argument(
        "--test", "-t",
        action="store_true",
        help="运行测试模式"
    )
    
    parser.add_argument(
        "--help-system", "-hs",
        action="store_true",
        help="显示系统帮助信息"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="详细输出模式"
    )
    
    args = parser.parse_args()
    
    # 设置日志级别
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # 显示系统帮助
    if args.help_system:
        print_help()
        return
    
    # 检查环境
    if not setup_environment():
        sys.exit(1)
    
    print("🤖 AutoGen多代理AI系统 v0.4")
    print("=" * 40)
    
    try:
        # 确定运行模式
        if args.test:
            asyncio.run(test_system())
        elif args.demo:
            asyncio.run(run_demo())
        elif args.batch:
            asyncio.run(run_batch_tasks(args.batch))
        else:
            asyncio.run(run_interactive())
            
    except KeyboardInterrupt:
        print("\n👋 程序被用户中断")
    except Exception as e:
        print(f"❌ 程序错误: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

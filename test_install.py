#!/usr/bin/env python
"""
测试Pydify安装的简单脚本。
运行方式：
    python test_install.py
"""

try:
    import pydify

    print(f"Pydify 安装成功! 版本: {pydify.__version__}")

    # 检查是否可以导入所有客户端类
    from pydify import (
        AgentClient,
        ChatbotClient,
        ChatflowClient,
        TextGenerationClient,
        WorkflowClient,
    )

    print("所有客户端类导入成功！")
    print("\n可用的客户端类:")
    print("- ChatbotClient: 聊天机器人应用")
    print("- TextGenerationClient: 文本生成应用")
    print("- AgentClient: 智能代理应用")
    print("- WorkflowClient: 工作流应用")
    print("- ChatflowClient: 对话流应用")

except ImportError as e:
    print(f"导入失败: {e}")
    print("请确认已经正确安装Pydify:")
    print("    pip install pydify")
    print("如果还有问题，请查看项目文档或提交问题。")

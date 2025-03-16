#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Pydify 基本用法示例
"""

import os
import sys
import time

# 将父目录添加到 Python 路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from pydify import create_client, DifyException


def main():
    """示例脚本主函数"""
    
    # 从环境变量获取 API 密钥或直接设置
    # 使用前请设置环境变量 DIFY_API_KEY 或在此处替换
    api_key = os.environ.get("DIFY_API_KEY", "your_api_key_here")
    
    # 创建客户端
    client = create_client(api_key=api_key)
    
    try:
        # 获取应用信息
        print("获取应用信息...")
        app_info = client.info.get_app_info()
        print(f"应用名称: {app_info.data.get('name', '未知')}")
        print(f"应用描述: {app_info.data.get('description', '无描述')}")
        print()
        
        # 发送聊天消息
        user_id = f"example_user_{int(time.time())}"
        query = "你好，请介绍一下Dify平台的主要功能"
        
        print(f"发送聊天消息: '{query}'")
        print("等待响应中...")
        
        # 使用流式响应
        stream = client.chat.create_message(
            query=query,
            user=user_id,
            response_mode="streaming"
        )
        
        print("\n回答:")
        # 逐步打印回答
        full_answer = ""
        for event in stream:
            if event.get("type") == "message":
                chunk = event.get("answer", "")
                full_answer += chunk
                print(chunk, end="", flush=True)
        print("\n")
        
        # 获取建议问题
        print("获取会话列表...")
        conversations = client.conversation.list_conversations(
            user=user_id,
            limit=5
        )
        
        if conversations.data.get("data"):
            conv = conversations.data["data"][0]
            conv_id = conv.get("id")
            print(f"会话ID: {conv_id}")
            print(f"会话标题: {conv.get('name', '无标题')}")
            
            # 获取会话历史
            print("\n获取会话历史...")
            messages = client.chat.list_messages(
                conversation_id=conv_id,
                user=user_id
            )
            
            if messages.data.get("data"):
                message = messages.data["data"][0]
                message_id = message.get("id")
                
                # 获取建议问题
                print("\n获取建议问题...")
                suggestions = client.chat.get_suggested_questions(
                    message_id=message_id,
                    user=user_id
                )
                
                if suggestions.data.get("data"):
                    print("建议问题:")
                    for i, question in enumerate(suggestions.data["data"], 1):
                        print(f"{i}. {question}")
                else:
                    print("没有建议问题")
        else:
            print("没有会话记录")
            
    except DifyException as e:
        print(f"错误: {e}")
    finally:
        # 关闭客户端会话
        client.close()


if __name__ == "__main__":
    main() 
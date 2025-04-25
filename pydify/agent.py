"""
Pydify - Dify Agent应用客户端

此模块提供与Dify Agent应用API交互的客户端。
Agent对话型应用能够迭代式的规划推理、自主工具调用，直至完成任务目标的智能助手。
"""

import json
import mimetypes
import os
from typing import Any, BinaryIO, Dict, Generator, List, Optional, Tuple, Union

from .chatbot import ChatbotClient
from .common import DifyBaseClient, DifyType


class AgentEvent:
    """事件类型枚举

    定义了Dify Agent API中可能的事件类型，用于处理流式响应中的事件。
    """

    MESSAGE = "message"  # LLM返回文本块事件，包含分块输出的文本内容
    AGENT_MESSAGE = "agent_message"  # Agent模式下返回文本块事件，包含分块输出的文本内容
    AGENT_THOUGHT = "agent_thought"  # Agent思考步骤事件，包含工具调用相关信息
    MESSAGE_FILE = "message_file"  # 文件事件，表示有新文件需要展示
    MESSAGE_END = "message_end"  # 消息结束事件，表示流式返回结束
    TTS_MESSAGE = "tts_message"  # TTS音频流事件，包含base64编码的音频块
    TTS_MESSAGE_END = "tts_message_end"  # TTS音频流结束事件
    MESSAGE_REPLACE = "message_replace"  # 消息内容替换事件，用于内容审查后的替换
    ERROR = "error"  # 流式输出过程中出现的异常事件
    PING = "ping"  # 保持连接存活的ping事件，每10秒一次


class AgentClient(ChatbotClient):
    """Dify Agent应用客户端类。

    提供与Dify Agent应用API交互的方法，包括发送消息、获取历史消息、管理会话、
    上传文件、语音转文字、文字转语音等功能。Agent应用支持迭代式规划推理和自主工具调用。
    """

    type = DifyType.Agent

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.task_id = None

    def send_message(
        self,
        query: str,
        user: str,
        response_mode: str = "streaming",
        inputs: Dict[str, Any] = None,
        conversation_id: str = None,
        files: List[Dict[str, Any]] = None,
        auto_generate_name: bool = True,
        **kwargs,  # 添加kwargs参数，用于接收额外的请求参数
    ) -> Union[Generator[Dict[str, Any], None, None], Dict[str, Any]]:
        """
        发送对话消息，创建会话消息。在Agent模式下，只支持streaming流式模式。

        Args:
            query (str): 用户输入/提问内容
            user (str): 用户标识，用于定义终端用户的身份
            response_mode (str, optional): 响应模式，只支持'streaming'。默认为'streaming'
            inputs (Dict[str, Any], optional): App定义的各变量值。默认为None
            conversation_id (str, optional): 会话ID，基于之前的聊天记录继续对话时需提供。默认为None
            files (List[Dict[str, Any]], optional): 要包含在消息中的文件列表，每个文件为一个字典。默认为None
            auto_generate_name (bool, optional): 是否自动生成会话标题。默认为True
            **kwargs: 传递给底层API请求的额外参数，如timeout, max_retries等

        Returns:
            Generator[Dict[str, Any], None, None]: 返回字典生成器

        Raises:
            ValueError: 当提供了无效的参数时
            DifyAPIError: 当API请求失败时
        """
        if response_mode != "streaming":
            raise ValueError("Agent mode only supports streaming response mode")

        payload = {
            "query": query,
            "user": user,
            "response_mode": "streaming",
            "auto_generate_name": auto_generate_name,
            "inputs": inputs or {},  # 确保inputs参数总是存在，如果未提供则使用空字典
        }

        if conversation_id:
            payload["conversation_id"] = conversation_id

        if files:
            payload["files"] = files

        endpoint = "chat-messages"

        return self.post_stream(endpoint, json_data=payload, **kwargs)  # 传递额外参数

    def stop_task(self, task_id: str, user: str) -> Dict[str, Any]:
        """
        停止正在进行的响应流。此方法仅在流式模式下有效。

        Args:
            task_id (str): 任务唯一标识,可从流式响应的数据块中获取
            user (str): 用户唯一标识,需要与发送消息时的user参数保持一致

        Returns:
            Dict[str, Any]: 停止响应的结果,格式如下:
            {
                "result": "success"  # 表示成功停止响应
            }

        Raises:
            requests.HTTPError: API请求失败时抛出此异常,包含具体的错误信息
            DifyAPIError: Dify服务端返回错误时抛出此异常
        """
        endpoint = f"chat-messages/{task_id}/stop"
        payload = {"user": user}
        return self.post(endpoint, json_data=payload)

    def get_meta(self) -> Dict[str, Any]:
        """
        获取应用Meta信息，用于获取工具icon等。

        Returns:
            Dict[str, Any]: 应用Meta信息

        Raises:
            requests.HTTPError: 当API请求失败时
        """
        return self.get("meta")

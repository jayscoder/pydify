"""
Pydify - Dify Text Generation应用客户端

此模块提供与Dify Text Generation应用API交互的客户端。
Text Generation文本生成应用无会话支持，适合用于翻译、文章写作、总结等AI任务。
"""

import os
from typing import Any, Dict, Generator, List, Optional, Union

from .common import DifyBaseClient, DifyType


class TextGenerationEvent:
    """事件类型枚举

    定义了Dify API中可能的事件类型，用于处理流式响应中的事件。

    示例结构体:
        message: {
            "event": "message",
            "task_id": "task_123",
            "message_id": "msg_456",
            "conversation_id": "conv_789",
            "answer": "这是LLM返回的文本块",
            "created_at": 1705395332
        }
        agent_message: {
            "event": "agent_message",
            "task_id": "task_123",
            "message_id": "msg_456",
            "conversation_id": "conv_789",
            "answer": "这是Agent模式下返回的文本块",
            "created_at": 1705395332
        }
        agent_thought: {
            "event": "agent_thought",
            "task_id": "task_123",
            "message_id": "msg_456",
            "position": 1,
            "thought": "Agent正在思考...",
            "observation": "工具调用返回结果",
            "tool": "tool1;tool2",
            "tool_input": "{\"dalle3\": {\"prompt\": \"a cute cat\"}}",
            "created_at": 1705395332,
            "message_files": ["file_123"],
            "file_id": "file_123",
            "conversation_id": "conv_789"
        }
        message_file: {
            "event": "message_file",
            "id": "file_123",
            "type": "image",
            "belongs_to": "assistant",
            "url": "https://example.com/file.jpg",
            "conversation_id": "conv_789"
        }
        message_end: {
            "event": "message_end",
            "task_id": "task_123",
            "message_id": "msg_456",
            "conversation_id": "conv_789",
            "metadata": {},
            "usage": {},
            "retriever_resources": []
        }
        tts_message: {
            "event": "tts_message",
            "task_id": "task_123",
            "message_id": "msg_456",
            "audio": "base64编码的音频数据",
            "created_at": 1705395332
        }
        tts_message_end: {
            "event": "tts_message_end",
            "task_id": "task_123",
            "message_id": "msg_456",
            "audio": "",
            "created_at": 1705395332
        }
        message_replace: {
            "event": "message_replace",
            "task_id": "task_123",
            "message_id": "msg_456",
            "conversation_id": "conv_789",
            "answer": "替换后的内容",
            "created_at": 1705395332
        }
        error: {
            "event": "error",
            "task_id": "task_123",
            "message_id": "msg_456",
            "status": 500,
            "code": "internal_error",
            "message": "发生内部错误"
        }
        ping: {
            "event": "ping",
        }
    """

    MESSAGE = "message"  # LLM返回文本块事件
    MESSAGE_END = "message_end"  # 消息结束事件
    TTS_MESSAGE = "tts_message"  # TTS音频流事件
    TTS_MESSAGE_END = "tts_message_end"  # TTS音频流结束事件
    MESSAGE_REPLACE = "message_replace"  # 消息内容替换事件
    ERROR = "error"  # 异常事件
    PING = "ping"  # 保持连接存活的ping事件


class TextGenerationClient(DifyBaseClient):
    """Dify Text Generation应用客户端类。

    提供与Dify Text Generation应用API交互的方法，包括发送消息、
    上传文件、文字转语音等功能。Text Generation应用无会话支持，
    适合用于翻译、文章写作、总结等AI任务。
    """

    type = DifyType.TextGeneration

    def completion(
        self,
        query: str,
        user: str,
        response_mode: str = "streaming",
        inputs: Dict[str, Any] = None,
        files: List[Dict[str, Any]] = None,
        **kwargs,  # 添加kwargs参数支持
    ) -> Union[Dict[str, Any], Generator[Dict[str, Any], None, None]]:
        """
        发送消息给文本生成应用。

        Args:
            query (str): 用户输入/提问内容，将作为inputs的query字段
            user (str): 用户标识，用于定义终端用户的身份
            response_mode (str, optional): 响应模式，'streaming'（流式）或'blocking'（阻塞）。默认为'streaming'
            inputs (Dict[str, Any], optional): 额外的输入参数。默认为None，若提供，会与query合并
            files (List[Dict[str, Any]], optional): 要包含在消息中的文件列表，每个文件为一个字典。默认为None
            **kwargs: 额外的请求参数，如timeout、max_retries等

        Returns:
            Union[Dict[str, Any], Generator[Dict[str, Any], None, None]]:
                如果response_mode为'blocking'，返回完整响应字典；
                如果response_mode为'streaming'，返回字典生成器。

        Raises:
            ValueError: 当提供了无效的参数时
            DifyAPIError: 当API请求失败时
        """
        if response_mode not in ["streaming", "blocking"]:
            raise ValueError("response_mode must be 'streaming' or 'blocking'")

        # 准备inputs，确保包含query
        if inputs is None:
            inputs = {}

        inputs["query"] = query
        payload = {
            "inputs": inputs,
            "user": user,
            "response_mode": response_mode,
        }

        if files:
            payload["files"] = files

        endpoint = "completion-messages"

        if response_mode == "streaming":
            return self.post_stream(endpoint, json_data=payload, **kwargs)  # 传递kwargs
        else:
            return self.post(endpoint, json_data=payload, **kwargs)  # 传递kwargs

    def stop_task(self, task_id: str, user: str) -> Dict[str, Any]:
        """
        停止正在进行的响应，仅支持流式模式。

        Args:
            task_id (str): 任务ID，可在流式返回Chunk中获取
            user (str): 用户标识，必须和发送消息接口传入user保持一致

        Returns:
            Dict[str, Any]: 停止响应的结果

        Raises:
            DifyAPIError: 当API请求失败时
        """
        endpoint = f"completion-messages/{task_id}/stop"
        payload = {"user": user}
        return self.post(endpoint, json_data=payload)

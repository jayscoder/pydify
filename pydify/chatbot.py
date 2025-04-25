"""
Pydify - Dify Chatbot应用客户端

此模块提供与Dify Chatbot应用API交互的客户端。
Chatbot对话应用支持会话持久化，可将之前的聊天记录作为上下文进行回答，适用于聊天/客服AI等场景。
"""

import json
import os
from typing import Any, Dict, Generator, List, Optional, Union

from .common import DifyBaseClient, DifyType


class ChatbotEvent:
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
    AGENT_MESSAGE = "agent_message"  # Agent模式下返回文本块事件
    AGENT_THOUGHT = "agent_thought"  # Agent思考步骤相关内容
    MESSAGE_FILE = "message_file"  # 文件事件
    MESSAGE_END = "message_end"  # 消息结束事件
    TTS_MESSAGE = "tts_message"  # TTS音频流事件
    TTS_MESSAGE_END = "tts_message_end"  # TTS音频流结束事件
    MESSAGE_REPLACE = "message_replace"  # 消息内容替换事件
    ERROR = "error"  # 异常事件
    PING = "ping"  # 保持连接存活的ping事件


class ChatbotClient(DifyBaseClient):
    """Dify Chatbot应用客户端类。

    提供与Dify Chatbot应用API交互的方法，包括发送消息、获取历史消息、管理会话、
    上传文件、语音转文字、文字转语音等功能。
    """

    type = DifyType.Chatbot

    def send_message(
        self,
        query: str,
        user: str,
        response_mode: str = "streaming",
        inputs: Dict[str, Any] = None,
        conversation_id: str = None,
        files: List[Dict[str, Any]] = None,
        auto_generate_name: bool = True,
        **kwargs,
    ) -> Union[Dict[str, Any], Generator[Dict[str, Any], None, None]]:
        """
        发送对话消息，创建会话消息。

        Args:
            query (str): 用户输入/提问内容
            user (str): 用户标识，用于定义终端用户的身份
            response_mode (str, optional): 响应模式，'streaming'（流式）或'blocking'（阻塞）。默认为'streaming'
            inputs (Dict[str, Any], optional): App定义的各变量值。默认为None
            conversation_id (str, optional): 会话ID，基于之前的聊天记录继续对话时需提供。默认为None
            files (List[Dict[str, Any]], optional): 要包含在消息中的文件列表，每个文件为一个字典。默认为None
            auto_generate_name (bool, optional): 是否自动生成会话标题。默认为True
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

        payload = {
            "query": query,
            "user": user,
            "response_mode": response_mode,
            "auto_generate_name": auto_generate_name,
        }

        # 确保inputs始终存在，即使是空字典
        payload["inputs"] = inputs or {}

        if conversation_id:
            payload["conversation_id"] = conversation_id

        if files:
            payload["files"] = files

        endpoint = "chat-messages"

        # 打印请求信息，便于调试
        print(f"请求URL: {self.base_url}{endpoint}")
        print(f"请求参数: {json.dumps(payload)}")

        if response_mode == "streaming":
            return self.post_stream(endpoint, json_data=payload, **kwargs)
        else:
            return self.post(endpoint, json_data=payload, **kwargs)

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
        endpoint = f"chat-messages/{task_id}/stop"
        payload = {"user": user}
        return self.post(endpoint, json_data=payload)

    def get_meta(self) -> Dict[str, Any]:
        """
        获取应用元信息，包括工具图标等。

        Returns:
            Dict[str, Any]: 元信息

        Raises:
            DifyAPIError: 当API请求失败时
        """
        return self.get("meta")

    def audio_to_text(self, file_path: str, user: str) -> Dict[str, Any]:
        """
        音频转文字，通过上传音频文件将其转换为文本。

        Args:
            file_path (str): 要上传的音频文件路径，支持mp3, wav, webm, m4a, mpga, mpeg格式
            user (str): 用户标识

        Returns:
            Dict[str, Any]: 转换结果，包含识别出的文本

        Raises:
            FileNotFoundError: 当文件不存在时
            ValueError: 当文件格式不支持时
            DifyAPIError: 当API请求失败时
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        # 检查文件类型
        supported_extensions = ["mp3", "wav", "webm", "m4a", "mpga", "mpeg"]
        file_extension = os.path.splitext(file_path)[1].lower().replace(".", "")

        if file_extension not in supported_extensions:
            raise ValueError(
                f"Unsupported audio file type. Supported types: {supported_extensions}"
            )

        with open(file_path, "rb") as file:
            return self.audio_to_text_obj(file, os.path.basename(file_path), user)

    def audio_to_text_obj(self, file_obj, filename: str, user: str) -> Dict[str, Any]:
        """
        音频转文字，通过文件对象将音频转换为文本。

        Args:
            file_obj: 音频文件对象
            filename (str): 文件名，用于确定文件类型
            user (str): 用户标识

        Returns:
            Dict[str, Any]: 转换结果，包含识别出的文本

        Raises:
            ValueError: 当文件格式不支持时
            DifyAPIError: 当API请求失败时
        """
        # 检查文件类型
        supported_extensions = ["mp3", "wav", "webm", "m4a", "mpga", "mpeg"]
        file_extension = os.path.splitext(filename)[1].lower().replace(".", "")

        if file_extension not in supported_extensions:
            raise ValueError(
                f"Unsupported audio file type. Supported types: {supported_extensions}"
            )

        files = {"file": (filename, file_obj)}
        data = {"user": user}

        headers = self._get_headers()
        # 移除Content-Type，让requests自动设置multipart/form-data
        headers.pop("Content-Type", None)

        endpoint = "audio-to-text"
        response = self._request(
            "POST", endpoint, headers=headers, files=files, data=data
        )
        return response.json()

    def get_messages(
        self, conversation_id: str, user: str, first_id: str = None, limit: int = 20
    ) -> Dict[str, Any]:
        """
        获取会话消息列表，支持分页加载历史聊天记录。

        Args:
            conversation_id (str): 会话ID，用于标识特定的对话会话
            user (str): 用户标识，由开发者定义规则，需保证用户标识在应用内唯一
            first_id (str, optional): 当前页第一条聊天记录的ID，用于分页加载。默认为None
            limit (int, optional): 一次请求返回的聊天记录数量，默认20条

        Returns:
            Dict[str, Any]: 包含消息列表和分页信息的响应数据，具体结构如下：
                - has_more (bool): 是否存在下一页
                - limit (int): 实际返回的记录数量
                - data (List[Dict]): 消息列表，每条消息包含：
                    - id (str): 消息ID
                    - conversation_id (str): 会话ID
                    - inputs (Dict): 用户输入参数
                    - query (str): 用户输入/提问内容
                    - answer (str): 回答消息内容
                    - created_at (int): 创建时间戳
                    - feedback (Dict): 用户反馈信息
                    - message_files (List[Dict]): 消息关联的文件列表
                        - id (str): 文件ID
                        - type (str): 文件类型
                        - url (str): 文件URL
                        - belongs_to (str): 文件归属方 assistant/user
                    - agent_thoughts (List[Dict]): Agent思考内容列表（仅Agent模式下不为空），每个思考包含：
                        - id (str): Agent思考ID，每一轮迭代唯一
                        - message_id (str): 所属消息ID
                        - position (int): 在消息中的位置，如第一轮迭代为1
                        - thought (str): Agent的思考内容
                        - observation (str): 工具调用的返回结果
                        - tool (str): 使用的工具列表，以分号分隔多个工具
                        - tool_input (str): 工具输入参数，JSON格式字符串
                        - created_at (int): 创建时间戳
                        - message_files (List[str]): 关联的文件ID列表
                        - file_id (str): 文件ID
                        - conversation_id (str): 所属会话ID
                    - retriever_resources (List[Dict]): 引用和归属分段列表，每个分段包含：
                        - position (int): 分段在回答中的位置
                        - dataset_id (str): 数据集ID
                        - dataset_name (str): 数据集名称
                        - document_id (str): 文档ID
                        - document_name (str): 文档名称
                        - segment_id (str): 分段ID
                        - score (float): 相似度得分
                        - content (str): 分段内容
        Raises:
            DifyAPIError: 当API请求失败时
        """
        endpoint = "messages"

        params = {
            "conversation_id": conversation_id,
            "user": user,
            "limit": limit,
        }

        if first_id:
            params["first_id"] = first_id

        return self.get(endpoint, params=params)

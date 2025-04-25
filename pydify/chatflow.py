"""
Pydify - Dify Chatflow应用客户端

此模块提供与Dify Chatflow应用API交互的客户端。
Chatflow工作流编排对话型应用基于工作流编排，适用于定义复杂流程的多轮对话场景，具有记忆功能。
"""

import json
import mimetypes
import os
from typing import Any, BinaryIO, Dict, Generator, List, Optional, Tuple, Union

from .chatbot import ChatbotClient
from .common import DifyBaseClient, DifyType


class ChatflowEvent:
    """事件类型枚举

    定义了Dify Chatflow API中可能的事件类型，用于处理流式响应中的事件。
    """

    MESSAGE = "message"  # LLM返回文本块事件，包含分块输出的文本内容
    MESSAGE_FILE = "message_file"  # 文件事件，表示有新文件需要展示
    MESSAGE_END = "message_end"  # 消息结束事件，表示流式返回结束
    MESSAGE_REPLACE = "message_replace"  # 消息内容替换事件，用于内容审查后的替换
    TTS_MESSAGE = "tts_message"  # TTS音频流事件，包含base64编码的音频块
    TTS_MESSAGE_END = "tts_message_end"  # TTS音频流结束事件
    WORKFLOW_STARTED = "workflow_started"  # workflow开始执行事件
    NODE_STARTED = "node_started"  # 节点开始执行事件
    NODE_FINISHED = "node_finished"  # 节点执行结束事件（包含成功/失败状态）
    WORKFLOW_FINISHED = "workflow_finished"  # workflow执行结束事件（包含成功/失败状态）
    ERROR = "error"  # 流式输出过程中出现的异常事件
    PING = "ping"  # 保持连接存活的ping事件，每10秒一次


class ChatflowClient(ChatbotClient):
    """Dify Chatflow应用客户端类。

    提供与Dify Chatflow应用API交互的方法，包括发送消息、获取历史消息、管理会话、
    上传文件、语音转文字、文字转语音等功能。Chatflow应用基于工作流编排，适用于定义复杂流程的多轮对话场景。
    """

    type = DifyType.Chatflow

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

        # 确保inputs字段始终存在，即使是空字典
        payload["inputs"] = inputs or {}

        if conversation_id:
            payload["conversation_id"] = conversation_id

        if files:
            payload["files"] = files

        endpoint = "chat-messages"

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
            requests.HTTPError: 当API请求失败时
        """
        endpoint = f"chat-messages/{task_id}/stop"
        payload = {"user": user}
        return self.post(endpoint, json_data=payload)

    def get_suggested_questions(
        self, message_id: str, user: str, **kwargs
    ) -> Dict[str, Any]:
        """
        获取下一轮建议问题列表。

        Args:
            message_id (str): 消息ID
            user (str): 用户标识
            **kwargs: 额外的请求参数，如timeout、max_retries等

        Returns:
            Dict[str, Any]: 建议问题列表

        Raises:
            DifyAPIError: 当API请求失败时
        """
        params = {
            "user": user,
            # "message_id": message_id,
        }
        # /messages/{message_id}/suggested
        endpoint = f"messages/{message_id}/suggested"
        return self.get(endpoint, params=params, **kwargs)

    def get_messages(
        self,
        conversation_id: str,
        user: str,
        first_id: str = None,
        limit: int = 20,
    ) -> Dict[str, Any]:
        """
        获取会话历史消息，滚动加载形式返回历史聊天记录，第一页返回最新limit条（倒序返回）。

        Args:
            conversation_id (str): 会话ID，用于标识特定的对话会话
            user (str): 用户标识，用于验证用户权限
            first_id (str, optional): 当前页第一条聊天记录的ID，用于分页加载。默认为None
            limit (int, optional): 一次请求返回的聊天记录数量，默认20条，用于控制分页大小。默认为20

        Returns:
            Dict[str, Any]: 返回包含以下字段的字典:
                - limit (int): 本次请求返回的消息数量
                - has_more (bool): 是否还有更多历史消息
                - data (List[Dict]): 消息列表，每个消息包含:
                    - id (str): 消息唯一标识
                    - conversation_id (str): 所属会话ID
                    - inputs (Dict): 输入参数
                    - query (str): 用户查询内容
                    - answer (str): AI助手回答内容
                    - message_files (List[Dict]): 消息相关文件列表，每个文件包含:
                        - id (str): 文件ID
                        - type (str): 文件类型
                        - url (str): 文件访问URL
                        - belongs_to (str): 文件所属方
                    - feedback (Dict): 用户反馈信息
                    - retriever_resources (List): 检索资源列表
                    - created_at (int): 消息创建时间戳
        Raises:
            requests.HTTPError: 当API请求失败时抛出
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

    def get_conversations(
        self,
        user: str,
        last_id: str = None,
        limit: int = 20,
        sort_by: str = "-updated_at",
    ) -> Dict[str, Any]:
        """
        获取会话列表，默认返回最近的20条。

        Args:
            user (str): 用户标识
            last_id (str, optional): 当前页最后面一条记录的ID。默认为None
            limit (int, optional): 一次请求返回多少条记录，默认20条，最大100条，最小1条。默认为20
            sort_by (str, optional): 排序字段，可选值：created_at, -created_at, updated_at, -updated_at。默认为"-updated_at"

        Returns:
            Dict[str, Any]: 会话列表及分页信息

        Raises:
            ValueError: 当提供了无效的参数时
            requests.HTTPError: 当API请求失败时
        """
        valid_sort_values = ["created_at", "-created_at", "updated_at", "-updated_at"]
        if sort_by not in valid_sort_values:
            raise ValueError(f"sort_by must be one of {valid_sort_values}")

        if limit < 1 or limit > 100:
            raise ValueError("limit must be between 1 and 100")

        endpoint = "conversations"

        params = {
            "user": user,
            "limit": limit,
            "sort_by": sort_by,
        }

        if last_id:
            params["last_id"] = last_id

        return self.get(endpoint, params=params)

    def delete_conversation(self, conversation_id: str, user: str) -> Dict[str, Any]:
        """
        删除会话。

        Args:
            conversation_id (str): 会话ID
            user (str): 用户标识

        Returns:
            Dict[str, Any]: 删除结果

        Raises:
            requests.HTTPError: 当API请求失败时
        """
        endpoint = f"conversations/{conversation_id}"
        payload = {"user": user}
        return self._request("DELETE", endpoint, json=payload).json()

    def rename_conversation(
        self,
        conversation_id: str,
        user: str,
        name: str = None,
        auto_generate: bool = False,
    ) -> Dict[str, Any]:
        """
        会话重命名，对会话进行重命名，会话名称用于显示在支持多会话的客户端上。

        Args:
            conversation_id (str): 会话ID
            user (str): 用户标识
            name (str, optional): 名称，若auto_generate为True时，该参数可不传。默认为None
            auto_generate (bool, optional): 自动生成标题。默认为False

        Returns:
            Dict[str, Any]: 重命名后的会话信息

        Raises:
            ValueError: 当提供了无效的参数时
            requests.HTTPError: 当API请求失败时
        """
        if not auto_generate and not name:
            raise ValueError("name is required when auto_generate is False")

        endpoint = f"conversations/{conversation_id}/name"

        payload = {"user": user, "auto_generate": auto_generate}

        if name:
            payload["name"] = name

        return self.post(endpoint, json_data=payload)

    def audio_to_text(self, file_path: str, user: str) -> Dict[str, Any]:
        """
        语音转文字。

        Args:
            file_path (str): 语音文件路径，支持格式：['mp3', 'mp4', 'mpeg', 'mpga', 'm4a', 'wav', 'webm']
            user (str): 用户标识

        Returns:
            Dict[str, Any]: 转换结果，包含文字内容

        Raises:
            FileNotFoundError: 当文件不存在时
            ValueError: 当文件格式不支持时
            requests.HTTPError: 当API请求失败时
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        # 检查文件类型
        supported_extensions = ["mp3", "mp4", "mpeg", "mpga", "m4a", "wav", "webm"]
        file_extension = os.path.splitext(file_path)[1].lower().replace(".", "")

        if file_extension not in supported_extensions:
            raise ValueError(
                f"Unsupported file type. Supported types: {supported_extensions}"
            )

        with open(file_path, "rb") as file:
            files = {"file": file}
            data = {"user": user}

            url = os.path.join(self.base_url, "audio-to-text")

            headers = self._get_headers()
            # 移除Content-Type，让requests自动设置multipart/form-data
            headers.pop("Content-Type", None)

            response = self._request(
                "POST", "audio-to-text", headers=headers, files=files, data=data
            )
            return response.json()

    def audio_to_text_obj(
        self, file_obj: BinaryIO, filename: str, user: str
    ) -> Dict[str, Any]:
        """
        使用文件对象进行语音转文字。

        Args:
            file_obj (BinaryIO): 语音文件对象
            filename (str): 文件名，用于确定文件类型
            user (str): 用户标识

        Returns:
            Dict[str, Any]: 转换结果，包含文字内容

        Raises:
            ValueError: 当文件格式不支持时
            requests.HTTPError: 当API请求失败时
        """
        # 检查文件类型
        supported_extensions = ["mp3", "mp4", "mpeg", "mpga", "m4a", "wav", "webm"]
        file_extension = os.path.splitext(filename)[1].lower().replace(".", "")

        if file_extension not in supported_extensions:
            raise ValueError(
                f"Unsupported file type. Supported types: {supported_extensions}"
            )

        files = {"file": (filename, file_obj)}
        data = {"user": user}

        headers = self._get_headers()
        # 移除Content-Type，让requests自动设置multipart/form-data
        headers.pop("Content-Type", None)

        response = self._request(
            "POST", "audio-to-text", headers=headers, files=files, data=data
        )
        return response.json()

    def text_to_audio(
        self,
        user: str,
        message_id: str = None,
        text: str = None,
    ) -> Dict[str, Any]:
        """
        文字转语音。

        Args:
            user (str): 用户标识
            message_id (str, optional): Dify生成的文本消息ID，如果提供，系统会自动查找相应的内容直接合成语音。默认为None
            text (str, optional): 语音生成内容，如果没有传message_id，则使用此字段内容。默认为None

        Returns:
            Dict[str, Any]: 转换结果，包含音频数据

        Raises:
            ValueError: 当必要参数缺失时
            requests.HTTPError: 当API请求失败时
        """
        if not message_id and not text:
            raise ValueError("Either message_id or text must be provided")

        endpoint = "text-to-audio"

        payload = {"user": user}

        if message_id:
            payload["message_id"] = message_id

        if text:
            payload["text"] = text

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

"""
Pydify - Dify Chatbot应用客户端

此模块提供与Dify Chatbot应用API交互的客户端。
Chatbot对话应用支持会话持久化，可将之前的聊天记录作为上下文进行回答，适用于聊天/客服AI等场景。
"""

import json
import os
from typing import Any, Dict, Generator, List, Optional, Union

from .common import DifyBaseClient


class ChatbotClient(DifyBaseClient):
    """Dify Chatbot应用客户端类。

    提供与Dify Chatbot应用API交互的方法，包括发送消息、获取历史消息、管理会话、
    上传文件、语音转文字、文字转语音等功能。
    """

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

    def stop_response(self, task_id: str, user: str) -> Dict[str, Any]:
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

    def process_streaming_response(
        self,
        stream_generator: Generator[Dict[str, Any], None, None],
        handle_message=None,
        handle_message_file=None,
        handle_message_end=None,
        handle_tts_message=None,
        handle_tts_message_end=None,
        handle_message_replace=None,
        handle_error=None,
        handle_ping=None,
        break_on_error=True,
    ) -> Dict[str, Any]:
        """
        处理流式响应，调用相应事件处理器。

        Args:
            stream_generator: 流式响应生成器
            handle_message: 消息事件处理函数
            handle_message_file: 消息文件事件处理函数
            handle_message_end: 消息结束事件处理函数
            handle_tts_message: TTS音频流事件处理函数
            handle_tts_message_end: TTS音频流结束事件处理函数
            handle_message_replace: 消息内容替换事件处理函数
            handle_error: 错误事件处理函数
            handle_ping: ping事件处理函数
            break_on_error: 当遇到错误时是否中断处理，默认为True

        Returns:
            Dict[str, Any]: 处理结果，包含消息ID和会话ID等信息

        示例:
            ```python
            def on_message(chunk):
                print(f"{chunk['answer']}")

            def on_message_end(chunk):
                print(f"消息结束: ID={chunk['message_id']}")

            client = ChatbotClient(api_key)
            stream = client.send_message(
                query="你好，帮我介绍下你自己",
                user="user123",
                response_mode="streaming"
            )
            result = client.process_streaming_response(
                stream,
                handle_message=on_message,
                handle_message_end=on_message_end
            )
            ```
        """
        result = {}
        answer_chunks = []

        for chunk in stream_generator:
            event = chunk.get("event")

            if event == "message" and handle_message:
                handle_message(chunk)
                # 累积回答内容
                if "answer" in chunk:
                    answer_chunks.append(chunk["answer"])
                # 保存消息ID和会话ID
                if "message_id" in chunk and not result.get("message_id"):
                    result["message_id"] = chunk["message_id"]
                if "conversation_id" in chunk and not result.get("conversation_id"):
                    result["conversation_id"] = chunk["conversation_id"]
                if "task_id" in chunk and not result.get("task_id"):
                    result["task_id"] = chunk["task_id"]

            elif event == "message_file" and handle_message_file:
                handle_message_file(chunk)
                # 保存文件相关信息
                if "files" not in result:
                    result["files"] = []
                if "file" in chunk:
                    result["files"].append(chunk["file"])

            elif event == "message_end" and handle_message_end:
                handle_message_end(chunk)
                # 保存元数据
                if "metadata" in chunk:
                    result["metadata"] = chunk["metadata"]
                if "message_id" in chunk and not result.get("message_id"):
                    result["message_id"] = chunk["message_id"]
                if "conversation_id" in chunk and not result.get("conversation_id"):
                    result["conversation_id"] = chunk["conversation_id"]

            elif event == "tts_message" and handle_tts_message:
                handle_tts_message(chunk)

            elif event == "tts_message_end" and handle_tts_message_end:
                handle_tts_message_end(chunk)

            elif event == "message_replace" and handle_message_replace:
                handle_message_replace(chunk)
                # 替换回答内容
                if "answer" in chunk:
                    answer_chunks = [chunk["answer"]]

            elif event == "error" and handle_error:
                handle_error(chunk)
                if break_on_error:
                    # 添加错误信息到结果中
                    result["error"] = {
                        "status": chunk.get("status"),
                        "code": chunk.get("code"),
                        "message": chunk.get("message"),
                    }
                    break

            elif event == "ping" and handle_ping:
                handle_ping(chunk)

        # 合并所有回答块
        if answer_chunks:
            result["answer"] = "".join(answer_chunks)

        return result

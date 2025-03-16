"""
Pydify - Dify Agent应用客户端

此模块提供与Dify Agent应用API交互的客户端。
Agent对话型应用能够迭代式的规划推理、自主工具调用，直至完成任务目标的智能助手。
"""

import json
import mimetypes
import os
from typing import Any, BinaryIO, Dict, Generator, List, Optional, Tuple, Union

from .common import DifyBaseClient


class AgentClient(DifyBaseClient):
    """Dify Agent应用客户端类。

    提供与Dify Agent应用API交互的方法，包括发送消息、获取历史消息、管理会话、
    上传文件、语音转文字、文字转语音等功能。Agent应用支持迭代式规划推理和自主工具调用。
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
        **kwargs,  # 添加kwargs参数，用于接收额外的请求参数
    ) -> Generator[Dict[str, Any], None, None]:
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

    def stop_response(self, task_id: str, user: str) -> Dict[str, Any]:
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

    def message_feedback(
        self,
        message_id: str,
        user: str,
        rating: str = None,
        content: str = None,
    ) -> Dict[str, Any]:
        """
        对消息进行反馈（点赞/点踩）。

        Args:
            message_id (str): 消息ID
            user (str): 用户标识
            rating (str, optional): 评价，可选值：'like'(点赞), 'dislike'(点踩), None(撤销)。默认为None
            content (str, optional): 反馈的具体信息。默认为None

        Returns:
            Dict[str, Any]: 反馈结果

        Raises:
            ValueError: 当提供了无效的参数时
            requests.HTTPError: 当API请求失败时
        """
        if rating and rating not in ["like", "dislike", None]:
            raise ValueError("rating must be 'like', 'dislike' or None")

        endpoint = f"messages/{message_id}/feedbacks"

        payload = {"user": user}

        if rating is not None:
            payload["rating"] = rating

        if content:
            payload["content"] = content

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
        # 尝试多种可能的端点路径格式
        possible_endpoints = [
            f"messages/{message_id}/suggested",  # 原始格式
            f"messages/{message_id}/suggested-questions",  # 新格式1
            f"chat-messages/{message_id}/suggested-questions",  # 新格式2
            "suggested-questions",  # 当前格式
        ]

        params = {
            "user": user,
        }

        # 添加详细日志
        # print(f"请求推荐问题: 消息ID={message_id}, 用户={user}")

        # 尝试所有可能的端点，直到找到一个有效的
        last_error = None
        for endpoint in possible_endpoints:
            try:
                params_to_use = params.copy()
                # 如果端点是standalone的suggested-questions，需要添加message_id参数
                if endpoint == "suggested-questions":
                    params_to_use["message_id"] = message_id
                else:
                    # 否则可能不需要在参数中包含message_id
                    params_to_use.pop("message_id", None)

                print(f"尝试端点: {endpoint}, 参数: {params_to_use}")
                result = self.get(endpoint, params=params_to_use, **kwargs)
                print(f"端点 {endpoint} 请求成功!")
                return result
            except Exception as e:
                last_error = e
                print(f"端点 {endpoint} 请求失败: {str(e)}")
                continue

        # 如果所有端点都失败，记录最后一个错误并返回空结果
        print(f"所有推荐问题端点请求都失败。最后错误: {str(last_error)}")
        return {"data": []}

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
            conversation_id (str): 会话ID
            user (str): 用户标识
            first_id (str, optional): 当前页第一条聊天记录的ID。默认为None
            limit (int, optional): 一次请求返回多少条聊天记录。默认为20

        Returns:
            Dict[str, Any]: 消息列表及分页信息，包含agent_thoughts（Agent的思考过程）

        Raises:
            requests.HTTPError: 当API请求失败时
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

    def upload_file(self, file_path: str, user: str) -> Dict[str, Any]:
        """
        上传文件（目前仅支持图片）到Dify API，可用于图文多模态理解。

        Args:
            file_path (str): 要上传的文件路径，支持png, jpg, jpeg, webp, gif格式
            user (str): 用户标识

        Returns:
            Dict[str, Any]: 上传文件的响应数据

        Raises:
            FileNotFoundError: 当文件不存在时
            ValueError: 当文件格式不支持时
            requests.HTTPError: 当API请求失败时
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        # 检查文件类型
        supported_extensions = ["png", "jpg", "jpeg", "webp", "gif"]
        file_extension = os.path.splitext(file_path)[1].lower().replace(".", "")

        if file_extension not in supported_extensions:
            raise ValueError(
                f"Unsupported file type. Supported types: {supported_extensions}"
            )

        with open(file_path, "rb") as file:
            files = {"file": file}
            data = {"user": user}

            headers = self._get_headers()
            # 移除Content-Type，让requests自动设置multipart/form-data
            headers.pop("Content-Type", None)

            response = self._request(
                "POST", "files/upload", headers=headers, files=files, data=data
            )
            return response.json()

    def upload_file_obj(
        self, file_obj: BinaryIO, filename: str, user: str
    ) -> Dict[str, Any]:
        """
        使用文件对象上传文件（目前仅支持图片）到Dify API。

        Args:
            file_obj (BinaryIO): 文件对象
            filename (str): 文件名，用于确定文件类型
            user (str): 用户标识

        Returns:
            Dict[str, Any]: 上传文件的响应数据

        Raises:
            ValueError: 当文件格式不支持时
            requests.HTTPError: 当API请求失败时
        """
        # 检查文件类型
        supported_extensions = ["png", "jpg", "jpeg", "webp", "gif"]
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
            "POST", "files/upload", headers=headers, files=files, data=data
        )
        return response.json()

    def get_app_info(self) -> Dict[str, Any]:
        """
        获取应用基本信息。

        Returns:
            Dict[str, Any]: 应用信息，包含名称、描述和标签

        Raises:
            requests.HTTPError: 当API请求失败时
        """
        return self.get("info")

    def get_parameters(self) -> Dict[str, Any]:
        """
        获取应用参数，包括功能开关、输入参数名称、类型及默认值等。

        Returns:
            Dict[str, Any]: 应用参数配置

        Raises:
            requests.HTTPError: 当API请求失败时
        """
        return self.get("parameters")

    def get_meta(self) -> Dict[str, Any]:
        """
        获取应用Meta信息，用于获取工具icon等。

        Returns:
            Dict[str, Any]: 应用Meta信息

        Raises:
            requests.HTTPError: 当API请求失败时
        """
        return self.get("meta")

    def process_streaming_response(
        self,
        stream_generator: Generator[Dict[str, Any], None, None],
        handle_message=None,
        handle_agent_message=None,
        handle_agent_thought=None,
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
            handle_message: LLM返回文本块事件处理函数
            handle_agent_message: Agent模式下返回文本块事件处理函数
            handle_agent_thought: Agent模式下思考步骤事件处理函数
            handle_message_file: 文件事件处理函数
            handle_message_end: 消息结束事件处理函数
            handle_tts_message: TTS音频流事件处理函数
            handle_tts_message_end: TTS音频流结束事件处理函数
            handle_message_replace: 消息内容替换事件处理函数
            handle_error: 错误事件处理函数
            handle_ping: ping事件处理函数
            break_on_error: 当遇到错误时是否中断处理，默认为True

        Returns:
            Dict[str, Any]: 处理结果，包含消息ID、会话ID等信息

        示例:
            ```python
            def on_agent_message(chunk):
                # 打印Agent返回的文本块
                print(f"{chunk['answer']}")

            def on_agent_thought(chunk):
                print(f"Agent思考: {chunk['thought']}")
                print(f"使用工具: {chunk['tool']}")
                print(f"工具输入: {chunk['tool_input']}")
                print(f"观察结果: {chunk['observation']}")

            def on_message_end(chunk):
                print(f"消息结束: ID={chunk['message_id']}")

            client = AgentClient(api_key)
            stream = client.send_message(
                query="帮我分析最近的股市走势",
                user="user123"
            )
            result = client.process_streaming_response(
                stream,
                handle_agent_message=on_agent_message,
                handle_agent_thought=on_agent_thought,
                handle_message_end=on_message_end
            )
            ```
        """
        result = {"agent_thoughts": []}
        answer_chunks = []

        for chunk in stream_generator:
            event = chunk.get("event")

            if event == "message" and handle_message:
                handle_message(chunk)
                # 累积回答内容
                if "answer" in chunk:
                    answer_chunks.append(chunk["answer"])
                # 保存消息和会话ID
                if "message_id" in chunk and not result.get("message_id"):
                    result["message_id"] = chunk["message_id"]
                if "conversation_id" in chunk and not result.get("conversation_id"):
                    result["conversation_id"] = chunk["conversation_id"]
                if "task_id" in chunk and not result.get("task_id"):
                    result["task_id"] = chunk["task_id"]

            elif event == "agent_message" and handle_agent_message:
                handle_agent_message(chunk)
                # 累积回答内容
                if "answer" in chunk:
                    answer_chunks.append(chunk["answer"])
                # 保存消息和会话ID
                if "message_id" in chunk and not result.get("message_id"):
                    result["message_id"] = chunk["message_id"]
                if "conversation_id" in chunk and not result.get("conversation_id"):
                    result["conversation_id"] = chunk["conversation_id"]
                if "task_id" in chunk and not result.get("task_id"):
                    result["task_id"] = chunk["task_id"]

            elif event == "agent_thought" and handle_agent_thought:
                if handle_agent_thought:
                    handle_agent_thought(chunk)
                # 保存Agent思考内容
                thought_data = {
                    "id": chunk.get("id"),
                    "position": chunk.get("position"),
                    "thought": chunk.get("thought"),
                    "observation": chunk.get("observation"),
                    "tool": chunk.get("tool"),
                    "tool_input": chunk.get("tool_input"),
                    "message_files": chunk.get("message_files", []),
                    "created_at": chunk.get("created_at"),
                }
                result["agent_thoughts"].append(thought_data)

            elif event == "message_file" and handle_message_file:
                handle_message_file(chunk)
                # 保存文件信息
                if not result.get("files"):
                    result["files"] = []
                result["files"].append(
                    {
                        "id": chunk.get("id"),
                        "type": chunk.get("type"),
                        "belongs_to": chunk.get("belongs_to"),
                        "url": chunk.get("url"),
                    }
                )

            elif event == "message_end" and handle_message_end:
                if handle_message_end:
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

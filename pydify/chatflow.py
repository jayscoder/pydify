"""
Pydify - Dify Chatflow应用客户端

此模块提供与Dify Chatflow应用API交互的客户端。
Chatflow工作流编排对话型应用基于工作流编排，适用于定义复杂流程的多轮对话场景，具有记忆功能。
"""

import json
import mimetypes
import os
from typing import Any, BinaryIO, Dict, Generator, List, Optional, Tuple, Union

from .common import DifyBaseClient


class ChatflowClient(DifyBaseClient):
    """Dify Chatflow应用客户端类。

    提供与Dify Chatflow应用API交互的方法，包括发送消息、获取历史消息、管理会话、
    上传文件、语音转文字、文字转语音等功能。Chatflow应用基于工作流编排，适用于定义复杂流程的多轮对话场景。
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

    def get_suggested_questions(self, message_id: str, user: str) -> Dict[str, Any]:
        """
        获取下一轮建议问题列表。

        Args:
            message_id (str): 消息ID
            user (str): 用户标识

        Returns:
            Dict[str, Any]: 建议问题列表

        Raises:
            requests.HTTPError: 当API请求失败时
        """
        endpoint = f"messages/{message_id}/suggested"
        params = {"user": user}
        return self.get(endpoint, params=params)

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
            Dict[str, Any]: 消息列表及分页信息

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
        上传文件到Dify API，可用于图文多模态理解。支持多种格式的文件。

        Args:
            file_path (str): 要上传的文件路径
            user (str): 用户标识

        Returns:
            Dict[str, Any]: 上传文件的响应数据

        Raises:
            FileNotFoundError: 当文件不存在时
            requests.HTTPError: 当API请求失败时
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        # 获取MIME类型
        mime_type, _ = mimetypes.guess_type(file_path)
        if not mime_type:
            mime_type = "application/octet-stream"

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
        使用文件对象上传文件到Dify API。

        Args:
            file_obj (BinaryIO): 文件对象
            filename (str): 文件名
            user (str): 用户标识

        Returns:
            Dict[str, Any]: 上传文件的响应数据

        Raises:
            requests.HTTPError: 当API请求失败时
        """
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
        handle_message_file=None,
        handle_message_end=None,
        handle_tts_message=None,
        handle_tts_message_end=None,
        handle_message_replace=None,
        handle_workflow_started=None,
        handle_node_started=None,
        handle_node_finished=None,
        handle_workflow_finished=None,
        handle_error=None,
        handle_ping=None,
        break_on_error=True,
    ) -> Dict[str, Any]:
        """
        处理流式响应，调用相应事件处理器。

        Args:
            stream_generator: 流式响应生成器
            handle_message: LLM返回文本块事件处理函数
            handle_message_file: 文件事件处理函数
            handle_message_end: 消息结束事件处理函数
            handle_tts_message: TTS音频流事件处理函数
            handle_tts_message_end: TTS音频流结束事件处理函数
            handle_message_replace: 消息内容替换事件处理函数
            handle_workflow_started: 工作流开始事件处理函数
            handle_node_started: 节点开始事件处理函数
            handle_node_finished: 节点完成事件处理函数
            handle_workflow_finished: 工作流完成事件处理函数
            handle_error: 错误事件处理函数
            handle_ping: ping事件处理函数
            break_on_error: 当遇到错误时是否中断处理，默认为True

        Returns:
            Dict[str, Any]: 处理结果，包含消息ID、会话ID等信息

        示例:
            ```python
            def on_message(chunk):
                print(f"收到消息块: {chunk['answer']}")

            def on_workflow_started(data):
                print(f"工作流开始: {data['id']}")

            def on_node_finished(data):
                print(f"节点完成: {data['node_id']}, 状态: {data['status']}")

            def on_workflow_finished(data):
                print(f"工作流完成: {data['id']}, 状态: {data['status']}")

            client = ChatflowClient(api_key)
            stream = client.send_message(
                query="你好，请介绍一下自己",
                user="user123",
                response_mode="streaming"
            )
            result = client.process_streaming_response(
                stream,
                handle_message=on_message,
                handle_workflow_started=on_workflow_started,
                handle_node_finished=on_node_finished,
                handle_workflow_finished=on_workflow_finished
            )
            ```
        """
        result = {"workflow_data": {}, "nodes_data": []}
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

            elif event == "message_file" and handle_message_file:
                handle_message_file(chunk)

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

            elif event == "workflow_started" and handle_workflow_started:
                if "workflow_run_id" in chunk:
                    result["workflow_run_id"] = chunk["workflow_run_id"]
                if "data" in chunk:
                    result["workflow_data"] = chunk["data"]
                if handle_workflow_started:
                    handle_workflow_started(chunk.get("data", {}))

            elif event == "node_started" and handle_node_started:
                if handle_node_started:
                    handle_node_started(chunk.get("data", {}))

            elif event == "node_finished" and handle_node_finished:
                if handle_node_finished:
                    data = chunk.get("data", {})
                    handle_node_finished(data)
                    # 收集节点数据
                    result["nodes_data"].append(data)

            elif event == "workflow_finished" and handle_workflow_finished:
                if handle_workflow_finished:
                    data = chunk.get("data", {})
                    handle_workflow_finished(data)
                    # 更新工作流数据
                    result["workflow_data"].update(data)

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

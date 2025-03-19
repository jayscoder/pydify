"""
Pydify - Dify Workflow应用客户端

此模块提供与Dify Workflow应用API交互的客户端。
"""

import json
import os
from typing import Any, BinaryIO, Dict, Generator, List, Optional, Tuple, Union

from .common import DifyAPIError, DifyBaseClient, DifyType


class WorkflowClient(DifyBaseClient):
    """Dify Workflow应用客户端类。

    提供与Dify Workflow应用API交互的方法，包括执行工作流、停止响应、上传文件和获取日志等功能。
    """

    type = DifyType.Workflow

    def run(
        self,
        inputs: Dict[str, Any],
        user: str,
        response_mode: str = "streaming",
        files: List[Dict[str, Any]] = None,
        **kwargs,
    ) -> Union[Dict[str, Any], Generator[Dict[str, Any], None, None]]:
        """
        执行工作流。

        Args:
            inputs (Dict[str, Any]): 必需参数。包含工作流所需的输入变量键值对。
                                   每个键对应一个工作流定义中的变量名称，值为该变量的具体内容。

                                   注意：根据API版本的不同，Dify API可能期望不同的参数格式：
                                   - 有些API版本要求使用 "inputs" 作为键
                                   - 有些API版本要求使用 "input" 作为键
                                   - 有些API版本期望直接提供扁平的输入结构

                                   常见输入示例：
                                   ```
                                   # 简单文本输入
                                   inputs = {
                                       "prompt": "请给我写一首诗",
                                       "topic": "人工智能"
                                   }

                                   # 包含更复杂结构的输入
                                   inputs = {
                                       "text_to_analyze": "这是一段需要分析的文本",
                                       "analysis_type": "sentiment",
                                       "options": {
                                           "detailed": True,
                                           "language": "chinese"
                                       }
                                   }
                                   ```

            user (str): 用户标识，用于跟踪和区分不同用户的请求

            response_mode (str, optional): 响应模式:
                - 'streaming'（流式）: 实时获取工作流执行过程和结果，适合长时间运行的任务
                - 'blocking'（阻塞）: 等待工作流完全执行完毕后返回结果，适合简短任务
                默认为'streaming'。

            files (List[Dict[str, Any]], optional): 文件列表，每个文件为一个字典，包含以下字段：
                - type (str): 文件类型，支持:
                    - document: 支持'TXT', 'MD', 'MARKDOWN', 'PDF', 'HTML', 'XLSX', 'XLS',
                              'DOCX', 'CSV', 'EML', 'MSG', 'PPTX', 'PPT', 'XML', 'EPUB'
                    - image: 支持'JPG', 'JPEG', 'PNG', 'GIF', 'WEBP', 'SVG'
                    - audio: 支持'MP3', 'M4A', 'WAV', 'WEBM', 'AMR'
                    - video: 支持'MP4', 'MOV', 'MPEG', 'MPGA'
                    - custom: 支持其他文件类型
                - transfer_method (str): 传递方式:
                    - 'remote_url': 使用远程URL获取文件
                    - 'local_file': 使用之前通过upload_file上传的文件ID
                - url (str): 文件的URL地址（仅当transfer_method为'remote_url'时需要）
                - upload_file_id (str): 上传文件ID（仅当transfer_method为'local_file'时需要）

                示例:
                ```
                [
                    {
                        "type": "document",
                        "transfer_method": "local_file",
                        "upload_file_id": "文件ID"
                    },
                    {
                        "type": "image",
                        "transfer_method": "remote_url",
                        "url": "https://example.com/image.png"
                    }
                ]
                ```

            **kwargs: 额外的请求参数:
                - timeout (int): 请求超时时间(秒)，默认为30秒
                - max_retries (int): 网络错误时的最大重试次数，默认为2次

        Returns:
            Union[Dict[str, Any], Generator[Dict[str, Any], None, None]]:
                如果response_mode为'blocking'，返回完整响应字典，包含工作流执行结果;
                如果response_mode为'streaming'，返回一个字典生成器，实时提供工作流执行状态。

                阻塞模式返回示例:
                ```
                {
                    "id": "workflow_run_id",
                    "status": "succeeded",
                    "outputs": {
                        "result": "这是工作流的结果输出",
                        "additional_data": {...}
                    },
                    "started_at": 1617979572,
                    "ended_at": 1617979575
                }
                ```

                流式模式返回的每个事件示例:
                ```
                {
                    "event": "workflow_started",
                    "data": {"id": "workflow_run_id", ...}
                }
                ```

        Raises:
            ValueError: 当提供了无效的参数时，例如不支持的response_mode
            DifyAPIError: 当API请求失败时。常见错误包括:
                - 400 invalid_param: 缺少必需参数或参数格式错误
                - 400 input_is_required: 工作流需要输入但未提供
                - 400 wrong_format: 输入格式不正确
                - 401 unauthorized: API密钥无效或无权限
                - 404 not_found: 工作流不存在
                - 429 too_many_requests: 请求频率超限
                - 500 internal_server_error: 服务器内部错误
        """
        if response_mode not in ["streaming", "blocking"]:
            raise ValueError("response_mode must be 'streaming' or 'blocking'")

        # 注意：如果您收到参数相关的错误，可能需要根据您的API版本修改以下代码
        # 当前我们使用 "inputs" 作为嵌套参数名 (复数形式)
        payload = {
            "inputs": inputs,
            "response_mode": response_mode,
            "user": user,
        }

        if files:
            payload["files"] = files

        endpoint = "workflows/run"

        try:
            if response_mode == "streaming":
                return self.post_stream(endpoint, json_data=payload, **kwargs)
            else:
                return self.post(endpoint, json_data=payload, **kwargs)
        except DifyAPIError as e:
            # 捕获并增强特定的API错误，提供更有用的提示
            if (
                "input is required" in str(e).lower()
                or "invalid_param" in str(e).lower()
            ):
                error_msg = f"{str(e)}\n\n可能的解决方法:\n"
                error_msg += "1. 检查您的API版本和参数格式要求\n"
                error_msg += "2. 修改workflow.py中的run方法中的payload格式:\n"
                error_msg += "   - 尝试将'inputs'改为'input'(单数形式)\n"
                error_msg += "   - 或尝试直接使用扁平结构\n"
                error_msg += "3. 参考Dify官方API文档查看最新的参数格式\n"

                raise DifyAPIError(
                    error_msg, status_code=e.status_code, error_data=e.error_data
                )
            else:
                # 原样抛出其他错误
                raise

    def stop_task(self, task_id: str, user: str, **kwargs) -> Dict[str, Any]:
        """
        停止正在执行的工作流任务。

        Args:
            task_id (str): 任务ID
            user (str): 用户标识
            **kwargs: 额外的请求参数，如timeout、max_retries等

        Returns:
            Dict[str, Any]: 停止任务的响应数据

        Raises:
            DifyAPIError: 当API请求失败时
        """
        endpoint = f"workflows/tasks/{task_id}/stop"
        payload = {"user": user}
        return self.post(endpoint, json_data=payload, **kwargs)

    def get_logs(
        self,
        keyword: str = None,
        status: str = None,
        page: int = 1,
        limit: int = 20,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        获取工作流执行日志。

        Args:
            keyword (str, optional): 搜索关键词
            status (str, optional): 执行状态，'succeeded'、'failed'或'stopped'
            page (int, optional): 页码，默认为1
            limit (int, optional): 每页数量，默认为20
            **kwargs: 额外的请求参数，如timeout、max_retries等

        Returns:
            Dict[str, Any]: 日志数据

        Raises:
            DifyAPIError: 当API请求失败时
        """
        params = {"page": page, "limit": limit}
        if keyword:
            params["keyword"] = keyword
        if status:
            params["status"] = status

        return self.get("workflows/logs", params=params, **kwargs)

    def process_streaming_response(
        self,
        stream_generator: Generator[Dict[str, Any], None, None],
        handle_workflow_started=None,
        handle_node_started=None,
        handle_node_finished=None,
        handle_workflow_finished=None,
        handle_tts_message=None,
        handle_tts_message_end=None,
        handle_ping=None,
    ) -> Dict[str, Any]:
        """
        处理流式响应，调用相应事件处理器。

        Args:
            stream_generator: 流式响应生成器
            handle_workflow_started: 工作流开始事件处理函数
            handle_node_started: 节点开始事件处理函数
            handle_node_finished: 节点完成事件处理函数
            handle_workflow_finished: 工作流完成事件处理函数
            handle_tts_message: TTS消息事件处理函数
            handle_tts_message_end: TTS消息结束事件处理函数
            handle_ping: ping事件处理函数

        Returns:
            Dict[str, Any]: 最终工作流结果

        示例:
            ```python
            def on_workflow_started(data):
                print(f"工作流开始: {data['id']}")

            def on_node_finished(data):
                print(f"节点完成: {data['node_id']}, 状态: {data['status']}")

            def on_workflow_finished(data):
                print(f"工作流完成: {data['id']}, 状态: {data['status']}")

            client = WorkflowClient(api_key)
            stream = client.run(inputs={"prompt": "你好"}, user="user123")
            result = client.process_streaming_response(
                stream,
                handle_workflow_started=on_workflow_started,
                handle_node_finished=on_node_finished,
                handle_workflow_finished=on_workflow_finished
            )
            ```
        """
        final_result = {}

        for chunk in stream_generator:
            event = chunk.get("event")

            if event == "workflow_started" and handle_workflow_started:
                handle_workflow_started(chunk.get("data", {}))

            elif event == "node_started" and handle_node_started:
                handle_node_started(chunk.get("data", {}))

            elif event == "node_finished" and handle_node_finished:
                handle_node_finished(chunk.get("data", {}))

            elif event == "workflow_finished" and handle_workflow_finished:
                data = chunk.get("data", {})
                if handle_workflow_finished:
                    handle_workflow_finished(data)
                final_result = data

            elif event == "tts_message" and handle_tts_message:
                handle_tts_message(chunk)

            elif event == "tts_message_end" and handle_tts_message_end:
                handle_tts_message_end(chunk)

            elif event == "ping" and handle_ping:
                handle_ping(chunk)

        return final_result

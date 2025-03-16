"""
Pydify - Dify Workflow应用客户端

此模块提供与Dify Workflow应用API交互的客户端。
"""

import os
import json
from typing import Dict, Any, List, Optional, Union, Generator, BinaryIO, Tuple

from .common import DifyBaseClient


class WorkflowClient(DifyBaseClient):
    """Dify Workflow应用客户端类。

    提供与Dify Workflow应用API交互的方法，包括执行工作流、停止响应、上传文件和获取日志等功能。
    """

    def run(
        self,
        inputs: Dict[str, Any],
        user: str,
        response_mode: str = "streaming",
        files: List[Dict[str, Any]] = None,
    ) -> Union[Dict[str, Any], Generator[Dict[str, Any], None, None]]:
        """
        执行工作流。

        Args:
            inputs (Dict[str, Any]): 工作流输入变量
            user (str): 用户标识
            response_mode (str, optional): 响应模式，'streaming'（流式）或'blocking'（阻塞）。默认为'streaming'。
            files (List[Dict[str, Any]], optional): 文件列表，每个文件为一个字典，包含类型、传递方式和URL/ID。

        Returns:
            Union[Dict[str, Any], Generator[Dict[str, Any], None, None]]:
                如果response_mode为'blocking'，返回完整响应字典；
                如果response_mode为'streaming'，返回字典生成器。

        Raises:
            ValueError: 当提供了无效的参数时
            requests.HTTPError: 当API请求失败时
        """
        if response_mode not in ["streaming", "blocking"]:
            raise ValueError("response_mode must be 'streaming' or 'blocking'")

        payload = {
            "inputs": inputs,
            "response_mode": response_mode,
            "user": user,
        }

        if files:
            payload["files"] = files

        endpoint = "workflows/run"

        if response_mode == "streaming":
            return self.post_stream(endpoint, json_data=payload)
        else:
            return self.post(endpoint, json_data=payload)

    def stop_task(self, task_id: str, user: str) -> Dict[str, Any]:
        """
        停止正在执行的工作流任务。

        Args:
            task_id (str): 任务ID
            user (str): 用户标识

        Returns:
            Dict[str, Any]: 停止任务的响应数据

        Raises:
            requests.HTTPError: 当API请求失败时
        """
        endpoint = f"workflows/tasks/{task_id}/stop"
        payload = {"user": user}
        return self.post(endpoint, json_data=payload)

    def upload_file(self, file_path: str, user: str) -> Dict[str, Any]:
        """
        上传文件到Dify API。

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
        
        return super().upload_file(file_path, user)
    
    def upload_file_obj(self, file_obj: BinaryIO, filename: str, user: str) -> Dict[str, Any]:
        """
        上传文件对象到Dify API。

        Args:
            file_obj (BinaryIO): 文件对象
            filename (str): 文件名
            user (str): 用户标识

        Returns:
            Dict[str, Any]: 上传文件的响应数据

        Raises:
            requests.HTTPError: 当API请求失败时
        """
        files = {'file': (filename, file_obj)}
        data = {'user': user}
        url = os.path.join(self.base_url, 'files/upload')
        
        headers = self._get_headers()
        # 移除Content-Type，让requests自动设置multipart/form-data
        headers.pop('Content-Type', None)
        
        response = self._request("POST", 'files/upload', headers=headers, files=files, data=data)
        return response.json()

    def get_logs(
        self,
        keyword: str = None,
        status: str = None,
        page: int = 1,
        limit: int = 20,
    ) -> Dict[str, Any]:
        """
        获取工作流执行日志。

        Args:
            keyword (str, optional): 搜索关键词
            status (str, optional): 执行状态，'succeeded'、'failed'或'stopped'
            page (int, optional): 页码，默认为1
            limit (int, optional): 每页数量，默认为20

        Returns:
            Dict[str, Any]: 日志数据

        Raises:
            requests.HTTPError: 当API请求失败时
        """
        params = {"page": page, "limit": limit}
        if keyword:
            params["keyword"] = keyword
        if status:
            params["status"] = status

        return self.get("workflows/logs", params=params)

    def get_app_info(self) -> Dict[str, Any]:
        """
        获取应用基本信息。

        Returns:
            Dict[str, Any]: 应用信息数据

        Raises:
            requests.HTTPError: 当API请求失败时
        """
        return self.get("info")

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

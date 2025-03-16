"""
Pydify - Dify Text Generation应用客户端

此模块提供与Dify Text Generation应用API交互的客户端。
Text Generation文本生成应用无会话支持，适合用于翻译、文章写作、总结等AI任务。
"""

import os
import json
import mimetypes
from typing import Dict, Any, List, Optional, Union, Generator, BinaryIO, Tuple

from .common import DifyBaseClient


class TextGenerationClient(DifyBaseClient):
    """Dify Text Generation应用客户端类。
    
    提供与Dify Text Generation应用API交互的方法，包括发送消息、
    上传文件、文字转语音等功能。Text Generation应用无会话支持，
    适合用于翻译、文章写作、总结等AI任务。
    """
    
    def completion(
        self,
        query: str,
        user: str,
        response_mode: str = "streaming",
        inputs: Dict[str, Any] = None,
        files: List[Dict[str, Any]] = None,
    ) -> Union[Dict[str, Any], Generator[Dict[str, Any], None, None]]:
        """
        发送消息给文本生成应用。
        
        Args:
            query (str): 用户输入/提问内容，将作为inputs的query字段
            user (str): 用户标识，用于定义终端用户的身份
            response_mode (str, optional): 响应模式，'streaming'（流式）或'blocking'（阻塞）。默认为'streaming'
            inputs (Dict[str, Any], optional): 额外的输入参数。默认为None，若提供，会与query合并
            files (List[Dict[str, Any]], optional): 要包含在消息中的文件列表，每个文件为一个字典。默认为None
            
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
            
        # 准备inputs，确保包含query
        if inputs is None:
            inputs = {}
        
        # 如果inputs中没有query字段，则添加
        if "query" not in inputs:
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
            return self.post_stream(endpoint, json_data=payload)
        else:
            return self.post(endpoint, json_data=payload)
            
    def stop_completion(self, task_id: str, user: str) -> Dict[str, Any]:
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
        endpoint = f"completion-messages/{task_id}/stop"
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
        supported_extensions = ['png', 'jpg', 'jpeg', 'webp', 'gif']
        file_extension = os.path.splitext(file_path)[1].lower().replace('.', '')
        
        if file_extension not in supported_extensions:
            raise ValueError(f"Unsupported file type. Supported types: {supported_extensions}")
            
        with open(file_path, 'rb') as file:
            files = {'file': file}
            data = {'user': user}
            
            headers = self._get_headers()
            # 移除Content-Type，让requests自动设置multipart/form-data
            headers.pop('Content-Type', None)
            
            response = self._request("POST", 'files/upload', headers=headers, files=files, data=data)
            return response.json()
            
    def upload_file_obj(self, file_obj: BinaryIO, filename: str, user: str) -> Dict[str, Any]:
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
        supported_extensions = ['png', 'jpg', 'jpeg', 'webp', 'gif']
        file_extension = os.path.splitext(filename)[1].lower().replace('.', '')
        
        if file_extension not in supported_extensions:
            raise ValueError(f"Unsupported file type. Supported types: {supported_extensions}")
            
        files = {'file': (filename, file_obj)}
        data = {'user': user}
        
        headers = self._get_headers()
        # 移除Content-Type，让requests自动设置multipart/form-data
        headers.pop('Content-Type', None)
        
        response = self._request("POST", 'files/upload', headers=headers, files=files, data=data)
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
        
    def process_streaming_response(
        self,
        stream_generator: Generator[Dict[str, Any], None, None],
        handle_message=None,
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
            handle_message_end: 消息结束事件处理函数
            handle_tts_message: TTS音频流事件处理函数
            handle_tts_message_end: TTS音频流结束事件处理函数
            handle_message_replace: 消息内容替换事件处理函数
            handle_error: 错误事件处理函数
            handle_ping: ping事件处理函数
            break_on_error: 当遇到错误时是否中断处理，默认为True
            
        Returns:
            Dict[str, Any]: 处理结果，包含消息ID等信息
            
        示例:
            ```python
            def on_message(chunk):
                print(f"收到文本块: {chunk['answer']}")
                
            def on_message_end(chunk):
                print(f"消息结束: ID={chunk['message_id']}")
                
            client = TextGenerationClient(api_key)
            stream = client.completion(
                query="写一篇关于人工智能的短文",
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
                # 保存消息ID
                if "message_id" in chunk and not result.get("message_id"):
                    result["message_id"] = chunk["message_id"]
                if "task_id" in chunk and not result.get("task_id"):
                    result["task_id"] = chunk["task_id"]
                
            elif event == "message_end" and handle_message_end:
                if handle_message_end:
                    handle_message_end(chunk)
                # 保存元数据
                if "metadata" in chunk:
                    result["metadata"] = chunk["metadata"]
                if "message_id" in chunk and not result.get("message_id"):
                    result["message_id"] = chunk["message_id"]
                
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
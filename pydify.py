import requests
import json
import os
import time
from typing import Dict, List, Optional, Union, Any, BinaryIO, Callable, Generator
import logging
import asyncio
import aiohttp
from enum import Enum, auto
from pathlib import Path
import io
import mimetypes

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('DifyClient')

class ResponseMode(Enum):
    """响应模式枚举"""
    STREAMING = "streaming"  # 流式模式
    BLOCKING = "blocking"    # 阻塞模式

class FileType(Enum):
    """文件类型枚举"""
    # 文档类型
    DOCUMENT = "document"
    # 图片类型
    IMAGE = "image"
    # 音频类型
    AUDIO = "audio"
    # 视频类型
    VIDEO = "video"
    # 自定义类型
    CUSTOM = "custom"

class TransferMethod(Enum):
    """文件传输方式枚举"""
    REMOTE_URL = "remote_url"  # 远程URL
    LOCAL_FILE = "local_file"  # 本地文件

class MessageRating(Enum):
    """消息评分枚举"""
    LIKE = "like"        # 点赞
    DISLIKE = "dislike"  # 点踩
    NONE = None          # 取消评分

class DifyApiError(Exception):
    """Dify API 错误类"""
    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message
        super().__init__(f"Dify API 错误 (状态码: {status_code}): {message}")

class DifyClient:
    """Dify API 客户端类"""
    
    def __init__(self, api_key: str, base_url: str = "https://api.dify.ai/v1"):
        """
        初始化 Dify 客户端
        
        Args:
            api_key (str): API密钥
            base_url (str, optional): API基础URL, 默认为"https://api.dify.ai/v1"
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")  # 移除结尾的斜杠以确保URL格式一致
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        logger.info(f"初始化 Dify 客户端，基础URL: {self.base_url}")
    
    def _handle_response(self, response: requests.Response) -> Dict:
        """
        处理API响应，检查错误
        
        Args:
            response (requests.Response): API响应对象
            
        Returns:
            Dict: 响应JSON数据
            
        Raises:
            DifyApiError: 如果API返回错误
        """
        if 200 <= response.status_code < 300:
            if response.content:
                try:
                    return response.json()
                except json.JSONDecodeError:
                    return {"status": "success", "data": response.text}
            else:
                return {"status": "success"}
        
        error_message = "未知错误"
        try:
            error_data = response.json()
            if "error" in error_data:
                error_message = error_data["error"]
            elif "message" in error_data:
                error_message = error_data["message"]
        except Exception:
            error_message = response.text or "无法解析错误信息"
        
        raise DifyApiError(response.status_code, error_message)
    
    def run_workflow(
        self, 
        inputs: Dict[str, Any] = None, 
        response_mode: ResponseMode = ResponseMode.BLOCKING, 
        user: str = "anonymous",
        files: List[Dict] = None
    ) -> Union[Dict, str]:
        """
        执行工作流
        
        Args:
            inputs (Dict[str, Any], optional): 工作流输入参数
            response_mode (ResponseMode, optional): 响应模式，默认为阻塞模式
            user (str, optional): 用户标识，默认为"anonymous"
            files (List[Dict], optional): 文件列表
            
        Returns:
            Union[Dict, str]: 阻塞模式返回结果字典，流式模式返回事件流文本
        """
        url = f"{self.base_url}/workflows/run"
        
        if inputs is None:
            inputs = {}
        
        data = {
            "inputs": inputs,
            "response_mode": response_mode.value,
            "user": user
        }
        
        if files:
            data["files"] = files
        
        logger.info(f"执行工作流，用户: {user}, 响应模式: {response_mode.value}")
        
        if response_mode == ResponseMode.BLOCKING:
            response = requests.post(url, headers=self.headers, json=data)
            return self._handle_response(response)
        else:
            # 流式模式
            response = requests.post(url, headers=self.headers, json=data, stream=True)
            
            if response.status_code != 200:
                self._handle_response(response)  # 出错时会抛出异常
            
            return response.iter_lines(decode_unicode=True)
    
    async def run_workflow_async(
        self, 
        inputs: Dict[str, Any] = None, 
        response_mode: ResponseMode = ResponseMode.STREAMING, 
        user: str = "anonymous",
        files: List[Dict] = None,
        callback = None
    ) -> Union[Dict, None]:
        """
        异步执行工作流
        
        Args:
            inputs (Dict[str, Any], optional): 工作流输入参数
            response_mode (ResponseMode, optional): 响应模式，默认为流式模式
            user (str, optional): 用户标识，默认为"anonymous"
            files (List[Dict], optional): 文件列表
            callback (callable, optional): 回调函数，用于流式响应模式
            
        Returns:
            Union[Dict, None]: 阻塞模式返回结果字典，流式模式（有回调）返回None
        """
        url = f"{self.base_url}/workflows/run"
        
        if inputs is None:
            inputs = {}
        
        data = {
            "inputs": inputs,
            "response_mode": response_mode.value,
            "user": user
        }
        
        if files:
            data["files"] = files
        
        logger.info(f"异步执行工作流，用户: {user}, 响应模式: {response_mode.value}")
        
        async with aiohttp.ClientSession() as session:
            headers = dict(self.headers)
            
            if response_mode == ResponseMode.BLOCKING:
                async with session.post(url, headers=headers, json=data) as response:
                    if response.status != 200:
                        text = await response.text()
                        raise DifyApiError(response.status, text)
                    
                    result = await response.json()
                    return result
            else:
                # 流式模式
                async with session.post(url, headers=headers, json=data) as response:
                    if response.status != 200:
                        text = await response.text()
                        raise DifyApiError(response.status, text)
                    
                    async for line in response.content.iter_any():
                        line = line.decode('utf-8')
                        if line.startswith('data: '):
                            data = line[6:]  # 移除 'data: ' 前缀
                            if callback:
                                try:
                                    event_data = json.loads(data)
                                    await callback(event_data)
                                except json.JSONDecodeError:
                                    logger.error(f"解析事件数据失败: {data}")
        
        return None
    
    def process_streaming_response(self, response_stream):
        """
        处理流式响应，转换为更易于处理的事件列表
        
        Args:
            response_stream: 响应流迭代器
            
        Returns:
            List[Dict]: 事件数据列表
        """
        events = []
        for line in response_stream:
            if line.startswith('data: '):
                data = line[6:]  # 移除 'data: ' 前缀
                try:
                    event_data = json.loads(data)
                    events.append(event_data)
                except json.JSONDecodeError:
                    logger.error(f"解析事件数据失败: {data}")
        
        return events
    
    def upload_file(self, file_path: str, user: str, file_type: Optional[str] = None) -> Dict:
        """
        上传文件
        
        Args:
            file_path (str): 文件路径
            user (str): 用户标识
            file_type (str, optional): 文件类型，默认为None(自动检测)
            
        Returns:
            Dict: 上传结果，包含文件ID和其他信息
        """
        url = f"{self.base_url}/files/upload"
        headers = {
            "Authorization": f"Bearer {self.api_key}"
            # 注意：不要设置 Content-Type，requests 会自动设置正确的 multipart/form-data
        }
        
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        # 自动检测文件类型
        if file_type is None:
            ext = file_path.suffix.lower().lstrip('.')
            # 根据文件扩展名确定文件类型
            document_exts = ['txt', 'md', 'markdown', 'pdf', 'html', 'xlsx', 'xls', 
                             'docx', 'csv', 'eml', 'msg', 'pptx', 'ppt', 'xml', 'epub']
            image_exts = ['jpg', 'jpeg', 'png', 'gif', 'webp', 'svg']
            audio_exts = ['mp3', 'm4a', 'wav', 'webm', 'amr']
            video_exts = ['mp4', 'mov', 'mpeg', 'mpga']
            
            if ext in document_exts:
                file_type = ext.upper()
            elif ext in image_exts:
                file_type = ext.upper()
            elif ext in audio_exts:
                file_type = ext.upper()
            elif ext in video_exts:
                file_type = ext.upper()
            else:
                file_type = "TXT"  # 默认文本类型
        
        logger.info(f"上传文件: {file_path}, 类型: {file_type}, 用户: {user}")
        
        # 准备表单数据
        with open(file_path, 'rb') as f:
            files = {
                'file': (file_path.name, f, f'text/{file_type.lower()}')
            }
            data = {
                'user': user,
                'type': file_type,
            }
            
            response = requests.post(url, headers=headers, files=files, data=data)
            return self._handle_response(response)
    
    async def upload_file_async(self, file_path: str, user: str, file_type: Optional[str] = None) -> Dict:
        """
        异步上传文件
        
        Args:
            file_path (str): 文件路径
            user (str): 用户标识
            file_type (str, optional): 文件类型，默认为None(自动检测)
            
        Returns:
            Dict: 上传结果，包含文件ID和其他信息
        """
        url = f"{self.base_url}/files/upload"
        headers = {
            "Authorization": f"Bearer {self.api_key}"
            # 注意：不要设置 Content-Type，aiohttp 会自动设置正确的 multipart/form-data
        }
        
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        # 自动检测文件类型（与同步方法相同）
        if file_type is None:
            ext = file_path.suffix.lower().lstrip('.')
            document_exts = ['txt', 'md', 'markdown', 'pdf', 'html', 'xlsx', 'xls', 
                            'docx', 'csv', 'eml', 'msg', 'pptx', 'ppt', 'xml', 'epub']
            image_exts = ['jpg', 'jpeg', 'png', 'gif', 'webp', 'svg']
            audio_exts = ['mp3', 'm4a', 'wav', 'webm', 'amr']
            video_exts = ['mp4', 'mov', 'mpeg', 'mpga']
            
            if ext in document_exts:
                file_type = ext.upper()
            elif ext in image_exts:
                file_type = ext.upper()
            elif ext in audio_exts:
                file_type = ext.upper()
            elif ext in video_exts:
                file_type = ext.upper()
            else:
                file_type = "TXT"  # 默认文本类型
        
        logger.info(f"异步上传文件: {file_path}, 类型: {file_type}, 用户: {user}")
        
        # 准备表单数据
        data = aiohttp.FormData()
        data.add_field('user', user)
        data.add_field('type', file_type)
        
        # 添加文件
        with open(file_path, 'rb') as f:
            data.add_field('file', 
                          f, 
                          filename=file_path.name, 
                          content_type=f'text/{file_type.lower()}')
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, data=data) as response:
                    if response.status != 201:  # 上传接口返回 201 Created
                        text = await response.text()
                        raise DifyApiError(response.status, text)
                    
                    result = await response.json()
                    return result
    
    def get_workflow_status(self, workflow_id: str) -> Dict:
        """
        获取工作流执行状态
        
        Args:
            workflow_id (str): 工作流执行ID
            
        Returns:
            Dict: 工作流执行状态信息
        """
        url = f"{self.base_url}/workflows/run/{workflow_id}"
        
        logger.info(f"获取工作流状态: {workflow_id}")
        
        response = requests.get(url, headers=self.headers)
        return self._handle_response(response)
    
    def stop_workflow(self, task_id: str, user: str) -> Dict:
        """
        停止工作流执行
        
        Args:
            task_id (str): 任务ID
            user (str): 用户标识
            
        Returns:
            Dict: 停止结果
        """
        url = f"{self.base_url}/workflows/tasks/{task_id}/stop"
        
        data = {
            "user": user
        }
        
        logger.info(f"停止工作流任务: {task_id}, 用户: {user}")
        
        response = requests.post(url, headers=self.headers, json=data)
        return self._handle_response(response)
    
    def get_workflow_logs(
        self, 
        keyword: Optional[str] = None,
        status: Optional[str] = None,
        page: int = 1,
        limit: int = 20
    ) -> Dict:
        """
        获取工作流日志
        
        Args:
            keyword (str, optional): 关键字过滤
            status (str, optional): 状态过滤，如 "succeeded"/"failed"/"stopped"
            page (int, optional): 页码，默认为1
            limit (int, optional): 每页条数，默认为20
            
        Returns:
            Dict: 工作流日志
        """
        url = f"{self.base_url}/workflows/logs"
        
        params = {
            "page": page,
            "limit": limit
        }
        
        if keyword:
            params["keyword"] = keyword
        
        if status:
            params["status"] = status
        
        logger.info(f"获取工作流日志，页码: {page}, 条数: {limit}")
        
        response = requests.get(url, headers=self.headers, params=params)
        return self._handle_response(response)
    
    def get_app_info(self) -> Dict:
        """
        获取应用基本信息
        
        Returns:
            Dict: 应用信息
        """
        url = f"{self.base_url}/info"
        
        logger.info("获取应用基本信息")
        
        response = requests.get(url, headers=self.headers)
        return self._handle_response(response)
    
    def get_app_parameters(self) -> Dict:
        """
        获取应用参数
        
        Returns:
            Dict: 应用参数
        """
        url = f"{self.base_url}/parameters"
        
        logger.info("获取应用参数")
        
        response = requests.get(url, headers=self.headers)
        return self._handle_response(response)
    
    def create_file_input(
        self, 
        file_id: str, 
        file_type: FileType = FileType.DOCUMENT,
        transfer_method: TransferMethod = TransferMethod.LOCAL_FILE
    ) -> Dict:
        """
        创建文件输入参数
        
        Args:
            file_id (str): 文件ID
            file_type (FileType, optional): 文件类型，默认为文档类型
            transfer_method (TransferMethod, optional): 传输方式，默认为本地文件
            
        Returns:
            Dict: 文件输入参数
        """
        return {
            "transfer_method": transfer_method.value,
            "upload_file_id": file_id,
            "type": file_type.value
        }
    
    def create_url_input(
        self, 
        url: str, 
        file_type: FileType = FileType.IMAGE,
        transfer_method: TransferMethod = TransferMethod.REMOTE_URL
    ) -> Dict:
        """
        创建URL输入参数
        
        Args:
            url (str): 文件URL
            file_type (FileType, optional): 文件类型，默认为图片类型
            transfer_method (TransferMethod, optional): 传输方式，默认为远程URL
            
        Returns:
            Dict: URL输入参数
        """
        return {
            "transfer_method": transfer_method.value,
            "url": url,
            "type": file_type.value
        }

class DifyChatClient:
    """Dify 聊天 API 客户端类"""
    
    def __init__(self, api_key: str, base_url: str = "http://sandanapp.com/v1"):
        """
        初始化 Dify 聊天客户端
        
        Args:
            api_key (str): API密钥
            base_url (str, optional): API基础URL, 默认为"http://sandanapp.com/v1"
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")  # 移除结尾的斜杠以确保URL格式一致
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        logger.info(f"初始化 Dify 聊天客户端，基础URL: {self.base_url}")
    
    def _handle_response(self, response: requests.Response) -> Dict:
        """
        处理API响应，检查错误
        
        Args:
            response (requests.Response): API响应对象
            
        Returns:
            Dict: 响应JSON数据
            
        Raises:
            DifyApiError: 如果API返回错误
        """
        if 200 <= response.status_code < 300:
            if response.content:
                try:
                    return response.json()
                except json.JSONDecodeError:
                    return {"status": "success", "data": response.text}
            else:
                return {"status": "success"}
        
        error_message = "未知错误"
        try:
            error_data = response.json()
            if "error" in error_data:
                error_message = error_data["error"]
            elif "message" in error_data:
                error_message = error_data["message"]
        except Exception:
            error_message = response.text or "无法解析错误信息"
        
        raise DifyApiError(response.status_code, error_message)

    def send_chat_message(
        self,
        query: str,
        inputs: Dict[str, Any] = None,
        response_mode: ResponseMode = ResponseMode.BLOCKING,
        user: str = "user",
        conversation_id: str = None,
        files: List[Dict] = None,
        auto_generate_name: bool = True
    ) -> Union[Dict, Generator]:
        """
        发送聊天消息
        
        Args:
            query (str): 用户输入/提问内容
            inputs (Dict[str, Any], optional): 允许传入 App 定义的各变量值
            response_mode (ResponseMode, optional): 响应模式，默认为阻塞模式
            user (str, optional): 用户标识
            conversation_id (str, optional): 会话 ID
            files (List[Dict], optional): 上传的文件列表
            auto_generate_name (bool, optional): 自动生成标题
            
        Returns:
            Union[Dict, Generator]: 阻塞模式返回结果字典，流式模式返回事件生成器
        """
        url = f"{self.base_url}/chat-messages"
        
        if inputs is None:
            inputs = {}
        
        data = {
            "query": query,
            "inputs": inputs,
            "response_mode": response_mode.value,
            "user": user,
            "auto_generate_name": auto_generate_name
        }
        
        if conversation_id:
            data["conversation_id"] = conversation_id
        
        if files:
            data["files"] = files
        
        logger.info(f"发送聊天消息，用户: {user}, 响应模式: {response_mode.value}")
        
        if response_mode == ResponseMode.BLOCKING:
            response = requests.post(url, headers=self.headers, json=data)
            return self._handle_response(response)
        else:
            # 流式模式
            response = requests.post(url, headers=self.headers, json=data, stream=True)
            
            if response.status_code != 200:
                self._handle_response(response)  # 出错时会抛出异常
            
            def generate_events():
                for line in response.iter_lines(decode_unicode=True):
                    if line.startswith('data: '):
                        data = line[6:]  # 移除 'data: ' 前缀
                        try:
                            event_data = json.loads(data)
                            yield event_data
                        except json.JSONDecodeError:
                            logger.error(f"解析事件数据失败: {data}")
            
            return generate_events()
    
    async def send_chat_message_async(
        self,
        query: str,
        inputs: Dict[str, Any] = None,
        response_mode: ResponseMode = ResponseMode.STREAMING,
        user: str = "user",
        conversation_id: str = None,
        files: List[Dict] = None,
        auto_generate_name: bool = True,
        callback: Callable = None
    ) -> Union[Dict, None]:
        """
        异步发送聊天消息
        
        Args:
            query (str): 用户输入/提问内容
            inputs (Dict[str, Any], optional): 允许传入 App 定义的各变量值
            response_mode (ResponseMode, optional): 响应模式，默认为流式模式
            user (str, optional): 用户标识
            conversation_id (str, optional): 会话 ID
            files (List[Dict], optional): 上传的文件列表
            auto_generate_name (bool, optional): 自动生成标题
            callback (callable, optional): 回调函数，用于流式响应模式
            
        Returns:
            Union[Dict, None]: 阻塞模式返回结果字典，流式模式（有回调）返回None
        """
        url = f"{self.base_url}/chat-messages"
        
        if inputs is None:
            inputs = {}
        
        data = {
            "query": query,
            "inputs": inputs,
            "response_mode": response_mode.value,
            "user": user,
            "auto_generate_name": auto_generate_name
        }
        
        if conversation_id:
            data["conversation_id"] = conversation_id
        
        if files:
            data["files"] = files
        
        logger.info(f"异步发送聊天消息，用户: {user}, 响应模式: {response_mode.value}")
        
        async with aiohttp.ClientSession() as session:
            headers = dict(self.headers)
            
            if response_mode == ResponseMode.BLOCKING:
                async with session.post(url, headers=headers, json=data) as response:
                    if response.status != 200:
                        text = await response.text()
                        raise DifyApiError(response.status, text)
                    
                    result = await response.json()
                    return result
            else:
                # 流式模式
                async with session.post(url, headers=headers, json=data) as response:
                    if response.status != 200:
                        text = await response.text()
                        raise DifyApiError(response.status, text)
                    
                    async for line in response.content.iter_any():
                        line = line.decode('utf-8')
                        if line.startswith('data: '):
                            data = line[6:]  # 移除 'data: ' 前缀
                            if callback:
                                try:
                                    event_data = json.loads(data)
                                    await callback(event_data)
                                except json.JSONDecodeError:
                                    logger.error(f"解析事件数据失败: {data}")
        
        return None
    
    def upload_file(self, file_path: str, user: str) -> Dict:
        """
        上传文件
        
        Args:
            file_path (str): 文件路径
            user (str): 用户标识
            
        Returns:
            Dict: 上传结果，包含文件ID和其他信息
        """
        url = f"{self.base_url}/files/upload"
        headers = {
            "Authorization": f"Bearer {self.api_key}"
            # 注意：不要设置 Content-Type，requests 会自动设置正确的 multipart/form-data
        }
        
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        # 获取MIME类型
        mime_type, _ = mimetypes.guess_type(str(file_path))
        if not mime_type:
            mime_type = 'application/octet-stream'
        
        logger.info(f"上传文件: {file_path}, MIME类型: {mime_type}, 用户: {user}")
        
        # 准备表单数据
        with open(file_path, 'rb') as f:
            files = {
                'file': (file_path.name, f, mime_type)
            }
            data = {
                'user': user
            }
            
            response = requests.post(url, headers=headers, files=files, data=data)
            return self._handle_response(response)
    
    def upload_file_content(self, file_content: BinaryIO, filename: str, user: str, mime_type: str = None) -> Dict:
        """
        上传文件内容
        
        Args:
            file_content (BinaryIO): 文件内容（文件对象或二进制数据）
            filename (str): 文件名
            user (str): 用户标识
            mime_type (str, optional): MIME类型，如果不提供会根据文件名猜测
            
        Returns:
            Dict: 上传结果，包含文件ID和其他信息
        """
        url = f"{self.base_url}/files/upload"
        headers = {
            "Authorization": f"Bearer {self.api_key}"
        }
        
        # 获取MIME类型
        if not mime_type:
            mime_type, _ = mimetypes.guess_type(filename)
            if not mime_type:
                mime_type = 'application/octet-stream'
        
        logger.info(f"上传文件内容: {filename}, MIME类型: {mime_type}, 用户: {user}")
        
        # 准备表单数据
        files = {
            'file': (filename, file_content, mime_type)
        }
        data = {
            'user': user
        }
        
        response = requests.post(url, headers=headers, files=files, data=data)
        return self._handle_response(response)
    
    async def upload_file_async(self, file_path: str, user: str) -> Dict:
        """
        异步上传文件
        
        Args:
            file_path (str): 文件路径
            user (str): 用户标识
            
        Returns:
            Dict: 上传结果，包含文件ID和其他信息
        """
        url = f"{self.base_url}/files/upload"
        headers = {
            "Authorization": f"Bearer {self.api_key}"
        }
        
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        # 获取MIME类型
        mime_type, _ = mimetypes.guess_type(str(file_path))
        if not mime_type:
            mime_type = 'application/octet-stream'
        
        logger.info(f"异步上传文件: {file_path}, MIME类型: {mime_type}, 用户: {user}")
        
        # 准备表单数据
        data = aiohttp.FormData()
        data.add_field('user', user)
        
        # 添加文件
        with open(file_path, 'rb') as f:
            data.add_field('file', 
                          f, 
                          filename=file_path.name, 
                          content_type=mime_type)
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, data=data) as response:
                    if response.status != 200:
                        text = await response.text()
                        raise DifyApiError(response.status, text)
                    
                    result = await response.json()
                    return result
    
    def stop_chat_response(self, task_id: str, user: str) -> Dict:
        """
        停止聊天响应
        
        Args:
            task_id (str): 任务ID
            user (str): 用户标识
            
        Returns:
            Dict: 停止结果
        """
        url = f"{self.base_url}/chat-messages/{task_id}/stop"
        
        data = {
            "user": user
        }
        
        logger.info(f"停止聊天响应: {task_id}, 用户: {user}")
        
        response = requests.post(url, headers=self.headers, json=data)
        return self._handle_response(response)
    
    def send_message_feedback(
        self, 
        message_id: str, 
        rating: MessageRating, 
        user: str,
        content: str = None
    ) -> Dict:
        """
        发送消息反馈
        
        Args:
            message_id (str): 消息ID
            rating (MessageRating): 评分（点赞/点踩/取消）
            user (str): 用户标识
            content (str, optional): 反馈内容
            
        Returns:
            Dict: 反馈结果
        """
        url = f"{self.base_url}/messages/{message_id}/feedbacks"
        
        data = {
            "rating": rating.value,
            "user": user
        }
        
        if content:
            data["content"] = content
        
        logger.info(f"发送消息反馈: {message_id}, 评分: {rating.value}, 用户: {user}")
        
        response = requests.post(url, headers=self.headers, json=data)
        return self._handle_response(response)
    
    def get_suggested_questions(self, message_id: str, user: str) -> Dict:
        """
        获取下一轮建议问题列表
        
        Args:
            message_id (str): 消息ID
            user (str): 用户标识
            
        Returns:
            Dict: 建议问题列表
        """
        url = f"{self.base_url}/messages/{message_id}/suggested"
        
        params = {
            "user": user
        }
        
        logger.info(f"获取建议问题: {message_id}, 用户: {user}")
        
        response = requests.get(url, headers=self.headers, params=params)
        return self._handle_response(response)
    
    def get_conversation_messages(
        self, 
        conversation_id: str, 
        user: str, 
        first_id: str = None, 
        limit: int = 20
    ) -> Dict:
        """
        获取会话历史消息
        
        Args:
            conversation_id (str): 会话ID
            user (str): 用户标识
            first_id (str, optional): 当前页第一条消息的ID
            limit (int, optional): 每页消息数量
            
        Returns:
            Dict: 历史消息列表
        """
        url = f"{self.base_url}/messages"
        
        params = {
            "conversation_id": conversation_id,
            "user": user,
            "limit": limit
        }
        
        if first_id:
            params["first_id"] = first_id
        
        logger.info(f"获取会话消息: {conversation_id}, 用户: {user}, 数量: {limit}")
        
        response = requests.get(url, headers=self.headers, params=params)
        return self._handle_response(response)
    
    def get_conversations(
        self, 
        user: str, 
        last_id: str = None, 
        limit: int = 20,
        sort_by: str = "-updated_at"
    ) -> Dict:
        """
        获取会话列表
        
        Args:
            user (str): 用户标识
            last_id (str, optional): 最后一条记录的ID
            limit (int, optional): 每页数量
            sort_by (str, optional): 排序字段
            
        Returns:
            Dict: 会话列表
        """
        url = f"{self.base_url}/conversations"
        
        params = {
            "user": user,
            "limit": limit,
            "sort_by": sort_by
        }
        
        if last_id:
            params["last_id"] = last_id
        
        logger.info(f"获取会话列表, 用户: {user}, 数量: {limit}")
        
        response = requests.get(url, headers=self.headers, params=params)
        return self._handle_response(response)
    
    def delete_conversation(self, conversation_id: str, user: str) -> Dict:
        """
        删除会话
        
        Args:
            conversation_id (str): 会话ID
            user (str): 用户标识
            
        Returns:
            Dict: 删除结果
        """
        url = f"{self.base_url}/conversations/{conversation_id}"
        
        data = {
            "user": user
        }
        
        logger.info(f"删除会话: {conversation_id}, 用户: {user}")
        
        response = requests.delete(url, headers=self.headers, json=data)
        return self._handle_response(response)
    
    def rename_conversation(
        self, 
        conversation_id: str, 
        user: str,
        name: str = None,
        auto_generate: bool = False
    ) -> Dict:
        """
        重命名会话
        
        Args:
            conversation_id (str): 会话ID
            user (str): 用户标识
            name (str, optional): 新名称
            auto_generate (bool, optional): 是否自动生成名称
            
        Returns:
            Dict: 重命名结果
        """
        url = f"{self.base_url}/conversations/{conversation_id}/name"
        
        data = {
            "user": user,
            "auto_generate": auto_generate
        }
        
        if name:
            data["name"] = name
        
        logger.info(f"重命名会话: {conversation_id}, 用户: {user}")
        
        response = requests.post(url, headers=self.headers, json=data)
        return self._handle_response(response)
    
    def audio_to_text(self, file_path: str, user: str) -> Dict:
        """
        语音转文字
        
        Args:
            file_path (str): 语音文件路径
            user (str): 用户标识
            
        Returns:
            Dict: 转换结果
        """
        url = f"{self.base_url}/audio-to-text"
        headers = {
            "Authorization": f"Bearer {self.api_key}"
        }
        
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        # 获取MIME类型
        mime_type, _ = mimetypes.guess_type(str(file_path))
        if not mime_type:
            mime_type = 'audio/mpeg'  # 默认为mp3
        
        logger.info(f"语音转文字: {file_path}, 用户: {user}")
        
        # 准备表单数据
        with open(file_path, 'rb') as f:
            files = {
                'file': (file_path.name, f, mime_type)
            }
            data = {
                'user': user
            }
            
            response = requests.post(url, headers=headers, files=files, data=data)
            return self._handle_response(response)
    
    def text_to_audio(self, text: str = None, user: str = "user", message_id: str = None) -> bytes:
        """
        文字转语音
        
        Args:
            text (str, optional): 文本内容
            user (str, optional): 用户标识
            message_id (str, optional): 消息ID，优先使用
            
        Returns:
            bytes: 音频数据
        """
        url = f"{self.base_url}/text-to-audio"
        headers = {
            "Authorization": f"Bearer {self.api_key}"
        }
        
        data = {
            'user': user
        }
        
        if message_id:
            data['message_id'] = message_id
        elif text:
            data['text'] = text
        else:
            raise ValueError("必须提供 text 或 message_id 参数")
        
        logger.info(f"文字转语音, 用户: {user}")
        
        response = requests.post(url, headers=headers, data=data)
        
        if response.status_code != 200:
            self._handle_response(response)  # 处理错误
        
        return response.content
    
    def get_app_info(self) -> Dict:
        """
        获取应用基本信息
        
        Returns:
            Dict: 应用信息
        """
        url = f"{self.base_url}/info"
        
        logger.info("获取应用基本信息")
        
        response = requests.get(url, headers=self.headers)
        return self._handle_response(response)
    
    def get_app_parameters(self) -> Dict:
        """
        获取应用参数
        
        Returns:
            Dict: 应用参数
        """
        url = f"{self.base_url}/parameters"
        
        logger.info("获取应用参数")
        
        response = requests.get(url, headers=self.headers)
        return self._handle_response(response)
    
    def get_app_meta(self) -> Dict:
        """
        获取应用元信息
        
        Returns:
            Dict: 应用元信息
        """
        url = f"{self.base_url}/meta"
        
        logger.info("获取应用元信息")
        
        response = requests.get(url, headers=self.headers)
        return self._handle_response(response)
    
    def create_file_input(
        self, 
        file_id: str, 
        file_type: str = "image",
        transfer_method: str = "local_file"
    ) -> Dict:
        """
        创建文件输入参数
        
        Args:
            file_id (str): 文件ID
            file_type (str, optional): 文件类型，默认为image
            transfer_method (str, optional): 传输方式，默认为local_file
            
        Returns:
            Dict: 文件输入参数
        """
        return {
            "type": file_type,
            "transfer_method": transfer_method,
            "upload_file_id": file_id
        }
    
    def create_url_input(
        self, 
        url: str, 
        file_type: str = "image",
        transfer_method: str = "remote_url"
    ) -> Dict:
        """
        创建URL输入参数
        
        Args:
            url (str): 文件URL
            file_type (str, optional): 文件类型，默认为image
            transfer_method (str, optional): 传输方式，默认为remote_url
            
        Returns:
            Dict: URL输入参数
        """
        return {
            "type": file_type,
            "transfer_method": transfer_method,
            "url": url
        }

# 导出类
__all__ = ['DifyClient', 'DifyChatClient', 'ResponseMode', 'FileType', 'TransferMethod', 
           'MessageRating', 'DifyApiError']

# 使用示例
if __name__ == "__main__":
    # 示例 1：阻塞模式运行工作流
    def example_blocking():
        api_key = "your_api_key_here"
        client = DifyClient(api_key, "https://api.dify.ai/v1")
        
        # 简单工作流
        result = client.run_workflow(
            inputs={"query": "你好，请介绍一下自己"},
            response_mode=ResponseMode.BLOCKING,
            user="test_user_123"
        )
        print("阻塞模式运行结果:", result)
        
    # 示例 2：流式模式运行工作流
    def example_streaming():
        api_key = "your_api_key_here"
        client = DifyClient(api_key, "https://api.dify.ai/v1")
        
        # 流式响应
        stream = client.run_workflow(
            inputs={"query": "给我讲个故事"},
            response_mode=ResponseMode.STREAMING,
            user="test_user_123"
        )
        
        # 打印每个事件
        for line in stream:
            if line.startswith('data: '):
                data = line[6:]  # 移除 'data: ' 前缀
                try:
                    event_data = json.loads(data)
                    print(f"事件: {event_data.get('event', 'unknown')}")
                    if event_data.get('event') == 'workflow_finished':
                        print("工作流执行完成:", event_data)
                except json.JSONDecodeError:
                    print(f"解析事件数据失败: {data}")
    
    # 示例 3：上传文件并在工作流中使用
    def example_file_upload():
        api_key = "your_api_key_here"
        client = DifyClient(api_key, "https://api.dify.ai/v1")
        
        # 上传文件
        file_result = client.upload_file(
            file_path="example.txt",
            user="test_user_123",
            file_type="TXT"
        )
        
        file_id = file_result.get("id")
        
        # 在工作流中使用文件
        result = client.run_workflow(
            inputs={
                "document": client.create_file_input(file_id)
            },
            response_mode=ResponseMode.BLOCKING,
            user="test_user_123"
        )
        
        print("文件处理结果:", result)
    
    # 示例 4：异步运行工作流
    async def example_async():
        api_key = "your_api_key_here"
        client = DifyClient(api_key, "https://api.dify.ai/v1")
        
        # 定义回调函数
        async def event_callback(event_data):
            print(f"收到事件: {event_data.get('event', 'unknown')}")
            
            if event_data.get('event') == 'workflow_finished':
                print("工作流执行完成:", event_data)
        
        # 异步运行工作流
        await client.run_workflow_async(
            inputs={"query": "异步测试消息"},
            response_mode=ResponseMode.STREAMING,
            user="async_user_123",
            callback=event_callback
        )
    
    # 示例 5：使用聊天客户端发送消息
    def example_chat():
        api_key = "your_api_key_here"
        client = DifyChatClient(api_key, "http://sandanapp.com/v1")
        
        # 发送聊天消息（阻塞模式）
        result = client.send_chat_message(
            query="你好，请介绍一下自己",
            response_mode=ResponseMode.BLOCKING,
            user="chat_user_123"
        )
        print("聊天响应:", result)
        
        # 发送聊天消息（流式模式）
        stream = client.send_chat_message(
            query="给我讲个故事",
            response_mode=ResponseMode.STREAMING,
            user="chat_user_123"
        )
        
        for event in stream:
            print(f"事件: {event.get('event', 'unknown')}")
            if event.get('event') == 'message_end':
                print("聊天结束:", event)
    
    # 示例 6：获取会话列表
    def example_get_conversations():
        api_key = "your_api_key_here"
        client = DifyChatClient(api_key, "http://sandanapp.com/v1")
        
        # 获取会话列表
        conversations = client.get_conversations(
            user="chat_user_123",
            limit=10
        )
        
        print("会话列表:", conversations)
        
        # 如果有会话，获取第一个会话的消息历史
        if conversations.get('data') and len(conversations['data']) > 0:
            conversation_id = conversations['data'][0]['id']
            
            messages = client.get_conversation_messages(
                conversation_id=conversation_id,
                user="chat_user_123",
                limit=5
            )
            
            print(f"会话 {conversation_id} 的消息:", messages)
    
    # 运行示例
    # example_blocking()
    # example_streaming()
    # example_file_upload()
    # asyncio.run(example_async())
    # example_chat()
    # example_get_conversations()

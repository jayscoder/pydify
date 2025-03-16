"""
Pydify - 通用工具和基础类

此模块提供了Dify API客户端的基础类和通用工具。
"""

import os
import json
import requests
import mimetypes
from urllib.parse import urljoin
from typing import Dict, Any, List, Optional, Union, Generator, BinaryIO, Tuple, Callable
from requests.exceptions import JSONDecodeError as RequestsJSONDecodeError


class DifyBaseClient:
    """Dify API 基础客户端类。

    提供与Dify API进行交互的基本功能，包括身份验证、HTTP请求和通用方法。
    各种特定应用类型的客户端都继承自此类，以重用共同的功能。
    """

    def __init__(self, api_key: str, base_url: str = None):
        """
        初始化Dify API客户端。

        Args:
            api_key (str): Dify API密钥
            base_url (str, optional): API基础URL。如果未提供，则使用https://api.dify.ai/v1
        """
        self.api_key = api_key
        self.base_url = base_url or "https://api.dify.ai/v1"
        
        # 如果base_url不以斜杠结尾，则添加斜杠
        if not self.base_url.endswith("/"):
            self.base_url += "/"

    def _get_headers(self) -> Dict[str, str]:
        """
        获取API请求头。

        Returns:
            Dict[str, str]: 包含认证信息的请求头
        """
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def _request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """
        发送HTTP请求到Dify API。

        Args:
            method (str): HTTP方法 (GET, POST, PUT, DELETE)
            endpoint (str): API端点
            **kwargs: 传递给requests的其他参数

        Returns:
            requests.Response: 请求响应对象

        Raises:
            DifyAPIError: 当HTTP请求失败时
        """
        url = urljoin(self.base_url, endpoint)
        headers = kwargs.pop("headers", {})
        headers.update(self._get_headers())
        
        # 设置重试机制
        max_retries = kwargs.pop("max_retries", 2)
        retry_delay = kwargs.pop("retry_delay", 1)
        timeout = kwargs.pop("timeout", 30)
        
        # 添加超时参数
        kwargs["timeout"] = timeout
        
        for attempt in range(max_retries + 1):
            try:
                response = requests.request(method, url, headers=headers, **kwargs)
                
                if not response.ok:
                    error_msg = f"API request failed: {response.status_code}"
                    error_data = {}
                    try:
                        error_data = response.json()
                        error_msg = f"{error_msg} - {error_data.get('error', {}).get('message', '')}"
                    except RequestsJSONDecodeError:
                        if response.text:
                            error_msg = f"{error_msg} - {response.text[:100]}"
                    
                    # 如果是可重试的错误码，并且还有重试次数，则重试
                    if response.status_code in [429, 500, 502, 503, 504] and attempt < max_retries:
                        print(f"请求失败，状态码: {response.status_code}，{attempt+1}秒后重试...")
                        import time
                        time.sleep(retry_delay)
                        continue
                    
                    # 否则抛出异常
                    raise DifyAPIError(error_msg, status_code=response.status_code, error_data=error_data)
                
                return response
                
            except (requests.RequestException, ConnectionError) as e:
                # 如果是网络错误且还有重试次数，则重试
                if attempt < max_retries:
                    print(f"网络错误: {str(e)}，{attempt+1}秒后重试...")
                    import time
                    time.sleep(retry_delay)
                    continue
                
                raise DifyAPIError(f"网络请求异常: {str(e)}")

    def get(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        """
        发送GET请求到Dify API。

        Args:
            endpoint (str): API端点
            **kwargs: 传递给requests的其他参数

        Returns:
            Dict[str, Any]: 响应的JSON数据
            
        Raises:
            DifyAPIError: 当API请求失败时
        """
        response = self._request("GET", endpoint, **kwargs)
        try:
            if not response.text.strip():
                # 如果响应为空，返回空字典
                return {}
            return response.json()
        except RequestsJSONDecodeError as e:
            # 捕获JSON解析错误，打印警告信息并返回空字典
            print(f"警告: 无法解析API响应为JSON ({endpoint})")
            print(f"响应内容: {response.text[:100]}")
            return {}

    def post(self, endpoint: str, data: Dict[str, Any] = None, json_data: Dict[str, Any] = None, **kwargs) -> Dict[str, Any]:
        """
        发送POST请求到Dify API。

        Args:
            endpoint (str): API端点
            data (Dict[str, Any], optional): 要发送的表单数据
            json_data (Dict[str, Any], optional): 要发送的JSON数据
            **kwargs: 传递给requests的其他参数

        Returns:
            Dict[str, Any]: 响应的JSON数据
            
        Raises:
            DifyAPIError: 当API请求失败时
        """
        response = self._request("POST", endpoint, data=data, json=json_data, **kwargs)
        try:
            if not response.text.strip():
                # 如果响应为空，返回空字典
                return {}
            return response.json()
        except RequestsJSONDecodeError as e:
            # 捕获JSON解析错误，打印警告信息并返回空字典
            print(f"警告: 无法解析API响应为JSON ({endpoint})")
            print(f"响应内容: {response.text[:100]}")
            return {}

    def post_stream(self, endpoint: str, json_data: Dict[str, Any], **kwargs) -> Generator[Dict[str, Any], None, None]:
        """
        发送流式POST请求到Dify API。

        Args:
            endpoint (str): API端点
            json_data (Dict[str, Any]): JSON数据
            **kwargs: 传递给requests的其他参数

        Yields:
            Dict[str, Any]: 每个响应块的JSON数据
            
        Raises:
            DifyAPIError: 当API请求失败时
        """
        url = urljoin(self.base_url, endpoint)
        headers = kwargs.pop("headers", {})
        headers.update(self._get_headers())
        
        # 设置重试机制
        max_retries = kwargs.pop("max_retries", 2)
        retry_delay = kwargs.pop("retry_delay", 1)
        timeout = kwargs.pop("timeout", 60)  # 流式请求需要更长的超时时间
        
        # 添加超时参数
        kwargs["timeout"] = timeout
        
        for attempt in range(max_retries + 1):
            try:
                with requests.post(url, json=json_data, headers=headers, stream=True, **kwargs) as response:
                    if not response.ok:
                        error_msg = f"API request failed: {response.status_code}"
                        error_data = {}
                        try:
                            error_data = response.json()
                            error_msg = f"{error_msg} - {error_data.get('error', {}).get('message', '')}"
                        except RequestsJSONDecodeError:
                            # 如果无法解析为JSON，提供一个简单的错误消息
                            error_msg = f"{error_msg} - 响应无法解析为JSON"
                            if response.text:
                                print(f"响应内容: {response.text[:100]}")
                        
                        # 如果是可重试的错误码，并且还有重试次数，则重试
                        if response.status_code in [429, 500, 502, 503, 504] and attempt < max_retries:
                            print(f"请求失败，状态码: {response.status_code}，{attempt+1}秒后重试...")
                            import time
                            time.sleep(retry_delay)
                            continue
                        
                        raise DifyAPIError(error_msg, status_code=response.status_code, error_data=error_data)
                    
                    # 处理SSE流式响应
                    for line in response.iter_lines():
                        if line:
                            line = line.decode('utf-8')
                            if line.startswith('data: '):
                                data = line[6:]  # 移除 'data: ' 前缀
                                try:
                                    yield json.loads(data)
                                except json.JSONDecodeError as e:
                                    # 打印警告信息并继续处理
                                    print(f"警告: 无法解析流式响应行为JSON: {data[:100]}")
                                    # 返回一个带有错误信息的字典，而不是抛出异常
                                    yield {"error": "JSON解析错误", "raw_data": data[:100]}
                    
                    # 如果成功完成了迭代，就跳出重试循环
                    break
                    
            except (requests.RequestException, ConnectionError) as e:
                # 如果是网络错误且还有重试次数，则重试
                if attempt < max_retries:
                    print(f"网络错误: {str(e)}，{attempt+1}秒后重试...")
                    import time
                    time.sleep(retry_delay)
                    continue
                
                # 如果已经重试了所有次数仍失败，抛出异常
                raise DifyAPIError(f"流式请求异常: {str(e)}")
    
    # 通用方法 - 这些方法在多个子类中重复出现，可以移到基类
    
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
            DifyAPIError: 当API请求失败时
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
            
        with open(file_path, 'rb') as file:
            return self.upload_file_obj(file, os.path.basename(file_path), user)
    
    def upload_file_obj(self, file_obj: BinaryIO, filename: str, user: str) -> Dict[str, Any]:
        """
        使用文件对象上传文件到Dify API。

        Args:
            file_obj (BinaryIO): 文件对象
            filename (str): 文件名
            user (str): 用户标识

        Returns:
            Dict[str, Any]: 上传文件的响应数据
            
        Raises:
            DifyAPIError: 当API请求失败时
        """
        files = {'file': (filename, file_obj)}
        data = {'user': user}
        
        headers = self._get_headers()
        # 移除Content-Type，让requests自动设置multipart/form-data
        headers.pop('Content-Type', None)
        
        response = self._request("POST", 'files/upload', headers=headers, files=files, data=data)
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
            message_id (str, optional): 消息ID，如果提供，系统会使用该消息的内容生成语音。默认为None
            text (str, optional): 要转换为语音的文本。如果未提供message_id，则必须提供此参数。默认为None

        Returns:
            Dict[str, Any]: 包含音频数据的响应
            
        Raises:
            ValueError: 当必要参数缺失时
            DifyAPIError: 当API请求失败时
        """
        if not message_id and not text:
            raise ValueError("Either message_id or text must be provided")
            
        payload = {"user": user}
        
        if message_id:
            payload["message_id"] = message_id
            
        if text:
            payload["text"] = text
            
        return self.post("text-to-audio", json_data=payload)
    
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
            ValueError: 当提供了无效的rating参数时
            DifyAPIError: 当API请求失败时
        """
        if rating and rating not in ["like", "dislike"]:
            raise ValueError("rating must be 'like', 'dislike' or None")
            
        payload = {"user": user}
        
        if rating is not None:
            payload["rating"] = rating
            
        if content:
            payload["content"] = content
            
        return self.post(f"messages/{message_id}/feedbacks", json_data=payload)
    
    def get_app_info(self) -> Dict[str, Any]:
        """
        获取应用基本信息。

        Returns:
            Dict[str, Any]: 应用信息，包含名称、描述和标签
            
        Raises:
            DifyAPIError: 当API请求失败时
        """
        return self.get("info")
        
    def get_parameters(self) -> Dict[str, Any]:
        """
        获取应用参数，包括功能开关、输入参数名称、类型及默认值等。

        Returns:
            Dict[str, Any]: 应用参数配置
            
        Raises:
            DifyAPIError: 当API请求失败时
        """
        return self.get("parameters")
    
    def get_conversations(
        self,
        user: str,
        last_id: str = None,
        limit: int = 20,
        sort_by: str = "-updated_at",
    ) -> Dict[str, Any]:
        """
        获取用户的会话列表。

        Args:
            user (str): 用户标识
            last_id (str, optional): 上一页最后一条会话的ID，用于分页。默认为None
            limit (int, optional): 每页数量，最大100。默认为20
            sort_by (str, optional): 排序方式，支持created_at和updated_at，默认为-updated_at

        Returns:
            Dict[str, Any]: 会话列表数据，包含会话基本信息
            
        Raises:
            DifyAPIError: 当API请求失败时
        """
        params = {
            "user": user,
            "limit": min(limit, 100),  # 限制最大数量为100
            "sort_by": sort_by,
        }
        
        if last_id:
            params["last_id"] = last_id
            
        return self.get("conversations", params=params)
        
    def get_messages(
        self,
        conversation_id: str,
        user: str,
        first_id: str = None,
        limit: int = 20,
    ) -> Dict[str, Any]:
        """
        获取会话历史消息列表。

        Args:
            conversation_id (str): 会话ID
            user (str): 用户标识
            first_id (str, optional): 上一页第一条消息的ID，用于分页。默认为None
            limit (int, optional): 每页数量，最大100。默认为20

        Returns:
            Dict[str, Any]: 消息列表数据，包含用户提问和AI回复
            
        Raises:
            DifyAPIError: 当API请求失败时
        """
        params = {
            "user": user,
            "conversation_id": conversation_id,
            "limit": min(limit, 100),  # 限制最大数量为100
        }
        
        if first_id:
            params["first_id"] = first_id
            
        return self.get("messages", params=params)
    
    def delete_conversation(self, conversation_id: str, user: str) -> Dict[str, Any]:
        """
        删除会话。

        Args:
            conversation_id (str): 会话ID
            user (str): 用户标识

        Returns:
            Dict[str, Any]: 删除结果
            
        Raises:
            DifyAPIError: 当API请求失败时
        """
        return self.post(f"conversations/{conversation_id}/delete", json_data={"user": user})
    
    def rename_conversation(
        self,
        conversation_id: str,
        user: str,
        name: str = None,
        auto_generate: bool = False,
    ) -> Dict[str, Any]:
        """
        重命名会话。

        Args:
            conversation_id (str): 会话ID
            user (str): 用户标识
            name (str, optional): 自定义会话名称。默认为None
            auto_generate (bool, optional): 是否自动生成名称，如果为True，name参数将被忽略。默认为False

        Returns:
            Dict[str, Any]: 更新后的会话信息
            
        Raises:
            ValueError: 当name和auto_generate都未提供或同时提供时
            DifyAPIError: 当API请求失败时
        """
        if not name and not auto_generate:
            raise ValueError("Either name or auto_generate must be provided")
        
        if name and auto_generate:
            raise ValueError("Cannot provide both name and auto_generate=True")
            
        payload = {"user": user}
        
        if auto_generate:
            payload["auto_generate"] = True
        else:
            payload["name"] = name
            
        return self.post(f"conversations/{conversation_id}/name", json_data=payload)
    
    def get_suggested_questions(self, message_id: str, user: str) -> Dict[str, Any]:
        """
        获取推荐问题列表。

        Args:
            message_id (str): 消息ID
            user (str): 用户标识

        Returns:
            Dict[str, Any]: 推荐问题列表
            
        Raises:
            DifyAPIError: 当API请求失败时
        """
        params = {
            "user": user,
            "message_id": message_id,
        }
        
        return self.get("suggested-questions", params=params)
    
    def process_streaming_response(
        self,
        stream_generator: Generator[Dict[str, Any], None, None],
        **handlers
    ) -> Dict[str, Any]:
        """
        处理流式响应，调用相应事件处理器。子类应重写此方法以支持特定应用类型的事件。
        
        Args:
            stream_generator: 流式响应生成器
            **handlers: 各种事件的处理函数
            
        Returns:
            Dict[str, Any]: 处理结果，包含消息ID等信息
        """
        raise NotImplementedError("Subclasses must implement process_streaming_response method")


class DifyAPIError(Exception):
    """Dify API错误异常"""
    
    def __init__(self, message: str, status_code: int = None, error_data: Dict = None):
        self.message = message
        self.status_code = status_code
        self.error_data = error_data or {}
        super().__init__(self.message)
    
    def __str__(self) -> str:
        if self.status_code:
            return f"[{self.status_code}] {self.message}"
        return self.message

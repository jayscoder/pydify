"""
Pydify - Dify API的Python客户端库

这个库提供了与Dify API交互的简单方式，支持所有主要功能，
包括对话、文本生成、工作流、文件上传等。
"""

import os
import json
import requests
import time
from typing import Dict, List, Union, Optional, BinaryIO, Iterator, Any, Tuple
import sseclient
import mimetypes
import warnings
from dotenv import load_dotenv

load_dotenv() # 加载环境变量.env

class DifyException(Exception):
    """Dify API异常基类"""
    def __init__(self, message, status_code=None, response=None):
        self.message = message
        self.status_code = status_code
        self.response = response
        super().__init__(self.message)


class DifyRequestError(DifyException):
    """请求错误，通常是由客户端引起的"""
    pass


class DifyServerError(DifyException):
    """服务器错误，通常是由Dify服务器引起的"""
    pass


class DifyAuthError(DifyException):
    """认证错误，通常是由无效的API密钥引起的"""
    pass


class DifyTimeoutError(DifyException):
    """请求超时错误"""
    pass


class DifyRateLimitError(DifyException):
    """请求频率限制错误"""
    pass


class DifyResponse:
    """Dify API响应包装器"""
    
    def __init__(self, response):
        self.response = response
        self._data = None
        self._conversation_id = None
        self._answer = None
        self._message_id = None
        self._metadata = None
        self._workflow_run_id = None
        self._task_id = None
        
    @property
    def status_code(self) -> int:
        """获取HTTP状态码"""
        return self.response.status_code
    
    @property
    def headers(self) -> Dict:
        """获取响应头"""
        return dict(self.response.headers)
    
    @property
    def data(self) -> Dict:
        """获取JSON响应数据"""
        if self._data is None:
            try:
                self._data = self.response.json()
            except ValueError:
                self._data = {}
        return self._data
    
    @property
    def text(self) -> str:
        """获取原始响应文本"""
        return self.response.text
    
    @property
    def content(self) -> bytes:
        """获取原始响应内容（字节）"""
        return self.response.content
    
    def __repr__(self) -> str:
        return f"<DifyResponse status_code={self.status_code}>"


class DifyStreamResponse:
    """Dify API流式响应包装器"""
    
    def __init__(self, response, message_type="message"):
        self.response = response
        self.message_type = message_type
        self._iterator = self._iter_content()
        
    def _iter_content(self):
        """从响应中迭代解析SSE事件"""
        buffer = ""
        
        # 确保response有iter_lines属性
        if not hasattr(self.response, 'iter_lines'):
            raise DifyException("响应对象不支持流式内容")
            
        for line in self.response.iter_lines(decode_unicode=True):
            if line:
                if line.startswith('data:'):
                    data = line[5:].strip()
                    if data == "[DONE]":
                        break
                        
                    try:
                        event_data = json.loads(data)
                        yield event_data
                    except json.JSONDecodeError:
                        # 忽略无法解析的数据
                        pass
        
    def __iter__(self):
        return self
        
    def __next__(self):
        try:
            return next(self._iterator)
        except StopIteration:
            raise StopIteration
    
    def iter_content(self) -> Iterator[Dict]:
        """迭代流式内容"""
        for event in self:
            yield event
            
    def stream_content(self) -> Iterator[str]:
        """迭代流式文本内容
        
        与iter_content不同，这个方法只返回文本内容部分
        """
        for event in self:
            # 处理普通聊天/完成消息格式
            if event.get("type") == self.message_type:
                content = event.get("answer", "")
                if content:
                    yield content
            # 处理简单的文本字段
            elif "text" in event:
                yield event["text"]
            elif "content" in event:
                yield event["content"]
            # 处理工作流事件数据格式
            elif event.get("event") == "node_finished" and "data" in event:
                data = event.get("data", {})
                # 检查节点类型，主要提取LLM节点输出的文本
                if data.get("node_type") == "llm" and "outputs" in data:
                    outputs = data.get("outputs", {})
                    if "text" in outputs:
                        yield outputs["text"]
            elif event.get('event') == 'message':
                yield event['answer']
            elif 'answer' in event:
                yield event['answer']
    
    def collect_response(self) -> str:
        """收集完整响应文本"""
        result = ""
        for chunk in self.stream_content():
            result += chunk
        return result
    

class BaseResource:
    """API资源基类"""
    
    def __init__(self, client):
        self.client = client


class ChatResource(BaseResource):
    """聊天相关API资源"""
    
    def create_message(
        self, 
        query: str,
        user: str,
        inputs: Dict = None,
        response_mode: str = "streaming",
        conversation_id: str = None,
        files: List[Dict] = None,
        auto_generate_name: bool = True
    ) -> Union[DifyResponse, DifyStreamResponse]:
        """
        发送对话消息
        
        Args:
            query: 用户输入内容
            user: 用户唯一标识
            inputs: 自定义变量，默认为空字典
            response_mode: 响应模式，"streaming"（流式）或"blocking"（阻塞式）
            conversation_id: 会话ID（可选，用于延续对话）
            files: 文件列表
            auto_generate_name: 是否自动生成会话标题
            
        Returns:
            流式或非流式响应对象
        """
        inputs = inputs or {}
        files = files or []
        
        data = {
            "query": query,
            "user": user,
            "inputs": inputs,
            "response_mode": response_mode,
            "auto_generate_name": auto_generate_name
        }
        
        if conversation_id:
            data["conversation_id"] = conversation_id
            
        if files:
            data["files"] = files
            
        return self.client.request(
            method="POST",
            path="/chat-messages",
            json=data,
            stream=(response_mode == "streaming")
        )
    
    def get_suggested_questions(self, message_id: str, user: str) -> DifyResponse:
        """
        获取建议问题
        
        Args:
            message_id: 消息ID
            user: 用户唯一标识
            
        Returns:
            API响应对象
        """
        return self.client.request(
            method="GET",
            path=f"/messages/{message_id}/suggested",
            params={"user": user}
        )
    
    def create_feedback(
        self,
        message_id: str,
        rating: Optional[str] = None,
        user: str = None,
        content: str = None
    ) -> DifyResponse:
        """
        提交消息反馈
        
        Args:
            message_id: 消息ID
            rating: 反馈类型："like"、"dislike"或None
            user: 用户唯一标识
            content: 反馈内容
            
        Returns:
            API响应对象
        """
        data = {}
        if rating:
            data["rating"] = rating
        if user:
            data["user"] = user
        if content:
            data["content"] = content
            
        return self.client.request(
            method="POST",
            path=f"/messages/{message_id}/feedbacks",
            json=data
        )
    
    def list_messages(
        self,
        conversation_id: str,
        user: str = None,
        first_id: str = None,
        limit: int = 20
    ) -> DifyResponse:
        """
        获取对话历史消息
        
        Args:
            conversation_id: 会话ID
            user: 用户唯一标识
            first_id: 起始消息ID
            limit: 返回消息数量限制
            
        Returns:
            API响应对象
        """
        params = {"conversation_id": conversation_id}
        if user:
            params["user"] = user
        if first_id:
            params["first_id"] = first_id
        if limit != 20:
            params["limit"] = limit
            
        return self.client.request(
            method="GET",
            path="/messages",
            params=params
        )


class CompletionResource(BaseResource):
    """文本生成相关API资源"""
    
    def create_completion(
        self,
        inputs: Dict,
        user: str,
        response_mode: str = "blocking",
        files: List[Dict] = None
    ) -> Union[DifyResponse, DifyStreamResponse]:
        """
        执行文本生成任务
        
        Args:
            inputs: 包含query和其他变量的字典
            user: 用户唯一标识
            response_mode: 响应模式，"streaming"（流式）或"blocking"（阻塞式）
            files: 文件列表
            
        Returns:
            流式或非流式响应对象
        """
        data = {
            "inputs": inputs,
            "user": user,
            "response_mode": response_mode
        }
        
        if files:
            data["files"] = files
            
        return self.client.request(
            method="POST",
            path="/completion-messages",
            json=data,
            stream=(response_mode == "streaming")
        )


class WorkflowResource(BaseResource):
    """工作流相关API资源"""
    
    def run_workflow(
        self,
        inputs: Dict,
        user: str,
        response_mode: str = "streaming",
        files: List[Dict] = None
    ) -> Union[DifyResponse, DifyStreamResponse]:
        """
        执行工作流
        
        Args:
            inputs: 自定义变量
            user: 用户唯一标识
            response_mode: 响应模式，"streaming"（流式）或"blocking"（阻塞式）
            files: 文件列表
            
        Returns:
            流式或非流式响应对象
        """
        data = {
            "inputs": inputs,
            "user": user,
            "response_mode": response_mode
        }
        
        if files:
            data["files"] = files
            
        return self.client.request(
            method="POST",
            path="/workflows/run",
            json=data,
            stream=(response_mode == "streaming")
        )


class FileResource(BaseResource):
    """文件相关API资源"""
    
    def upload(
        self,
        file: Union[str, BinaryIO],
        user: str,
        filename: str = None
    ) -> DifyResponse:
        """
        上传文件
        
        Args:
            file: 文件路径或文件对象
            user: 用户唯一标识
            filename: 文件名（当file是文件对象时需提供）
            
        Returns:
            API响应对象
        """
        if isinstance(file, str):
            file_obj = open(file, "rb")
            if not filename:
                filename = os.path.basename(file)
        else:
            file_obj = file
            if not filename:
                raise ValueError("当提供文件对象时，必须指定filename参数")
        
        try:
            file_data = {"file": (filename, file_obj)}
            return self.client.request(
                method="POST",
                path="/files/upload",
                data={"user": user},
                files=file_data,
                stream=False
            )
        finally:
            if isinstance(file, str):
                file_obj.close()


class ConversationResource(BaseResource):
    """会话相关API资源"""
    
    def list_conversations(
        self,
        user: str,
        last_id: str = None,
        limit: int = 20,
        sort_by: str = "-updated_at"
    ) -> DifyResponse:
        """
        获取会话列表
        
        Args:
            user: 用户唯一标识
            last_id: 分页ID
            limit: 返回条数限制
            sort_by: 排序字段
            
        Returns:
            API响应对象
        """
        params = {"user": user}
        if last_id:
            params["last_id"] = last_id
        if limit != 20:
            params["limit"] = limit
        if sort_by != "-updated_at":
            params["sort_by"] = sort_by
            
        return self.client.request(
            method="GET",
            path="/conversations",
            params=params
        )
    
    def delete_conversation(self, conversation_id: str, user: str) -> DifyResponse:
        """
        删除会话
        
        Args:
            conversation_id: 会话ID
            user: 用户唯一标识
            
        Returns:
            API响应对象
        """
        return self.client.request(
            method="DELETE",
            path=f"/conversations/{conversation_id}",
            params={"user": user}
        )
    
    def rename_conversation(
        self,
        conversation_id: str,
        name: str = None,
        auto_generate: bool = None,
        user: str = None
    ) -> DifyResponse:
        """
        重命名会话
        
        Args:
            conversation_id: 会话ID
            name: 新名称
            auto_generate: 是否自动生成名称
            user: 用户唯一标识
            
        Returns:
            API响应对象
        """
        data = {}
        if name:
            data["name"] = name
        if auto_generate is not None:
            data["auto_generate"] = auto_generate
        if user:
            data["user"] = user
            
        return self.client.request(
            method="POST",
            path=f"/conversations/{conversation_id}/name",
            json=data
        )


class MultiModalResource(BaseResource):
    """多模态相关API资源"""
    
    def audio_to_text(self, file: Union[str, BinaryIO], user: str) -> DifyResponse:
        """
        语音转文字
        
        Args:
            file: 语音文件路径或文件对象
            user: 用户唯一标识
            
        Returns:
            API响应对象
        """
        if isinstance(file, str):
            with open(file, "rb") as f:
                return self._upload_audio(f, user)
        else:
            return self._upload_audio(file, user)
    
    def _upload_audio(self, file_obj: BinaryIO, user: str) -> DifyResponse:
        """上传音频文件内部方法"""
        file_data = {"file": file_obj}
        return self.client.request(
            method="POST",
            path="/audio-to-text",
            data={"user": user},
            files=file_data
        )
    
    def text_to_audio(
        self,
        text: str = None,
        message_id: str = None,
        user: str = None
    ) -> bytes:
        """
        文字转语音
        
        Args:
            text: 待转换文本
            message_id: 消息ID（优先使用）
            user: 用户唯一标识
            
        Returns:
            音频数据（字节）
        """
        data = {}
        if message_id:
            data["message_id"] = message_id
        elif text:
            data["text"] = text
        else:
            raise ValueError("必须提供text或message_id参数之一")
            
        if user:
            data["user"] = user
            
        response = self.client.request(
            method="POST",
            path="/text-to-audio",
            json=data,
            raw=True
        )
        
        return response.content


class TaskResource(BaseResource):
    """任务相关API资源"""
    
    def stop_task(self, resource_type: str, task_id: str, user: str) -> DifyResponse:
        """
        停止流式任务
        
        Args:
            resource_type: 资源类型
            task_id: 任务ID
            user: 用户唯一标识
            
        Returns:
            API响应对象
        """
        return self.client.request(
            method="POST",
            path=f"/{resource_type}/{task_id}/stop",
            json={"user": user}
        )


class InfoResource(BaseResource):
    """信息相关API资源"""
    
    def get_app_info(self) -> DifyResponse:
        """
        获取应用信息
        
        Returns:
            API响应对象
        """
        return self.client.request(
            method="GET",
            path="/info"
        )
    
    def get_parameters(self) -> DifyResponse:
        """
        获取应用参数
        
        Returns:
            API响应对象
        """
        return self.client.request(
            method="GET",
            path="/parameters"
        )
    
    def get_meta(self) -> DifyResponse:
        """
        获取元数据（如工具图标）
        
        Returns:
            API响应对象
        """
        return self.client.request(
            method="GET",
            path="/meta"
        )


class DifyClient:
    """Dify API客户端"""
    
    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.dify.ai/v1",
        timeout: int = 60,
        max_retries: int = 3,
        retry_delay: int = 1
    ):
        """
        初始化Dify客户端
        
        Args:
            api_key: Dify API密钥
            base_url: API基础URL
            timeout: 请求超时时间（秒）
            max_retries: 最大重试次数
            retry_delay: 重试延迟时间（秒）
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.session = requests.Session()
        
        # 初始化API资源
        self.chat = ChatResource(self)
        self.completion = CompletionResource(self)
        self.workflow = WorkflowResource(self)
        self.file = FileResource(self)
        self.conversation = ConversationResource(self)
        self.multimodal = MultiModalResource(self)
        self.task = TaskResource(self)
        self.info = InfoResource(self)
    
    def request(
        self,
        method: str,
        path: str,
        params: Dict = None,
        data: Dict = None,
        json: Dict = None,
        files: Dict = None,
        headers: Dict = None,
        stream: bool = False,
        raw: bool = False
    ) -> Union[DifyResponse, DifyStreamResponse, requests.Response]:
        """
        发送API请求
        
        Args:
            method: HTTP方法（GET、POST等）
            path: API路径
            params: URL参数
            data: 表单数据
            json: JSON数据
            files: 文件数据
            headers: 请求头
            stream: 是否使用流式响应
            raw: 是否返回原始响应对象
            
        Returns:
            API响应对象
        """
        url = f"{self.base_url}{path}"
        headers = headers or {}
        headers["Authorization"] = f"Bearer {self.api_key}"
        
        if not files and "Content-Type" not in headers and not data:
            headers["Content-Type"] = "application/json"
            
        for attempt in range(self.max_retries):
            try:
                response = self.session.request(
                    method=method,
                    url=url,
                    params=params,
                    data=data,
                    json=json,
                    files=files,
                    headers=headers,
                    timeout=self.timeout,
                    stream=stream
                )
                
                if response.status_code >= 500:
                    raise DifyServerError(
                        f"服务器错误: {response.status_code}",
                        status_code=response.status_code,
                        response=response
                    )
                elif response.status_code == 401:
                    raise DifyAuthError(
                        "认证错误: API密钥无效",
                        status_code=response.status_code,
                        response=response
                    )
                elif response.status_code == 429:
                    raise DifyRateLimitError(
                        "请求频率限制",
                        status_code=response.status_code,
                        response=response
                    )
                elif 400 <= response.status_code < 500:
                    error_msg = "请求错误"
                    try:
                        error_data = response.json()
                        if "error" in error_data:
                            error_msg = f"请求错误: {error_data['error']}"
                    except (ValueError, KeyError):
                        pass
                    
                    raise DifyRequestError(
                        error_msg,
                        status_code=response.status_code,
                        response=response
                    )
                
                # 处理成功响应
                if raw:
                    return response
                elif stream:
                    try:
                        return DifyStreamResponse(response)
                    except Exception as e:
                        raise DifyException(f"处理流式响应失败: {str(e)}")
                else:
                    return DifyResponse(response)
                    
            except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
                if attempt == self.max_retries - 1:
                    raise DifyTimeoutError(f"请求超时: {str(e)}")
                time.sleep(self.retry_delay)
            
            except (DifyServerError, DifyRateLimitError) as e:
                if attempt == self.max_retries - 1:
                    raise
                time.sleep(self.retry_delay)
                
            except Exception as e:
                raise DifyException(f"请求异常: {str(e)}")
    
    def close(self):
        """关闭客户端会话"""
        self.session.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


# 便捷创建客户端的函数
def create_client(
    api_key: str = None,
    base_url: str = None,
    **kwargs
) -> DifyClient:
    """
    创建Dify客户端实例
    
    Args:
        api_key: Dify API密钥（如果未提供，将尝试从环境变量DIFY_API_KEY获取）
        base_url: API基础URL（如果未提供，将尝试从环境变量DIFY_API_BASE_URL获取）
        **kwargs: 传递给DifyClient构造函数的其他参数
        
    Returns:
        DifyClient实例
    """
    api_key = api_key or os.environ.get("DIFY_API_KEY")
    if not api_key:
        raise ValueError("必须提供API密钥或设置DIFY_API_KEY环境变量")
        
    base_url = base_url or os.environ.get("DIFY_API_BASE_URL", "https://api.dify.ai/v1")
    
    return DifyClient(api_key=api_key, base_url=base_url, **kwargs)

"""
Pydify - 通用工具和基础类

此模块提供了Dify API客户端的基础类和通用工具。
"""

import datetime
import json
import mimetypes
import os
import re
import time
from typing import (
    Any,
    BinaryIO,
    Callable,
    Dict,
    Generator,
    List,
    Optional,
    Tuple,
    Union,
)
from urllib.parse import urljoin

import requests
import sseclient
from requests.exceptions import JSONDecodeError as RequestsJSONDecodeError


class DifyType:
    """Dify应用类型枚举

    Dify平台支持多种类型的应用，每种类型有不同的API端点和功能。
    此类定义了所有支持的应用类型常量，用于客户端类型标识。
    """

    Workflow = "workflow"
    Chatbot = "chatbot"
    Chatflow = "chatflow"
    Agent = "agent"
    TextGeneration = "text_generation"


class DifyBaseClient:
    """Dify API 基础客户端类。

    提供与Dify API进行交互的基本功能，包括身份验证、HTTP请求和通用方法。
    各种特定应用类型的客户端都继承自此类，以重用共同的功能。

    主要功能:
    - HTTP请求处理 (GET/POST/流式请求)
    - 错误处理和重试机制
    - 文件上传
    - 用户会话管理
    - 消息反馈功能

    子类应设置适当的type属性，并根据需要实现特定的API方法。
    """

    type = None

    def __init__(self, api_key: str, base_url: str = None):
        """
        初始化Dify API客户端。

        Args:
            api_key (str): Dify API密钥，可以从Dify平台的应用设置中获取。
                          API密钥决定了权限范围和可访问的功能。
            base_url (str, optional): API基础URL。如果未提供，则使用默认的Dify API地址。
                                    可以设置为自托管Dify实例的URL。
                                    也可以通过DIFY_BASE_URL环境变量设置。

        注意:
            - API密钥应当保密，不要在客户端代码中硬编码
            - 对于自托管实例，确保base_url格式正确，通常以/v1结尾
        """
        self.api_key = api_key
        self.base_url = (
            base_url or os.environ.get("DIFY_BASE_URL") or "https://api.dify.ai/v1"
        )

        # 如果base_url不以斜杠结尾，则添加斜杠
        if not self.base_url.endswith("/"):
            self.base_url += "/"

    def _get_headers(self) -> Dict[str, str]:
        """
        获取API请求头。

        Returns:
            Dict[str, str]: 包含认证信息的请求头，用于API认证
        """
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def _request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """
        发送HTTP请求到Dify API并处理可能的错误。

        此方法是所有API请求的核心，实现了错误处理、重试逻辑和超时控制。
        所有其他HTTP方法（get, post等）都基于此方法。

        Args:
            method (str): HTTP方法 (GET, POST, PUT, DELETE)
            endpoint (str): API端点路径，相对于base_url
            **kwargs: 传递给requests的其他参数，常用的包括:
                - params: URL查询参数
                - data: 表单数据
                - json: JSON数据
                - timeout: 请求超时时间(秒)
                - max_retries: 最大重试次数
                - retry_delay: 重试间隔(秒)

        Returns:
            requests.Response: 请求响应对象

        Raises:
            DifyAPIError: 当HTTP请求失败时，包含详细的错误信息和可能的解决方案
                - status_code: HTTP状态码
                - error_data: 服务器返回的错误数据
                - 常见错误包括认证错误(401)、参数错误(400)、资源不存在(404)等
            连接错误:
                - 网络连接问题
                - SSL证书错误
                - 超时
                - 服务器不可达
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
                    error_data = {}
                    error_details = ""

                    # 尝试解析错误数据
                    try:
                        error_data = response.json()
                        if isinstance(error_data, dict):
                            if "error" in error_data and isinstance(
                                error_data["error"], dict
                            ):
                                error_details = error_data["error"].get("message", "")
                            else:
                                error_details = error_data.get("message", "")
                    except RequestsJSONDecodeError:
                        if response.text:
                            error_details = response.text[:500]

                    # 构建格式化的错误消息
                    error_msg = f"""
PYDIFY:API请求失败: 
└─ 请求信息:
   ├─ 方法: {method}
   ├─ URL: {url}
   └─ 端点: {endpoint}
└─ 响应信息:
   ├─ 状态码: {response.status_code} ({response.reason})
   └─ 错误详情: {error_details}
"""

                    # 如果是可重试的错误码，并且还有重试次数，则重试
                    if (
                        response.status_code in [429, 500, 502, 503, 504]
                        and attempt < max_retries
                    ):
                        print(
                            f"请求失败，状态码: {response.status_code}，{attempt+1}秒后重试..."
                        )
                        time.sleep(retry_delay)
                        continue

                    # 否则抛出异常
                    raise DifyAPIError(
                        error_msg,
                        status_code=response.status_code,
                        error_data=error_data,
                    )

                return response

            except (requests.RequestException, ConnectionError) as e:
                # 如果是网络错误且还有重试次数，则重试
                if attempt < max_retries:
                    # 提供更详细的错误信息
                    error_type = type(e).__name__

                    # 检测具体的连接问题类型
                    if isinstance(e, requests.exceptions.SSLError):
                        error_msg = f"SSL连接错误: {str(e)}"
                    elif isinstance(e, requests.exceptions.ConnectTimeout):
                        error_msg = f"连接超时: {str(e)}"
                    elif isinstance(e, requests.exceptions.ReadTimeout):
                        error_msg = f"读取超时: {str(e)}"
                    elif isinstance(e, requests.exceptions.ConnectionError):
                        error_msg = f"网络连接错误: {str(e)}"
                    else:
                        error_msg = f"网络错误({error_type}): {str(e)}"

                    print(f"{error_msg}，{attempt+1}秒后重试...")
                    time.sleep(retry_delay)
                    continue

                # 提供更友好的错误信息
                error_type = type(e).__name__

                # 格式化的网络错误消息
                error_msg = f"""
PYDIFY:网络请求失败: 
└─ 请求信息:
   ├─ 方法: {method}
   ├─ URL: {url}
   └─ 端点: {endpoint}
└─ 错误信息:
   ├─ 类型: {error_type}
   └─ 详情: {str(e)}
"""

                # 提供连接问题的建议
                suggestions = """
请检查:
1. 网络连接是否正常
2. API地址是否正确: {0}
3. 服务器是否可用
4. SSL证书是否有效
5. 超时设置是否合理: {1}秒
""".format(
                    self.base_url, timeout
                )

                raise DifyAPIError(f"{error_msg}{suggestions}")

    def get(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        """
        发送GET请求到Dify API。

        Args:
            endpoint (str): API端点，相对于base_url的路径
            **kwargs: 传递给_request方法的其他参数，常用的包括:
                - params: URL查询参数
                - timeout: 请求超时时间(秒)
                - max_retries: 最大重试次数

        Returns:
            Dict[str, Any]: 响应的JSON数据，解析为Python字典

        Raises:
            DifyAPIError: 当API请求失败时，包含详细的错误信息

        示例:
            ```python
            # 获取应用信息
            app_info = client.get("app-info")

            # 带参数的请求
            messages = client.get("messages", params={"conversation_id": "conv_123", "limit": 10})
            ```
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

    def post(
        self,
        endpoint: str,
        data: Dict[str, Any] = None,
        json_data: Dict[str, Any] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        发送POST请求到Dify API。

        Args:
            endpoint (str): API端点，相对于base_url的路径
            data (Dict[str, Any], optional): 要发送的表单数据
            json_data (Dict[str, Any], optional): 要发送的JSON数据
            **kwargs: 传递给_request方法的其他参数，常用的包括:
                - timeout: 请求超时时间(秒)
                - max_retries: 最大重试次数

        Returns:
            Dict[str, Any]: 响应的JSON数据，解析为Python字典

        Raises:
            DifyAPIError: 当API请求失败时，包含详细的错误信息

        示例:
            ```python
            # 发送消息
            response = client.post("messages", json_data={
                "query": "你好",
                "user": "user_123",
                "response_mode": "blocking"
            })
            ```
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

    def post_stream(
        self, endpoint: str, json_data: Dict[str, Any], **kwargs
    ) -> Generator[Dict[str, Any], None, None]:
        """
        发送流式POST请求到Dify API，用于接收SSE实时响应。

        此方法主要用于处理长时间运行的请求，如流式生成文本、Agent思考过程、
        工作流执行等需要实时获取进度和结果的场景。

        Args:
            endpoint (str): API端点，相对于base_url的路径
            json_data (Dict[str, Any]): 要发送的JSON数据
            **kwargs: 传递给requests的其他参数，常用的包括:
                - timeout: 请求超时时间(秒)，流式请求通常需要更长的超时时间
                - max_retries: 最大重试次数

        Yields:
            Dict[str, Any]: 每个SSE事件块解析后的JSON数据

        Raises:
            DifyAPIError: 当API请求失败时
            网络错误: 连接问题、超时等

        示例:
            ```python
            # 流式生成文本
            stream = client.post_stream("messages", json_data={
                "query": "写一篇文章",
                "user": "user_123",
                "response_mode": "streaming"
            })

            # 处理每个事件块
            for chunk in stream:
                if "answer" in chunk:
                    print(chunk["answer"], end="")
            ```
        """
        url = urljoin(self.base_url, endpoint)
        headers = kwargs.pop("headers", {})
        headers.update(self._get_headers())

        # 设置重试机制
        max_retries = kwargs.pop("max_retries", 2)
        retry_delay = kwargs.pop("retry_delay", 1)
        timeout = kwargs.get("timeout", 3600)  # 流式请求需要更长的超时时间

        # 添加超时参数
        kwargs["timeout"] = timeout

        with requests.post(
            url, json=json_data, headers=headers, stream=True, **kwargs
        ) as response:
            try:
                response.raise_for_status()
            except Exception as e:
                try:
                    error_data = response.content.decode("utf-8").strip("\n")
                    try:
                        error_json = json.loads(error_data)

                        # 构建格式化的错误消息
                        error_msg = f"""
PYDIFY:流式请求失败: 
└─ 请求信息:
   ├─ 方法: POST
   ├─ URL: {url}
   └─ 端点: {endpoint}
└─ 请求参数:
   └─ {json.dumps(json_data, ensure_ascii=False, indent=2)[:500]}...
└─ 响应信息:
   ├─ 状态码: {response.status_code} ({response.reason})
   ├─ 错误类型: {error_json.get('code', '未知')}
   └─ 错误详情: {error_json.get('message', '未知')}
"""
                        raise DifyAPIError(error_msg)
                    except json.JSONDecodeError:
                        # 无法解析JSON时直接使用原始错误内容
                        error_msg = f"""
PYDIFY:流式请求失败: 
└─ 请求信息:
   ├─ 方法: POST
   ├─ URL: {url}
   └─ 端点: {endpoint}
└─ 响应信息:
   ├─ 状态码: {response.status_code} ({response.reason})
   └─ 错误详情: {error_data[:500]}
└─ 原始错误:
   └─ {str(e)}
"""
                        raise DifyAPIError(error_msg)
                except Exception as decode_error:
                    # 构建格式化的错误消息（无法获取响应内容）
                    error_msg = f"""
PYDIFY:流式请求失败: 
└─ 请求信息:
   ├─ 方法: POST
   ├─ URL: {url}
   └─ 端点: {endpoint}
└─ 响应信息:
   ├─ 状态码: {response.status_code} ({response.reason})
└─ 原始错误:
   ├─ 类型: {type(e).__name__}
   └─ 详情: {str(e)}
└─ 解析错误:
   └─ {str(decode_error)}
"""
                    raise DifyAPIError(error_msg)

            try:
                client = sseclient.SSEClient(response)
            except Exception as e:
                # 构建格式化的SSE初始化错误消息
                error_msg = f"""
PYDIFY:SSE客户端初始化失败: 
└─ 请求信息:
   ├─ 方法: POST
   ├─ URL: {url}
   └─ 端点: {endpoint}
└─ 错误信息:
   ├─ 类型: {type(e).__name__}
   └─ 详情: {str(e)}
"""
                raise DifyAPIError(error_msg)

            # 处理SSE流式响应
            for event in client.events():
                try:
                    yield json.loads(event.data)
                except json.JSONDecodeError as e:
                    # 构建格式化的JSON解析错误消息
                    error_msg = f"""
PYDIFY:处理SSE流式响应时JSON解析错误: 
└─ 请求信息:
   ├─ 方法: POST
   ├─ URL: {url}
   └─ 端点: {endpoint}
└─ 错误信息:
   ├─ 类型: {type(e).__name__}
   └─ 详情: {str(e)}
└─ 原始数据:
   └─ {event.data[:500]}
"""
                    raise DifyAPIError(error_msg)

    def stop_task(self, task_id: str, user: str) -> Dict[str, Any]:
        """
        停止任务
        仅支持流式模式。
        Args:
            task_id (str): 任务唯一标识,可从流式响应的数据块中获取
            user (str): 用户唯一标识,需要与发送消息时的user参数保持一致

        Returns:
            Dict[str, Any]: 停止响应的结果,格式如下:
            {
                "result": "success"  # 表示成功停止响应
            }
        """
        raise NotImplementedError("停止任务方法未实现")

    # 通用方法 - 这些方法在多个子类中重复出现，可以移到基类
    def upload_file(self, file_path: str, user: str, **kwargs) -> Dict[str, Any]:
        """
        上传文件到Dify API。

        Args:
            file_path (str): 要上传的文件路径
            user (str): 用户标识
            **kwargs: 额外的请求参数，如timeout、max_retries等
        Returns:
            Dict[str, Any]: 上传文件的响应数据

        Raises:
            FileNotFoundError: 当文件不存在时
            DifyAPIError: 当API请求失败时，可能的错误包括：
                - 400 no_file_uploaded: 必须提供文件
                - 400 too_many_files: 目前只接受一个文件
                - 400 unsupported_preview: 该文件不支持预览
                - 400 unsupported_estimate: 该文件不支持估算
                - 413 file_too_large: 文件太大
                - 415 unsupported_file_type: 不支持的扩展名，当前只接受文档类文件
                - 503 s3_connection_failed: 无法连接到 S3 服务
                - 503 s3_permission_denied: 无权限上传文件到 S3
                - 503 s3_file_too_large: 文件超出 S3 大小限制
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件未找到: {file_path}")

        with open(file_path, "rb") as file:
            return self.upload_file_obj(
                file, os.path.basename(file_path), user, **kwargs
            )

    def upload_file_obj(
        self, file_obj: BinaryIO, filename: str, user: str, **kwargs
    ) -> Dict[str, Any]:
        """
        使用文件对象上传文件到Dify API。

        Args:
            file_obj (BinaryIO): 文件对象
            filename (str): 文件名
            user (str): 用户标识
            **kwargs: 额外的请求参数，如timeout、max_retries等

        Returns:
            Dict[str, Any]: 上传文件的响应数据，包含以下字段：
                - id (str): 文件ID
                - name (str): 文件名
                - size (int): 文件大小（字节）
                - extension (str): 文件扩展名
                - mime_type (str): 文件MIME类型
                - created_at (int): 创建时间戳
                - created_by (uuid): 创建者ID
            例子:
            ```
            {
                'created_at': 1742181534,
                'created_by': 'df217b97-2203-4fb9-a4b6-ebe74ac6a315',
                'extension': 'png',
                'id': '88fb21ea-e0b9-48a9-a315-e44e6cfcbcb7',
                'mime_type': 'image/png',
                'name': 'test_image.png',
                'size': 289
            }
            ```

        Raises:
            DifyAPIError: 当API请求失败时，可能的错误包括：
                - 400 bad_request_key_error: 请求格式错误
                - 400 no_file_uploaded: 必须提供文件
                - 413 file_too_large: 文件太大
                - 415 unsupported_file_type: 不支持的文件类型
        """
        # 根据文件扩展名推断MIME类型
        import mimetypes

        mime_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"

        # 直接使用requests库进行请求，而不是通过_request方法
        try:
            url = urljoin(self.base_url, "files/upload")

            # 准备请求头（不包含Content-Type，让requests自动处理)
            headers = {
                "Authorization": f"Bearer {self.api_key}",
            }

            # 准备文件和表单数据
            files = {"file": (filename, file_obj, mime_type)}
            data = {"user": user}

            # 设置超时参数
            timeout = kwargs.pop("timeout", 30)

            # 直接发送请求
            response = requests.post(
                url,
                headers=headers,
                files=files,
                data=data,
                timeout=timeout,
            )

            # 检查响应状态
            if not response.ok:
                error_data = {}
                error_details = ""

                # 尝试解析错误数据
                try:
                    error_data = response.json()
                    if isinstance(error_data, dict):
                        if "error" in error_data and isinstance(
                            error_data["error"], dict
                        ):
                            error_details = error_data["error"].get("message", "")
                        else:
                            error_details = error_data.get("message", "")
                except:
                    if response.text:
                        error_details = response.text[:500]

                # 构建格式化的错误消息
                error_msg = f"""
PYDIFY:文件上传失败: 
└─ 文件信息:
   ├─ 文件名: {filename}
   ├─ MIME类型: {mime_type}
   └─ 用户: {user}
└─ 请求信息:
   └─ URL: {url}
└─ 响应信息:
   ├─ 状态码: {response.status_code} ({response.reason})
   └─ 错误详情: {error_details}
"""

                raise DifyAPIError(
                    error_msg, status_code=response.status_code, error_data=error_data
                )

            return response.json()

        except requests.RequestException as e:
            # 构建格式化的网络错误消息
            error_msg = f"""
PYDIFY:文件上传网络错误: 
└─ 文件信息:
   ├─ 文件名: {filename}
   ├─ MIME类型: {mime_type}
   └─ 用户: {user}
└─ 请求信息:
   └─ URL: {url}
└─ 错误信息:
   ├─ 类型: {type(e).__name__}
   └─ 详情: {str(e)}
"""
            raise DifyAPIError(error_msg)
        except Exception as e:
            if isinstance(e, DifyAPIError):
                raise

            # 构建格式化的通用错误消息
            error_msg = f"""
PYDIFY:文件上传失败: 
└─ 文件信息:
   ├─ 文件名: {filename}
   ├─ MIME类型: {mime_type}
   └─ 用户: {user}
└─ 错误信息:
   ├─ 类型: {type(e).__name__}
   └─ 详情: {str(e)}
"""
            raise DifyAPIError(error_msg)

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
        **kwargs,  # 添加kwargs参数支持
    ) -> Dict[str, Any]:
        """
        对消息进行反馈（点赞/点踩）。

        Args:
            message_id (str): 消息ID
            user (str): 用户标识
            rating (str, optional): 评价，可选值：'like'(点赞), 'dislike'(点踩), None(撤销)。默认为None
            content (str, optional): 反馈的具体信息。默认为None
            **kwargs: 额外的请求参数，如timeout、max_retries等

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

        return self.post(
            f"messages/{message_id}/feedbacks", json_data=payload, **kwargs
        )

    def get_app_info(self, **kwargs) -> Dict[str, Any]:
        """
        获取应用基本信息。

        Args:
            **kwargs: 额外的请求参数，如timeout、max_retries等

        Returns:
            Dict[str, Any]: 应用信息，包含名称、描述和标签

        Raises:
            DifyAPIError: 当API请求失败时
        """
        return self.get("info", **kwargs)

    ALLOWED_FILE_EXTENSIONS = {
        "image": [".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg"],
        "document": [
            ".txt",
            ".md",
            ".markdown",
            ".pdf",
            ".html",
            ".xlsx",
            ".xls",
            ".docx",
            ".csv",
            ".eml",
            ".msg",
            ".pptx",
            ".ppt",
            ".xml",
            ".epub",
        ],
        "audio": [".mp3", ".m4a", ".wav", ".webm", ".amr"],
        "video": [".mp4", ".mov", ".mpeg", ".mpga"],
    }

    def get_parameters(self, raw: bool = True, **kwargs) -> Dict[str, Any]:
        """
        获取应用参数，包括功能开关、输入参数配置、文件上传限制等。

        此方法通常用于应用初始化阶段，获取应用的各种配置参数和功能开关状态。

        Args:
            raw (bool): 是否返回原始数据，默认为True
            **kwargs: 额外的请求参数，如timeout、max_retries等

        Returns:
            Dict[str, Any]: 包含应用参数的字典，可能包含以下字段：
                - opening_statement (str): 应用开场白文本
                - suggested_questions (List[str]): 开场推荐问题列表
                - suggested_questions_after_answer (Dict): 回答后推荐问题配置
                    - enabled (bool): 是否启用此功能
                - speech_to_text (Dict): 语音转文本功能配置
                    - enabled (bool): 是否启用此功能
                - retriever_resource (Dict): 引用和归属功能配置
                    - enabled (bool): 是否启用此功能
                - annotation_reply (Dict): 标记回复功能配置
                    - enabled (bool): 是否启用此功能
                - user_input_form (List[Dict]): 用户输入表单配置列表，每项包含一个控件配置:
                    通用配置:
                        - type: 控件类型
                            - text-input: 单行文本输入
                            - paragraph: 多行文本输入
                            - select: 下拉选择框，需配置options选项列表
                            - number: 数字输入框
                            - file: 单文件上传，可限制文件类型和上传方式
                            - file-list: 多文件上传，可设置最大数量
                        - label: 显示名称
                        - variable: 变量标识
                        - required: 是否必填
                        - max_length: 最大长度限制/最大数量限制
                        - options: 选项值列表（可选）
                    file/file-list类型控件特殊配置:
                        - allowed_file_types (str): 允许的文件类型，可选值:
                            - image: 图片文件
                            - document: 文档文件
                            - audio: 音频文件
                            - video: 视频文件
                            - custom: 自定义文件类型
                        - allowed_file_extensions (List[str]): 允许的文件后缀列表
                            (仅当allowed_file_types为custom时需要配置)
                            - document类型包含: 'TXT', 'MD', 'MARKDOWN', 'PDF', 'HTML', 'XLSX',
                              'XLS', 'DOCX', 'CSV', 'EML', 'MSG', 'PPTX', 'PPT', 'XML', 'EPUB'
                            - image类型包含: 'JPG', 'JPEG', 'PNG', 'GIF', 'WEBP', 'SVG'
                            - audio类型包含: 'MP3', 'M4A', 'WAV', 'WEBM', 'AMR'
                            - video类型包含: 'MP4', 'MOV', 'MPEG', 'MPGA'
                        - allowed_file_upload_methods (List[str]): 允许的文件上传方式，可多选
                            - remote_url: 远程URL上传
                            - local_file: 本地文件上传
                - system_parameters (Dict): 系统级参数
                    - file_size_limit (int): 文档上传大小限制(MB)
                    - image_file_size_limit (int): 图片上传大小限制(MB)
                    - audio_file_size_limit (int): 音频上传大小限制(MB)
                    - video_file_size_limit (int): 视频上传大小限制(MB)
        Raises:
            DifyAPIError: 当API请求失败时

        Example:
            ```python
            # 获取应用参数
            params = client.get_parameters()

            # 示例返回数据:
            {
                "user_input_form": [
                    {
                        "label": "Query",
                        "variable": "query",
                        "required": true,
                        "max_length": 1000, # 最大长度限制
                        "type": "paragraph"
                    },
                    {
                        'label': 'Input',
                        'variable': 'input',
                        'required': True,
                        'max_length': 100, # 最大长度限制
                        "type": "text-input"
                    },
                    {
                        'label': 'Select',
                        'variable': 'select',
                        'required': True,
                        'options': ['Option1', 'Option2', 'Option3'],
                        "type": "select"
                    },
                    {
                        'label': 'Number',
                        'variable': 'number',
                        'required': True,
                        "type": "number"
                    },
                    {
                        'label': 'Image',
                        'variable': 'image',
                        'required': True,
                        "type": "file",
                        'allowed_file_types': ['image'],
                            'allowed_file_extensions': [...],
                            'allowed_file_upload_methods': ['remote_url', 'local_file']
                        }
                    },
                    {
                        'label': 'Files',
                        'variable': 'files',
                        'required': True,
                        'max_length': 3, # 最大数量限制
                        'allowed_file_types': ['image', 'document', 'audio', 'video'],
                            'allowed_file_extensions': [...]
                        },
                        "type": "file-list"
                    }
                ],
                "system_parameters": {
                    "file_size_limit": 15,
                    "image_file_size_limit": 10,
                    "audio_file_size_limit": 50,
                    "video_file_size_limit": 100
                }
            }
            ```
        """
        params = self.get("parameters", **kwargs)

        if raw:
            return params

        # 对user_input_form进行处理，使其变成一个列表
        user_input_form = []
        for item in params["user_input_form"]:
            for form_type in item:
                type_item = item[form_type]
                type_item["type"] = form_type
                if form_type in ["file", "file-list"]:
                    allowed_file_extensions = []
                    if "custom" not in type_item["allowed_file_types"]:
                        for allowed_file_type in type_item["allowed_file_types"]:
                            allowed_file_extensions.extend(
                                self.ALLOWED_FILE_EXTENSIONS[allowed_file_type]
                            )
                    else:
                        allowed_file_extensions = type_item["allowed_file_extensions"]
                    type_item["allowed_file_extensions"] = allowed_file_extensions
                user_input_form.append(type_item)
        params["user_input_form"] = user_input_form

        return params

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
        return self.post(
            f"conversations/{conversation_id}/delete", json_data={"user": user}
        )

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

    def get_suggested_questions(
        self, message_id: str, user: str, **kwargs
    ) -> Dict[str, Any]:
        """
        获取下一轮建议问题列表。

        Args:
            message_id (str): 消息ID，用于获取指定消息的建议问题
            user (str): 用户唯一标识，用于追踪用户上下文
            **kwargs: 额外的请求参数，支持timeout(超时时间)、max_retries(最大重试次数)等

        Returns:
            Dict[str, Any]: 返回包含建议问题列表的字典，格式如下:
            {
                "result": "success",  # 请求结果状态
                "data": [             # 建议问题列表
                    "问题1",
                    "问题2",
                    "问题3"
                ]
            }

        Raises:
            DifyAPIError: 当API请求失败时抛出此异常，包含详细的错误信息
        """
        endpoint = f"messages/{message_id}/suggested"

        params = {
            "user": user,
        }
        return self.get(endpoint, params=params, **kwargs)


class DifyAPIError(Exception):
    """Dify API错误异常"""

    def __init__(self, message: str, status_code: int = None, error_data: Dict = None):
        self.message = message
        self.status_code = status_code
        self.error_data = error_data or {}
        super().__init__(self.message)

    def __str__(self) -> str:
        """返回格式化的错误信息"""
        if self.status_code:
            # 如果错误信息中已经包含了状态码信息（通常是前面改进的错误格式），就直接返回消息
            if f"状态码: {self.status_code}" in self.message:
                return self.message

            # 否则，添加状态码信息
            if self.error_data:
                return f"[状态码: {self.status_code}]\n{self.message}\n└─ 错误数据: {json.dumps(self.error_data, ensure_ascii=False, indent=2)}"
            else:
                return f"[状态码: {self.status_code}]\n{self.message}"
        return self.message


def analyze_app_capabilities(client):
    """分析应用的功能和配置"""
    # 获取应用参数
    params = client.get_parameters()

    # 基本信息
    print("=== 应用功能配置分析 ===")

    # 检查基本功能
    features = []
    if "opening_statement" in params and params["opening_statement"]:
        features.append("开场白")
    if params.get("suggested_questions"):
        features.append("推荐问题")
    if params.get("suggested_questions_after_answer", {}).get("enabled"):
        features.append("回答后推荐问题")
    if params.get("speech_to_text", {}).get("enabled"):
        features.append("语音转文本")
    if params.get("retriever_resource", {}).get("enabled"):
        features.append("引用和归属")
    if params.get("annotation_reply", {}).get("enabled"):
        features.append("标记回复")

    print(f"启用的功能: {', '.join(features) if features else '无特殊功能'}")

    # 检查表单配置
    if "user_input_form" in params:
        form_types = []
        variables = []
        for item in params["user_input_form"]:
            for form_type in item:
                form_types.append(form_type)
                variables.append(item[form_type].get("variable"))

        print(f"\n表单配置: 共{len(params['user_input_form'])}个控件")
        print(f"控件类型: {', '.join(form_types)}")
        print(f"变量名列表: {', '.join(variables)}")

    # 检查文件上传能力
    if "file_upload" in params:
        upload_types = []
        for upload_type, config in params["file_upload"].items():
            if config.get("enabled"):
                upload_types.append(upload_type)

        if upload_types:
            print(f"\n支持上传文件类型: {', '.join(upload_types)}")

            # 详细的图片上传配置
            if "image" in params["file_upload"] and params["file_upload"]["image"].get(
                "enabled"
            ):
                img_config = params["file_upload"]["image"]
                print(f"图片上传限制: 最多{img_config.get('number_limits', 0)}张")
                print(
                    f"支持的传输方式: {', '.join(img_config.get('transfer_methods', []))}"
                )

    # 检查系统参数
    if "system_parameters" in params:
        print("\n系统参数限制:")
        for param, value in params["system_parameters"].items():
            print(f"- {param}: {value}MB")

    return params

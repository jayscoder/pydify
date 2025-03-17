"""
Pydify - 通用工具和基础类

此模块提供了Dify API客户端的基础类和通用工具。
"""

import json
import mimetypes
import os
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
                    if (
                        response.status_code in [429, 500, 502, 503, 504]
                        and attempt < max_retries
                    ):
                        print(
                            f"请求失败，状态码: {response.status_code}，{attempt+1}秒后重试..."
                        )
                        import time

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
                    import time

                    time.sleep(retry_delay)
                    continue

                # 提供更友好的错误信息
                error_type = type(e).__name__
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

                # 提供连接问题的建议
                suggestions = "\n请检查:\n1. 网络连接是否正常\n2. API地址是否正确\n3. 服务器是否可用\n4. SSL证书是否有效"

                raise DifyAPIError(f"{error_msg}{suggestions}")

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

    def post_stream(
        self, endpoint: str, json_data: Dict[str, Any], **kwargs
    ) -> Generator[Dict[str, Any], None, None]:
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

        # 打印请求信息，方便调试
        print(f"请求URL: {url}")
        print(f"请求参数: {json.dumps(json_data, ensure_ascii=False)[:500]}")

        for attempt in range(max_retries + 1):
            try:
                with requests.post(
                    url, json=json_data, headers=headers, stream=True, **kwargs
                ) as response:
                    if not response.ok:
                        error_msg = f"API request failed: {response.status_code}"
                        error_data = {}

                        try:
                            # 尝试解析响应内容作为JSON
                            error_data = response.json()
                            # 提取标准错误信息字段
                            if "error" in error_data and isinstance(
                                error_data["error"], dict
                            ):
                                error_msg = f"{error_msg} - {error_data['error'].get('message', '')}"
                            elif "message" in error_data:
                                error_msg = (
                                    f"{error_msg} - {error_data.get('message', '')}"
                                )
                        except Exception:
                            # 如果无法解析为JSON，提供原始响应内容
                            if response.text:
                                error_msg = (
                                    f"{error_msg} - 响应内容: {response.text[:200]}"
                                )
                            else:
                                error_msg = f"{error_msg} - 服务器未返回错误详情"

                        # 打印详细的错误信息，方便调试
                        print(f"API请求失败 ({endpoint}):")
                        print(f"状态码: {response.status_code}")
                        print(f"响应头: {dict(response.headers)}")
                        print(
                            f"响应内容: {response.text[:500] if response.text else '(无内容)'}"
                        )

                        # 如果是可重试的错误码，并且还有重试次数，则重试
                        if (
                            response.status_code in [429, 500, 502, 503, 504]
                            and attempt < max_retries
                        ):
                            print(
                                f"请求失败，状态码: {response.status_code}，{attempt+1}秒后重试..."
                            )
                            import time

                            time.sleep(retry_delay)
                            continue

                        raise DifyAPIError(
                            error_msg,
                            status_code=response.status_code,
                            error_data=error_data,
                        )

                    # 处理SSE流式响应
                    for line in response.iter_lines():
                        if line:
                            line = line.decode("utf-8")
                            if line.startswith("data: "):
                                data = line[6:]  # 移除 'data: ' 前缀
                                try:
                                    yield json.loads(data)
                                except json.JSONDecodeError as e:
                                    # 打印警告信息并继续处理
                                    print(
                                        f"警告: 无法解析流式响应行为JSON: {data[:100]}"
                                    )
                                    # 返回一个带有错误信息的字典，而不是抛出异常
                                    yield {
                                        "error": "JSON解析错误",
                                        "raw_data": data[:100],
                                    }

                    # 如果成功完成了迭代，就跳出重试循环
                    break

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
                    import time

                    time.sleep(retry_delay)
                    continue

                # 提供更友好的错误信息
                error_type = type(e).__name__
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

                # 提供连接问题的建议
                suggestions = "\n请检查:\n1. 网络连接是否正常\n2. API地址是否正确\n3. 服务器是否可用\n4. SSL证书是否有效"

                raise DifyAPIError(f"{error_msg}{suggestions}")

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

        with open(file_path, "rb") as file:
            return self.upload_file_obj(file, os.path.basename(file_path), user)

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
            DifyAPIError: 当API请求失败时
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

    def get_app_info(self) -> Dict[str, Any]:
        """
        获取应用基本信息。

        Returns:
            Dict[str, Any]: 应用信息，包含名称、描述和标签

        Raises:
            DifyAPIError: 当API请求失败时
        """
        return self.get("info")

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

    def get_parameters(self, raw: bool = False, **kwargs) -> Dict[str, Any]:
        """
        获取应用参数，包括功能开关、输入参数配置、文件上传限制等。

        此方法通常用于应用初始化阶段，获取应用的各种配置参数和功能开关状态。

        Args:
            raw (bool): 是否返回原始数据，默认返回处理后的数据
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
        self, stream_generator: Generator[Dict[str, Any], None, None], **handlers
    ) -> Dict[str, Any]:
        """
        处理流式响应，调用相应事件处理器。子类应重写此方法以支持特定应用类型的事件。

        Args:
            stream_generator: 流式响应生成器
            **handlers: 各种事件的处理函数

        Returns:
            Dict[str, Any]: 处理结果，包含消息ID等信息
        """
        raise NotImplementedError(
            "Subclasses must implement process_streaming_response method"
        )


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

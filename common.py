"""
Pydify - 通用工具和基础类

此模块提供了Dify API客户端的基础类和通用工具。
"""

import os
import json
import requests
from urllib.parse import urljoin
from typing import Dict, Any, List, Optional, Union, Generator, Tuple


class DifyBaseClient:
    """Dify API 基础客户端类。

    提供与Dify API进行交互的基本功能，包括身份验证和HTTP请求。
    """

    def __init__(self, api_key: str, base_url: str = None):
        """
        初始化Dify API客户端。

        Args:
            api_key (str): Dify API密钥
            base_url (str, optional): API基础URL。默认为环境变量DIFY_BASE_URL或http://localhost:5000/v1
        """
        self.api_key = api_key
        self.base_url = base_url or os.environ.get("DIFY_BASE_URL", "http://localhost:5000/v1")
        if not self.base_url.endswith("/v1"):
            self.base_url = urljoin(self.base_url, "/v1")

    def _get_headers(self) -> Dict[str, str]:
        """
        获取包含认证信息的请求头。

        Returns:
            Dict[str, str]: 包含认证信息的请求头字典
        """
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
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
            requests.HTTPError: 当HTTP请求失败时
        """
        url = urljoin(self.base_url, endpoint)
        headers = kwargs.pop("headers", {})
        headers.update(self._get_headers())

        response = requests.request(method, url, headers=headers, **kwargs)
        
        if not response.ok:
            error_msg = f"API request failed: {response.status_code}"
            try:
                error_data = response.json()
                error_msg = f"{error_msg} - {error_data.get('error', {}).get('message', '')}"
            except ValueError:
                pass
            
            raise requests.HTTPError(error_msg, response=response)
        
        return response

    def get(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        """
        发送GET请求到Dify API。

        Args:
            endpoint (str): API端点
            **kwargs: 传递给requests的其他参数

        Returns:
            Dict[str, Any]: 响应的JSON数据
        """
        response = self._request("GET", endpoint, **kwargs)
        return response.json()

    def post(self, endpoint: str, data: Dict[str, Any] = None, json_data: Dict[str, Any] = None, **kwargs) -> Dict[str, Any]:
        """
        发送POST请求到Dify API。

        Args:
            endpoint (str): API端点
            data (Dict[str, Any], optional): 表单数据
            json_data (Dict[str, Any], optional): JSON数据
            **kwargs: 传递给requests的其他参数

        Returns:
            Dict[str, Any]: 响应的JSON数据
        """
        response = self._request("POST", endpoint, data=data, json=json_data, **kwargs)
        return response.json()

    def post_stream(self, endpoint: str, json_data: Dict[str, Any], **kwargs) -> Generator[Dict[str, Any], None, None]:
        """
        发送流式POST请求到Dify API。

        Args:
            endpoint (str): API端点
            json_data (Dict[str, Any]): JSON数据
            **kwargs: 传递给requests的其他参数

        Yields:
            Dict[str, Any]: 每个响应块的JSON数据
        """
        url = urljoin(self.base_url, endpoint)
        headers = kwargs.pop("headers", {})
        headers.update(self._get_headers())

        with requests.post(url, json=json_data, headers=headers, stream=True, **kwargs) as response:
            if not response.ok:
                error_msg = f"API request failed: {response.status_code}"
                try:
                    error_data = response.json()
                    error_msg = f"{error_msg} - {error_data.get('error', {}).get('message', '')}"
                except ValueError:
                    pass
                
                raise requests.HTTPError(error_msg, response=response)
            
            # 处理SSE流式响应
            for line in response.iter_lines():
                if line:
                    line = line.decode('utf-8')
                    if line.startswith('data: '):
                        data = line[6:]  # 移除 'data: ' 前缀
                        try:
                            yield json.loads(data)
                        except json.JSONDecodeError:
                            # 忽略无法解析的行
                            pass

    def upload_file(self, file_path: str, user: str) -> Dict[str, Any]:
        """
        上传文件到Dify API。

        Args:
            file_path (str): 要上传的文件路径
            user (str): 用户标识

        Returns:
            Dict[str, Any]: 上传文件的响应数据
        """
        with open(file_path, 'rb') as file:
            files = {'file': file}
            data = {'user': user}
            url = urljoin(self.base_url, 'files/upload')
            
            headers = self._get_headers()
            # 移除Content-Type，让requests自动设置multipart/form-data
            headers.pop('Content-Type', None)
            
            response = requests.post(url, headers=headers, files=files, data=data)
            
            if not response.ok:
                error_msg = f"File upload failed: {response.status_code}"
                try:
                    error_data = response.json()
                    error_msg = f"{error_msg} - {error_data.get('error', {}).get('message', '')}"
                except ValueError:
                    pass
                
                raise requests.HTTPError(error_msg, response=response)
            
            return response.json()

class DifyAPIError(Exception):
    """Dify API错误异常"""
    
    def __init__(self, message: str, status_code: int = None, error_data: Dict = None):
        self.message = message
        self.status_code = status_code
        self.error_data = error_data or {}
        super().__init__(self.message)

"""
Pydify - Dify 网站API交互

此模块提供与Dify网站API交互的工具。
"""

import time
from typing import Callable, List, Union

import requests
import yaml

from .config import *


class DifySite:
    """
    Dify网站API交互类，提供与Dify平台管理API的交互功能

    此类封装了Dify平台的所有管理API，包括登录认证、应用管理、API密钥管理等功能。
    初始化时会自动登录并获取访问令牌，后续所有API调用都会使用此令牌进行认证。
    """

    def __init__(self, base_url, email, password):
        """
        初始化DifySite实例并自动登录获取访问令牌

        Args:
            base_url (str): Dify平台的基础URL，例如 "http://sandanapp.com:11080"
            email (str): 登录邮箱账号
            password (str): 登录密码

        Raises:
            Exception: 登录失败时抛出异常，包含错误信息
        """
        if base_url.endswith("/"):
            base_url = base_url[:-1]
        self.base_url = base_url
        self.email = email
        self.password = password
        self.access_token = None
        self.refresh_token = None

        # 自动登录并获取访问令牌
        self._login()

    def _login(self):
        """
        登录Dify平台并获取访问令牌

        Raises:
            Exception: 登录失败时抛出异常，包含错误信息
        """
        url = f"{self.base_url}/console/api/login"
        data = {
            "email": self.email,
            "language": "zh-CN",
            "password": self.password,
            "remember_me": True,
        }
        response = requests.post(url, json=data)
        if response.status_code != 200:
            raise Exception(f"登录失败: {response.text}")

        response_data = response.json()["data"]
        self.access_token = response_data["access_token"]
        self.refresh_token = response_data["refresh_token"]

    def fetch_apps(
        self, page=1, limit=100, name="", is_created_by_me=False, keywords="", tagIDs=[]
    ):
        """
        获取Dify平台中的应用列表，支持分页和过滤条件

        Args:
            page (int, optional): 页码，从1开始. 默认为1.
            limit (int, optional): 每页返回的应用数量上限. 默认为100.
            name (str, optional): 按应用名称过滤. 默认为空字符串，不过滤.
            is_created_by_me (bool, optional): 是否只查询当前用户创建的应用. 默认为False(查询所有).
            keywords (str, optional): 关键词搜索. 默认为空字符串，不过滤.
            tagIDs (list, optional): 标签ID列表，按标签过滤. 默认为空列表，不过滤.

        Raises:
            Exception: 获取应用列表失败时抛出异常，包含错误信息

        Returns:
            dict: 应用列表的响应数据，包含以下字段：
                - page (int): 当前页码
                - limit (int): 每页数量
                - total (int): 应用总数
                - has_more (bool): 是否有更多页
                - data (list): 应用列表，每个应用包含以下字段：
                    - id (str): 应用ID
                    - name (str): 应用名称
                    - description (str): 应用描述
                    - mode (str): 应用模式，如chat、completion、workflow、agent-chat等
                    - icon_type (str): 图标类型
                    - icon (str): 图标
                    - icon_background (str): 图标背景色
                    - icon_url (str): 图标URL
                    - model_config (dict): 模型配置
                    - workflow (dict): 工作流配置
                    - created_by (str): 创建者ID
                    - created_at (int): 创建时间戳
                    - updated_by (str): 更新者ID
                    - updated_at (int): 更新时间戳
                    - tags (list): 标签列表
        """
        # 处理关键词中的空格，转换为URL编码
        keywords = keywords.replace(" ", "+")
        # 处理标签ID列表，转换为分号分隔的字符串
        tagIDs = "%3B".join(tagIDs)

        # 构建URL参数
        params = []
        if page:
            params.append(f"page={page}")
        if limit:
            params.append(f"limit={limit}")
        if name:
            params.append(f"name={name}")
        if is_created_by_me:
            params.append(f"is_created_by_me={is_created_by_me}")
        if keywords:
            params.append(f"keywords={keywords}")
        if tagIDs:
            params.append(f"tagIDs={tagIDs}")

        # 构建完整的API URL
        url = f"{self.base_url}/console/api/apps?" + "&".join(params)

        # 发送请求
        response = requests.get(
            url, headers={"Authorization": f"Bearer {self.access_token}"}
        )
        if response.status_code != 200:
            raise Exception(f"获取应用失败: {response.text}")
        return response.json()

    def fetch_all_apps(self):
        """
        获取Dify平台中的所有应用列表

        Returns:
            list: 所有应用的列表，每个应用包含详细信息
        """
        all_apps = []
        for page in range(1, 100):
            resp = self.fetch_apps(page=page, limit=100)
            all_apps.extend(resp["data"])
            if not resp["has_more"]:
                break
        return all_apps

    def fetch_app_dsl(self, app_id):
        """
        获取指定应用的DSL配置

        Args:
            app_id (str): 要获取DSL的应用ID

        Raises:
            Exception: 获取DSL失败时抛出异常，包含错误信息

        Returns:
            str: YAML格式的DSL内容
        """
        export_url = (
            f"{self.base_url}/console/api/apps/{app_id}/export?include_secret=false"
        )
        response = requests.get(
            export_url, headers={"Authorization": f"Bearer {self.access_token}"}
        )
        if response.status_code != 200:
            raise Exception(f"获取DSL失败: {response.text}")
        return response.json()["data"]

    def import_app_dsl(self, dsl: Union[str, dict], app_id=None):
        """
        将DSL配置导入为新应用

        Args:
            dsl (str): YAML格式的DSL配置内容
            app_id (str, optional): 要导入DSL的应用ID. 默认为None(创建新应用).

        Raises:
            Exception: 导入DSL失败时抛出异常，包含错误信息

        Returns:
            dict: 导入成功后的响应数据，包含新创建应用的信息:
                新创建的应用信息，包含id、name等字段
        """
        import_url = f"{self.base_url}/console/api/apps/imports"
        if isinstance(dsl, dict):
            dsl = yaml.dump(dsl)

        payload = {"mode": "yaml-content", "yaml_content": dsl}

        if app_id:
            payload["app_id"] = app_id
        response = requests.post(
            import_url,
            headers={"Authorization": f"Bearer {self.access_token}"},
            json=payload,
        )
        if response.status_code != 200:
            raise Exception(f"导入DSL失败: {response.text}")
        return response.json()

    def create_app(
        self,
        name,
        description,
        mode,
        tag_ids: Union[List[str], str] = None,
        dsl: Union[str, dict] = None,
    ):
        """
        创建新的Dify应用

        Args:
            name (str): 应用名称
            description (str): 应用描述
            mode (str): 应用模式，从DifyAppMode类中选择，如DifyAppMode.CHAT
            tag_ids (list, optional): 标签ID列表，按标签过滤. 默认为空列表，不过滤.
            dsl (str, optional): YAML格式的DSL配置内容. 默认为None(不导入DSL).

        Raises:
            Exception: 创建应用失败时抛出异常，包含错误信息

        Returns:
            dict: 创建应用成功后的响应，包含以下字段:
                - id (str): 应用ID，如"8aa70316-9c2e-4d6e-8588-617ed91b6b5c"
                - name (str): 应用名称
                - description (str): 应用描述
                - mode (str): 应用模式
                - icon (str): 应用图标
                - icon_background (str): 图标背景色
                - status (str): 应用状态
                - api_status (str): API状态
                - api_rpm (int): API每分钟请求数限制
                - api_rph (int): API每小时请求数限制
                - is_demo (bool): 是否为演示应用
                - created_at (int): 创建时间戳
        """
        create_url = f"{self.base_url}/console/api/apps"
        payload = {
            "name": name,
            "description": description,
            "mode": mode,
            "icon": "🤖",
            "icon_background": "#FFEAD5",
            "icon_type": "emoji",
        }
        response = requests.post(
            create_url,
            headers={"Authorization": f"Bearer {self.access_token}"},
            json=payload,
        )
        if response.status_code != 201:
            raise Exception(f"创建应用失败: {response.text}")

        app_info = response.json()
        app_id = app_info["id"]
        if tag_ids and len(tag_ids) > 0:
            self.bind_tag_to_app(app_id, tag_ids=tag_ids)

        if dsl:
            self.import_app_dsl(dsl, app_id=app_id)
        return app_info

    def fetch_app(self, app_id):
        """
        获取指定应用的详细信息

        Args:
            app_id (str): 要获取的应用ID

        Raises:
            Exception: 获取应用信息失败时抛出异常，包含错误信息

        Returns:
            dict: 应用的详细信息，包含以下字段:
                - id (str): 应用ID
                - name (str): 应用名称
                - description (str): 应用描述
                - mode (str): 应用模式(chat, completion, workflow等)
                - icon_type (str): 图标类型
                - icon (str): 图标内容
                - icon_background (str): 图标背景色
                - icon_url (str): 图标URL
                - enable_site (bool): 是否启用网站
                - enable_api (bool): 是否启用API
                - model_config (dict): 模型配置
                - workflow (dict): 工作流配置(仅workflow模式)
                - site (dict): 网站配置
                - api_base_url (str): API基础URL
                - use_icon_as_answer_icon (bool): 是否使用应用图标作为回答图标
                - created_by (str): 创建者ID
                - created_at (int): 创建时间戳
                - updated_by (str): 更新者ID
                - updated_at (int): 更新时间戳
                - deleted_tools (list): 已删除的工具列表
        """
        get_url = f"{self.base_url}/console/api/apps/{app_id}"
        response = requests.get(
            get_url, headers={"Authorization": f"Bearer {self.access_token}"}
        )

        if response.status_code != 200:
            raise Exception(f"获取应用信息失败: {response.text}")

        return response.json()

    def create_app_api_key(self, app_id):
        """
        为指定应用创建API密钥

        Args:
            app_id (str): 要创建API密钥的应用ID

        Raises:
            Exception: 创建API密钥失败时抛出异常，包含错误信息

        Returns:
            dict: 创建的API密钥信息，包含以下字段:
                - id (str): API密钥ID
                - type (str): 密钥类型，通常为"app"
                - token (str): API密钥令牌，例如"app-QGNv5nH4Zk9gKPCDwRklvlkp"
                - last_used_at (str|null): 最后使用时间，首次创建为null
                - created_at (int): 创建时间戳
        """
        create_url = f"{self.base_url}/console/api/apps/{app_id}/api-keys"
        response = requests.post(
            create_url, headers={"Authorization": f"Bearer {self.access_token}"}
        )
        if response.status_code != 201:
            raise Exception(f"创建API密钥失败: {response.text}")
        return response.json()

    def fetch_app_api_keys(self, app_id):
        """
        获取指定应用的所有API密钥列表

        Args:
            app_id (str): 要获取API密钥的应用ID

        Raises:
            Exception: 获取API密钥列表失败时抛出异常，包含错误信息

        Returns:
            list: API密钥列表，每个密钥包含以下字段:
                - id (str): API密钥ID
                - type (str): 密钥类型，通常为"app"
                - token (str): API密钥令牌
                - last_used_at (str|null): 最后使用时间，如果未使用过则为null
                - created_at (int): 创建时间戳
        """
        get_url = f"{self.base_url}/console/api/apps/{app_id}/api-keys"
        response = requests.get(
            get_url, headers={"Authorization": f"Bearer {self.access_token}"}
        )
        if response.status_code != 200:
            raise Exception(f"获取API密钥列表失败: {response.text}")
        return response.json()["data"]

    def delete_app_api_key(self, app_id, api_key_id):
        """
        删除指定应用的API密钥

        Args:
            app_id (str): 应用ID
            api_key_id (str): 要删除的API密钥ID

        Raises:
            Exception: 删除API密钥失败时抛出异常，包含错误信息

        Returns:
            dict: 删除操作的响应数据，如果删除成功，通常返回空对象{}
        """
        delete_url = f"{self.base_url}/console/api/apps/{app_id}/api-keys/{api_key_id}"
        response = requests.delete(
            delete_url, headers={"Authorization": f"Bearer {self.access_token}"}
        )
        if response.status_code != 204:
            raise Exception(f"删除API密钥失败: {response.text}")
        return response.json()

    def app_url(self, app_id, app_mode):
        """
        在浏览器中打开指定应用的控制台页面

        Args:
            app_id (str): 要打开的应用ID
            app_mode (str): 应用模式，应与应用创建时的模式一致
        """
        url = f"{self.base_url}/app/{app_id}/{app_mode}"
        return url

    def delete_app(self, app_id):
        """
        删除指定应用

        Args:
            app_id (str): 要删除的应用ID

        Raises:
            Exception: 删除应用失败时抛出异常，包含错误信息

        Returns:
            dict: 删除操作的响应数据，如果删除成功，通常返回空对象{}
        """
        delete_url = f"{self.base_url}/console/api/apps/{app_id}"
        response = requests.delete(
            delete_url, headers={"Authorization": f"Bearer {self.access_token}"}
        )
        if response.status_code != 204:
            raise Exception(f"删除应用失败: {response.text}")
        return response.json()

    def update_app(self, app_id, name, description):
        """
        更新指定应用的名称和描述

        Args:
            app_id (str): 要更新的应用ID
            name (str): 新的应用名称
            description (str): 新的应用描述

        Raises:
            Exception: 更新应用失败时抛出异常，包含错误信息

        Returns:
            dict: 更新应用成功后的响应数据，包含以下字段:
                - id (str): 应用ID
                - name (str): 应用名称
                - description (str): 应用描述
                - mode (str): 应用模式
                - icon (str): 应用图标
                - icon_background (str): 图标背景色
                - icon_type (str): 图标类型
        """
        update_url = f"{self.base_url}/console/api/apps/{app_id}"
        payload = {
            "name": name,
            "description": description,
            "icon": "🤖",
            "icon_background": "#FFEAD5",
            "icon_type": "emoji",
            "use_icon_as_answer_icon": True,
        }
        response = requests.put(
            update_url,
            headers={"Authorization": f"Bearer {self.access_token}"},
            json=payload,
        )
        if response.status_code != 200:
            raise Exception(f"更新应用失败: {response.text}")
        return response.json()

    def fetch_tags(self):
        """
        获取Dify平台中的所有标签列表

        Returns:
            list: 所有标签的列表，每个标签包含以下字段:
                - id (str): 标签ID
                - name (str): 标签名称
                - binding_count (str): 标签绑定数量
        """
        url = f"{self.base_url}/console/api/tags?type=app"
        response = requests.get(
            url, headers={"Authorization": f"Bearer {self.access_token}"}
        )
        if response.status_code != 200:
            raise Exception(f"获取标签列表失败: {response.text}")
        return response.json()

    def create_tag(self, name):
        """
        创建新的Dify标签

        Args:
            name (str): 标签名称

        Raises:
            Exception: 创建标签失败时抛出异常，包含错误信息

        Returns:
            dict: 创建标签成功后的响应数据，包含以下字段:
                - id (str): 标签ID
                - name (str): 标签名称
                - binding_count (str): 标签绑定数量
        """
        url = f"{self.base_url}/console/api/tags"
        # 先检查是否存在同名标签
        tags = self.fetch_tags()
        for tag in tags:
            if tag["name"] == name:
                # 存在则返回老的标签
                return tag
        # 不存在则创建
        payload = {
            "name": name,
            "type": "app",
        }
        response = requests.post(
            url, headers={"Authorization": f"Bearer {self.access_token}"}, json=payload
        )
        if response.status_code != 200:
            raise Exception(f"创建标签失败 {response.status_code} {response.text}")
        return response.json()

    def delete_tag(self, tag_id):
        """
        删除指定标签

        Args:
            tag_id (str): 要删除的标签ID

        Raises:
            Exception: 删除标签失败时抛出异常，包含错误信息

        Returns:
            dict: 删除操作的响应数据，如果删除成功，通常返回空对象{}
        """
        delete_url = f"{self.base_url}/console/api/tags/{tag_id}"
        response = requests.delete(
            delete_url, headers={"Authorization": f"Bearer {self.access_token}"}
        )
        if response.status_code != 204:
            raise Exception(f"删除标签失败: {response.text}")
        return response.json()

    def update_tag(self, tag_id, name):
        """
        更新指定标签的名称

        Args:
            tag_id (str): 要更新的标签ID
            name (str): 新的标签名称
        Raises:
            Exception: 更新标签失败时抛出异常，包含错误信息

        Returns:
            dict: 更新标签成功后的响应数据，包含以下字段:
                - id (str): 标签ID
                - name (str): 标签名称
                - type (str): 标签类型
                - binding_count (str): 标签绑定数量
        """
        update_url = f"{self.base_url}/console/api/tags/{tag_id}"
        payload = {
            "name": name,
        }
        response = requests.patch(
            update_url,
            headers={"Authorization": f"Bearer {self.access_token}"},
            json=payload,
        )
        if response.status_code != 200:
            raise Exception(f"更新标签失败: {response.text}")
        return response.json()

    def bind_tag_to_app(self, app_id, tag_ids: Union[List[str], str]):
        """
        将标签绑定到指定应用

        Args:
            app_id (str): 要绑定标签的应用ID
            tag_id (str): 要绑定的标签ID

        Raises:
            Exception: 绑定标签失败时抛出异常，包含错误信息

        Returns:
            dict: 绑定标签成功后的响应数据，为空
        """
        bind_url = f"{self.base_url}/console/api/tag-bindings/create"
        if isinstance(tag_ids, str):
            tag_ids = [tag_ids]
        payload = {
            "target_id": app_id,
            "tag_ids": tag_ids,
            "type": "app",
        }
        response = requests.post(
            bind_url,
            headers={"Authorization": f"Bearer {self.access_token}"},
            json=payload,
        )
        if response.status_code != 200:
            raise Exception(f"绑定标签失败: {response.text}")
        return response.json()

    def remove_tag_from_app(self, app_id, tag_ids: Union[List[str], str]):
        """
        从指定应用中移除标签

        Args:
            app_id (str): 要移除标签的应用ID
            tag_ids (Union[List[str], str]): 要移除的标签ID或标签ID列表

        Raises:
            Exception: 移除标签失败时抛出异常，包含错误信息

        Returns:
            dict: 移除标签成功后的响应数据，为空
        """
        remove_url = f"{self.base_url}/console/api/tag-bindings/remove"
        if isinstance(tag_ids, str):
            tag_ids = [tag_ids]
        payload = {
            "target_id": app_id,
            "tag_ids": tag_ids,
            "type": "app",
        }
        response = requests.post(
            remove_url,
            headers={"Authorization": f"Bearer {self.access_token}"},
            json=payload,
        )
        if response.status_code != 200:
            raise Exception(f"移除标签失败: {response.text}")
        return response.json()

    def fetch_tool_providers(self):
        """
        获取Dify平台中的所有工具提供者列表

        Returns:
            list: 所有工具提供者的列表，每个提供者包含以下字段:
                - id (str): 工具提供者的唯一标识符
                - author (str): 工具提供者的作者
                - name (str): 工具提供者的名称
                - plugin_id (str, optional): 插件ID，如果不是插件则为None
                - plugin_unique_identifier (str): 插件的唯一标识符
                - description (dict): 多语言描述，包含不同语言版本的描述文本
                - icon (str): 工具提供者图标的URL路径
                - label (dict): 多语言标签，包含不同语言版本的显示名称
                - type (str): 工具提供者类型，如"builtin"表示内置工具
                - team_credentials (dict): 团队凭证信息
                - is_team_authorization (bool): 是否需要团队授权
                - allow_delete (bool): 是否允许删除
                - tools (list): 该提供者提供的工具列表
                - labels (list): 工具提供者的标签列表，如"productivity"等分类
        """
        url = f"{self.base_url}/console/api/workspaces/current/tool-providers"
        response = requests.get(
            url, headers={"Authorization": f"Bearer {self.access_token}"}
        )
        if response.status_code != 200:
            raise Exception(f"获取工具提供者列表失败: {response.text}")
        return response.json()

    def publish_workflow_app(self, app_id):
        """
        发布指定工作流应用

        Args:
            app_id (str): 要发布的应用ID
            http://sandanapp.com:38080/console/api/apps/02475b04-3ce0-4191-bb16-81c7a6ced09a/workflows/publish

        """

        publish_url = f"{self.base_url}/console/api/apps/{app_id}/workflows/publish"
        payload = {"marked_comment": "", "marked_name": ""}
        response = requests.post(
            publish_url,
            headers={"Authorization": f"Bearer {self.access_token}"},
            json=payload,
        )

        if response.status_code != 200:
            raise Exception(f"发布应用失败: {response.text}")
        return response.json()

    def create_workflow_tool(
        self,
        name: str,
        label: str,
        workflow_app_id: str,
        description: str = None,
        parameters: list = None,
        labels: list = None,
        privacy_policy: str = None,
        icon: dict = None,
    ):
        """
        创建指定工作流应用的工具
        """
        create_url = f"{self.base_url}/console/api/workspaces/current/tool-provider/workflow/create"
        payload = {
            "name": name,
            "description": description if description is not None else "",
            "label": label,
            "icon": DEFAULT_ICON if icon is None else icon,
            "parameters": parameters if parameters is not None else [],
            "labels": labels if labels is not None else [],
            "privacy_policy": privacy_policy if privacy_policy is not None else "",
            "workflow_app_id": workflow_app_id,
        }
        response = requests.post(
            create_url,
            headers={"Authorization": f"Bearer {self.access_token}"},
            json=payload,
        )
        if response.status_code != 200:
            raise Exception(f"创建工具失败: {response.text}")
        return self.fetch_workflow_tool(
            workflow_app_id=workflow_app_id, workflow_tool_id=None
        )

    def update_workflow_tool(
        self,
        name: str = None,
        label: str = None,
        workflow_app_id: Union[str, None] = None,
        workflow_tool_id: Union[str, None] = None,
        description: str = None,
        parameters: list = None,
        labels: list = None,
        privacy_policy: str = None,
        icon: dict = None,
        upsert: bool = True,
    ):
        """
        更新指定工作流应用的工具
        http://sandanapp.com:38080/console/api/workspaces/current/tool-provider/workflow/update
        payload = {"name":"get_acceptance_time","description":"","icon":{"content":"🤖","background":"#FFEAD5"},"label":"获取受理时间","parameters":[{"name":"xfFile_text","description":"","form":"llm"}],"labels":[],"privacy_policy":"","workflow_tool_id":"ffd433a6-0a42-435a-ae05-5c2ef22cd9a4"}
        Args:
            workflow_tool_id (str): 要更新的工具ID
            name (str): 工具名称
            description (str): 工具描述
            label (str): 工具显示名称
            parameters (list): 工具参数列表
            labels (list): 工具标签列表
            privacy_policy (str): 隐私政策
            upsert (bool): 是否自动创建工具

        如果某个参数是None，则不更新该参数
        """
        try:
            old_tool = self.fetch_workflow_tool(
                workflow_app_id=workflow_app_id, workflow_tool_id=workflow_tool_id
            )
        except Exception as e:
            if upsert:
                return self.create_workflow_tool(
                    name=name,
                    label=label,
                    workflow_app_id=workflow_app_id,
                    description=description,
                    parameters=parameters,
                    labels=labels,
                    privacy_policy=privacy_policy,
                    icon=icon,
                )
            else:
                raise Exception(f"工具不存在: {e}")

        name = name if name is not None else old_tool["name"]
        description = (
            description if description is not None else old_tool["description"]
        )
        label = label if label is not None else old_tool["label"]
        parameters = parameters if parameters is not None else old_tool["parameters"]
        labels = labels if labels is not None else old_tool["tool"]["labels"]
        privacy_policy = (
            privacy_policy if privacy_policy is not None else old_tool["privacy_policy"]
        )
        icon = icon if icon is not None else old_tool["icon"]
        workflow_tool_id = old_tool["workflow_tool_id"]
        workflow_app_id = old_tool["workflow_app_id"]

        publish_url = f"{self.base_url}/console/api/workspaces/current/tool-provider/workflow/update"
        payload = {
            "name": name,
            "description": description,
            "icon": icon,
            "label": label,
            "parameters": parameters,
            "labels": labels,
            "privacy_policy": privacy_policy,
            "workflow_tool_id": workflow_tool_id,
        }
        response = requests.post(
            publish_url,
            headers={"Authorization": f"Bearer {self.access_token}"},
            json=payload,
        )
        if response.status_code != 200:
            raise Exception(f"发布工具失败: {response.text}")

        return self.fetch_workflow_tool(
            workflow_app_id=workflow_app_id, workflow_tool_id=workflow_tool_id
        )

    def fetch_workflow_tool(
        self, workflow_app_id: str = "", workflow_tool_id: str = ""
    ):
        """
        获取指定工作流应用的工具详情信息

        Args:
            workflow_app_id (str): 要获取工具信息的工作流应用ID

        Raises:
            Exception: 获取工具信息失败时抛出异常，包含错误信息

        Returns:
            dict: 工作流工具详细信息，包含以下字段:
                - name (str): 工具名称
                - label (str): 工具显示名称
                - workflow_tool_id (str): 工具ID
                - workflow_app_id (str): 关联的工作流应用ID
                - icon (dict): 工具图标信息，包含content(图标内容)和background(背景色)
                - description (str): 工具描述
                - parameters (list): 工具参数列表，每个参数包含:
                    - name (str): 参数名
                    - description (str): 参数描述
                    - form (str): 参数表单类型(form/llm)
                - tool (dict): 工具详细配置，包含:
                    - author (str): 作者
                    - name (str): 工具名称
                    - label (dict): 多语言标签
                    - description (dict): 多语言描述
                    - parameters (list): 详细参数配置
                    - labels (list): 标签列表
                    - output_schema (dict|null): 输出模式
                - synced (bool): 是否已同步
                - privacy_policy (str): 隐私政策
        """
        if workflow_tool_id:
            url = f"{self.base_url}/console/api/workspaces/current/tool-provider/workflow/get?workflow_tool_id={workflow_tool_id}"
        else:
            url = f"{self.base_url}/console/api/workspaces/current/tool-provider/workflow/get?workflow_app_id={workflow_app_id}"
        response = requests.get(
            url, headers={"Authorization": f"Bearer {self.access_token}"}
        )
        if response.status_code != 200:
            raise Exception(
                f"获取工具失败: {response.text} workflow_tool_id: {workflow_tool_id} workflow_app_id: {workflow_app_id}"
            )
        return response.json()

    def delete_workflow_tool(self, workflow_tool_id: str):
        """
        删除指定工作流应用的工具
        """
        delete_url = f"{self.base_url}/console/api/workspaces/current/tool-provider/workflow/delete"
        payload = {"workflow_tool_id": workflow_tool_id}
        response = requests.post(
            delete_url,
            headers={"Authorization": f"Bearer {self.access_token}"},
            json=payload,
        )
        if response.status_code != 200:
            raise Exception(f"删除工具失败: {response.text}")
        return response.json()

    def export_app_json(
        self, app_id: str, on_progress: Callable[[str, int], None] = None
    ):
        """
        导出应用的JSON数据

        Args:
            app_id (str): 应用ID
            on_progress (Callable[[str, int], None], optional): 进度回调函数. Defaults to None.

        Returns:
            dict: 导出的JSON数据
        """
        dsl_dict = {}
        tool_dict = {}

        def do_fetch(app_id: str, depth: int = 0):
            if app_id in dsl_dict or depth > 50:
                # 防止无限递归
                return

            dsl = self.fetch_app_dsl(app_id)
            dsl = yaml.safe_load(dsl)
            dsl_dict[app_id] = dsl
            for node in dsl["workflow"]["graph"]["nodes"]:
                if node["data"]["type"] == "tool":
                    tool_id = node["data"]["provider_id"]
                    tool = self.fetch_workflow_tool(workflow_tool_id=tool_id)
                    tool_dict[tool_id] = tool
                    tool_workflow_app_id = tool["workflow_app_id"]
                    if on_progress:
                        on_progress(
                            tool_workflow_app_id, len(tool_dict) + len(dsl_dict)
                        )
                    time.sleep(0.05)
                    do_fetch(tool_workflow_app_id, depth + 1)

        do_fetch(app_id)

        return {
            "version": VERSION,
            "id": app_id,
            "name": dsl_dict[app_id]["app"]["name"],
            "dsl": dsl_dict,
            "tool": tool_dict,
        }

    def import_app_json(
        self, json_data: dict, prefix: str, suffix: str, tag_ids: list[str]
    ):
        """
        导入JSON数据到Dify

        Args:
            json_data (dict): 导入的JSON数据
            prefix (str): 前缀
            suffix (str): 后缀
            tag_ids (list[str]): 标签ID列表
            override (bool, optional): 是否覆盖已存在的应用. Defaults to False.

        Raises:
            Exception: 导入的JSON数据中缺少dsl
            Exception: 导入的JSON数据中缺少tool
            Exception: 工具名称已存在
            Exception: 应用名称已存在
        """
        # 获取client中所有的app
        if "dsl" not in json_data:
            raise Exception("JSON数据中缺少dsl")
        if "tool" not in json_data:
            raise Exception("JSON数据中缺少tool")

        exist_apps = self.fetch_all_apps()
        exist_apps_map = {app["name"]: app["id"] for app in exist_apps}
        exist_tool_providers = self.fetch_tool_providers()
        exist_tool_providers_map = {
            provider["name"]: provider for provider in exist_tool_providers
        }

        # 修改所有tool的名称
        create_tool_payloads = {}
        for tool in json_data["tool"].values():
            tool["name"] = prefix + tool["name"] + suffix
            tool["label"] = prefix + tool["label"] + suffix
            if tool["name"] in exist_tool_providers_map:
                raise Exception(f'工具 {tool["name"]} 已存在')
            create_tool_payloads[tool["workflow_app_id"]] = tool

        # 修改所有app的名称
        create_app_payloads = {}

        for app_id, dsl in json_data["dsl"].items():
            new_name = prefix + dsl["app"]["name"] + suffix
            if new_name in exist_apps_map:
                raise Exception(f"应用 {new_name} 已存在")
            dsl["app"]["name"] = new_name
            create_app_payloads[new_name] = {
                "name": new_name,
                "description": dsl["app"]["description"],
                "mode": dsl["app"]["mode"],
                "tag_ids": tag_ids,
                "dsl": dsl,
                "tool": create_tool_payloads.get(app_id, None),
            }

        old_tool_mapping = {}  # 老的tool_id -> 新的tool

        for payload in create_app_payloads.values():
            payload["id"] = self.create_app(
                name=payload["name"],
                description=payload["description"],
                mode=payload["mode"],
                tag_ids=payload["tag_ids"],
                dsl=payload["dsl"],
            )["id"]

            if payload["tool"]:
                self.publish_workflow_app(payload["id"])
                tool = self.create_workflow_tool(
                    name=payload["tool"]["name"],
                    label=payload["tool"]["label"],
                    workflow_app_id=payload["id"],
                    description=payload["tool"]["description"],
                    parameters=payload["tool"].get("parameters", None),
                    labels=payload["tool"]["tool"].get("labels", None),
                    privacy_policy=payload["tool"].get("privacy_policy", None),
                    icon=payload["tool"].get("icon", None),
                )
                old_tool_mapping[payload["tool"]["workflow_tool_id"]] = tool
                payload["tool"] = tool

        # 更新所有的dsl中引用的provider_id为新的tool_id
        for payload in create_app_payloads.values():
            dsl = payload["dsl"]
            for node in dsl["workflow"]["graph"]["nodes"]:
                if node["data"]["type"] == "tool":
                    new_tool = old_tool_mapping[node["data"]["provider_id"]]
                    node["data"]["provider_id"] = new_tool["workflow_tool_id"]
                    node["data"]["provider_name"] = new_tool["name"]
                    node["data"]["tool_label"] = new_tool["label"]
                    node["data"]["tool_name"] = new_tool["name"]

            # 更新dsl
            self.import_app_dsl(dsl=dsl, app_id=payload["id"])
            # 发布
            self.publish_workflow_app(payload["id"])
            # 重新更新工具
            if payload["tool"]:
                self.update_workflow_tool(
                    name=payload["tool"]["name"],
                    label=payload["tool"]["label"],
                    workflow_app_id=payload["id"],
                    upsert=True,
                )

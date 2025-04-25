"""
Pydify - Dify 网站API交互

此模块提供与Dify网站API交互的工具。
"""

import webbrowser

import requests


# Dify应用模式的枚举类，用于创建应用时指定应用类型
class DifyAppMode:
    """
    Dify应用模式的枚举类，定义了Dify支持的所有应用类型
    """

    CHAT = "chat"  # 聊天助手chatbot
    AGENT_CHAT = "agent-chat"  # Agent - 代理模式
    COMPLETION = "completion"  # 文本生成应用
    ADVANCED_CHAT = "advanced-chat"  # Chatflow - 高级聊天流
    WORKFLOW = "workflow"  # 工作流应用


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

    def import_app_dsl(self, dsl, app_id=None):
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

    def create_app(self, name, description, mode):
        """
        创建新的Dify应用

        Args:
            name (str): 应用名称
            description (str): 应用描述
            mode (str): 应用模式，从DifyAppMode类中选择，如DifyAppMode.CHAT

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
        return response.json()

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

    def jump_to_app(self, app_id, app_mode):
        """
        在浏览器中打开指定应用的控制台页面

        Args:
            app_id (str): 要打开的应用ID
            app_mode (str): 应用模式，应与应用创建时的模式一致
        """
        url = f"{self.base_url}/console/apps/{app_id}/{app_mode}"
        # 使用默认浏览器打开
        webbrowser.open(url)

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

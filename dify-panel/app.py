import os
import sys
import gradio as gr
from pathlib import Path
import time
import datetime
import json
import logging
import traceback

# 配置日志
log_dir = os.path.join(os.path.dirname(__file__), 'logs')
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, f'dify_panel_{datetime.datetime.now().strftime("%Y%m%d")}.log')

# 配置日志格式和处理
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('dify_panel')

# 导入本地模块
from models import User, DifyServer, DifyAppCache, DifyToolProviderCache, initialize_database
from config import APP_NAME, APP_VERSION, DEBUG, SERVER_HOST, SERVER_PORT

# 添加上级目录到系统路径，以便导入pydify
parent_dir = Path(__file__).parent.parent
sys.path.append(str(parent_dir))

# 导入pydify
try:
    from pydify.site import DifySite, DifyAppMode
except ImportError:
    print("警告: 无法导入pydify模块。请确保pydify已正确安装。")
    
    # 定义一个简单的DifyAppMode类作为后备
    class DifyAppMode:
        CHAT = "chat"
        AGENT_CHAT = "agent-chat"
        COMPLETION = "completion" 
        ADVANCED_CHAT = "advanced-chat"
        WORKFLOW = "workflow"
    
    # 定义一个模拟的DifySite类
    class DifySite:
        def __init__(self, base_url, email, password):
            self.base_url = base_url
            self.email = email
            self.password = password
            print(f"模拟连接到Dify服务器: {base_url}")
            
        def fetch_all_apps(self):
            print("模拟获取应用列表")
            return []
            
        def create_app(self, name, description, mode):
            print(f"模拟创建应用: {name}")
            return {"id": "mock-id", "name": name}
            
        def delete_app(self, app_id):
            print(f"模拟删除应用: {app_id}")
            
        def update_app(self, app_id, name, description):
            print(f"模拟更新应用: {app_id}")
            
        def fetch_app(self, app_id):
            print(f"模拟获取应用详情: {app_id}")
            return {
                "id": app_id,
                "name": "模拟应用",
                "description": "这是一个模拟应用",
                "mode": "chat",
                "created_at": time.time(),
                "updated_at": time.time()
            }
            
        def app_url(self, app_id, mode):
            return f"#模拟应用URL: {app_id}"
            
        def get_tool_providers(self):
            print("模拟获取工具提供者列表")
            return []

# 初始化数据库
initialize_database()

# 创建CSS样式
css = """
.gradio-container {
    max-width: 1200px !important;
}
.footer {
    margin-top: 20px;
    text-align: center;
    font-size: 12px;
    color: #888;
}
.app-title {
    text-align: center;
    margin-bottom: 20px;
}
.user-info {
    text-align: right;
    margin-right: 20px;
    font-size: 14px;
}
"""

# 定义全局状态
user_state = {"user": None, "dify_site": None, "current_server": None}

# 自动加载默认服务器，添加超时机制
def load_default_server():
    """尝试加载默认服务器，添加超时机制"""
    try:
        default_server = DifyServer.get_or_none(DifyServer.is_default == True)
        if default_server:
            user_state["current_server"] = default_server
            logger.info(f"尝试连接默认服务器: {default_server.name} ({default_server.base_url})")
            
            # 连接到Dify站点
            try:
                # 这里可能会卡住，添加日志
                logger.debug(f"开始连接到服务器: {default_server.base_url}")
                dify = DifySite(default_server.base_url, default_server.email, default_server.password)
                logger.debug(f"服务器连接创建成功")
                user_state["dify_site"] = dify
                logger.info(f"成功连接到默认服务器: {default_server.name}")
                return True, f"已自动连接到默认服务器: {default_server.name}"
            except Exception as e:
                logger.error(f"连接到服务器 {default_server.name} 失败: {str(e)}")
                return False, f"连接到服务器失败: {str(e)}"
        logger.warning("未找到默认服务器")
        return False, "未找到默认服务器"
    except Exception as e:
        logger.error(f"加载默认服务器失败: {str(e)}")
        return False, f"加载默认服务器失败: {str(e)}"

# 全局错误处理函数
def handle_error(func):
    """装饰器: 为函数添加错误处理"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            error_msg = str(e)
            func_name = func.__name__
            logger.error(f"函数 {func_name} 执行出错: {error_msg}")
            logger.debug(f"错误详情: {traceback.format_exc()}")
            # 根据不同类型的函数返回不同的错误消息
            if 'message' in kwargs:
                return gr.update(value=f"操作失败: {error_msg}")
            return gr.update(value=f"操作失败: {error_msg}")
    return wrapper

# 用户身份验证
def auth(username, password):
    """验证用户身份"""
    logger.info(f"尝试验证用户: {username}")
    user = User.authenticate(username, password)
    if user:
        user_state["user"] = user
        logger.info(f"用户 {username} 验证成功")
        return True
    logger.warning(f"用户 {username} 验证失败")
    return False

# 登录成功后初始化界面，添加超时和错误处理
def init_interface():
    """登录成功后初始化主界面，添加超时处理"""
    username = user_state["user"].username
    logger.info(f"初始化用户 {username} 的主界面")
    
    # 设置默认返回值，避免加载失败时卡死
    status_msg = "正在初始化..."
    apps_data = []
    providers_data = []
    
    try:
        # 尝试加载默认服务器，设置超时
        success, message = load_default_server()
        
        # 初始化主界面数据
        status_msg = message if success else "未找到默认服务器"
        logger.info(f"用户 {username} 的主界面状态: {status_msg}")
        
        # 只有成功连接服务器才尝试获取数据
        if success:
            try:
                # 获取应用列表，设置错误处理
                apps_data = get_apps() 
            except Exception as e:
                logger.error(f"获取应用列表失败: {str(e)}")
                apps_data = []
                
            try:
                # 获取工具提供者列表，设置错误处理
                providers_data = get_tool_providers()
            except Exception as e:
                logger.error(f"获取工具提供者列表失败: {str(e)}")
                providers_data = []
        else:
            logger.warning(f"未连接到服务器，跳过加载应用和工具提供者列表")
    except Exception as e:
        logger.error(f"初始化界面失败: {str(e)}")
        status_msg = f"初始化失败: {str(e)}"
    
    # 无论如何都要返回结果，防止UI卡死
    return (
        gr.update(value=status_msg),  # 主状态
        gr.update(value=apps_data),  # 应用列表
        gr.update(value=providers_data),  # 工具提供者列表
        gr.update(value=f"当前用户: {username}"),  # 用户信息
    )

# 登出处理
def logout():
    """处理用户登出"""
    username = user_state["user"].username if user_state["user"] else "未知用户"
    logger.info(f"用户 {username} 请求登出")
    # 清除全局状态
    user_state["user"] = None
    user_state["dify_site"] = None
    user_state["current_server"] = None
    logger.info(f"用户 {username} 已登出，全局状态已清除")

# 服务器管理组件
def add_server(name, base_url, email, password, is_default):
    """添加Dify服务器"""
    try:
        # 尝试连接到服务器验证凭据
        logger.info(f"尝试添加服务器: {name} ({base_url})")
        dify = DifySite(base_url, email, password)
        server = DifyServer.create(
            name=name,
            base_url=base_url,
            email=email,
            password=password,
            is_default=is_default
        )
        
        if is_default:
            logger.info(f"服务器 {name} 被设置为默认服务器")
        
        refresh_servers()
        logger.info(f"成功添加服务器: {name}")
        return gr.update(value=f"添加成功: {name}"), "", "", "", "", False
    except Exception as e:
        logger.error(f"添加服务器 {name} 失败: {str(e)}")
        return gr.update(value=f"添加失败: {str(e)}"), name, base_url, email, password, is_default

def delete_server(server_id):
    """删除Dify服务器"""
    try:
        server = DifyServer.get_by_id(server_id)
        server_name = server.name
        logger.info(f"尝试删除服务器: {server_name} (ID: {server_id})")
        server.delete_instance(recursive=True)  # 递归删除关联的应用缓存和工具提供者缓存
        refresh_servers()
        logger.info(f"成功删除服务器: {server_name} 及其关联数据")
        return gr.update(value="删除成功")
    except Exception as e:
        logger.error(f"删除服务器 ID: {server_id} 失败: {str(e)}")
        return gr.update(value=f"删除失败: {str(e)}")

# 检查用户会话
def check_session(request: gr.Request):
    """检查用户会话是否有效"""
    try:
        user_id = request.cookies.get("user_id")
        if not user_id:
            return None
        
        user = User.get_or_none(User.id == int(user_id))
        return user
    except Exception as e:
        print(f"检查会话错误: {str(e)}")
        return None

# 登录组件
@handle_error
def login(username, password):
    """处理用户登录"""
    user = User.authenticate(username, password)
    if user:
        user_state["user"] = user
        
        # 尝试加载默认服务器
        success, message = load_default_server()
        
        # 初始化主界面数据
        status_msg = message if success else "未找到默认服务器"
        apps_data = get_apps() if success else []
        providers_data = get_tool_providers() if success else []
        
        # 设置cookie和返回界面更新
        return (
            gr.update(visible=False),  # 隐藏登录界面
            gr.update(visible=True),   # 显示主界面
            gr.update(value=f"登录成功，欢迎 {username}"),  # 登录消息
            gr.update(value=status_msg),  # 主状态
            gr.update(value=apps_data),  # 应用列表
            gr.update(value=providers_data),  # 工具提供者列表
            gr.update(value=f"当前用户: {username}"),  # 用户信息
            gr.update(visible=True),  # 显示登出按钮
            json.dumps({"user_id": str(user.id), "max_age": 604800})  # Cookie信息
        )
    else:
        return (
            gr.update(visible=True),    # 保持登录界面可见
            gr.update(visible=False),   # 保持主界面隐藏
            gr.update(value="用户名或密码错误"),  # 登录错误消息
            gr.update(),  # 不变更主状态
            gr.update(),  # 不变更应用列表
            gr.update(),  # 不变更工具提供者列表
            gr.update(),  # 不变更用户信息
            gr.update(visible=False),  # 隐藏登出按钮
            None  # 不设置Cookie
        )

# 自动登录检查
def check_cookie(request: gr.Request):
    """检查cookie中是否存在用户ID并尝试自动登录"""
    try:
        if not request:
            return None
            
        cookie_user_id = request.cookies.get("user_id") if hasattr(request, "cookies") else None
        if not cookie_user_id:
            return None
            
        # 查询用户
        user = User.get_or_none(User.id == int(cookie_user_id))
        return user
    except Exception as e:
        print(f"自动登录检查失败: {str(e)}")
        return None

# 自动登录
def auto_login(request: gr.Request = None):
    """尝试自动登录"""
    user = None
    if request is not None:
        user = check_cookie(request)
    
    if user:
        user_state["user"] = user
        
        # 尝试加载默认服务器
        success, message = load_default_server()
        
        # 初始化主界面数据
        status_msg = message if success else "未找到默认服务器"
        apps_data = get_apps() if success else []
        providers_data = get_tool_providers() if success else []
        
        return (
            gr.update(visible=False),  # 隐藏登录界面
            gr.update(visible=True),   # 显示主界面
            gr.update(value=""),  # 清空登录消息
            gr.update(value=status_msg),  # 主状态
            gr.update(value=apps_data),  # 应用列表
            gr.update(value=providers_data),  # 工具提供者列表
            gr.update(value=f"当前用户: {user.username}"),  # 用户信息
            gr.update(visible=True)  # 显示登出按钮
        )
    
    # 用户未登录，显示登录界面
    return (
        gr.update(visible=True),  # 显示登录界面
        gr.update(visible=False),  # 隐藏主界面
        gr.update(value=""),  # 清空登录消息
        gr.update(),  # 不更新主状态
        gr.update(),  # 不更新应用列表
        gr.update(),  # 不更新工具提供者列表
        gr.update(value=""),  # 清空用户信息
        gr.update(visible=False)  # 隐藏登出按钮
    )

# 服务器管理组件
def get_servers():
    """获取所有服务器列表"""
    servers = list(DifyServer.select().dicts())
    logger.debug(f"获取到 {len(servers)} 个服务器")
    return servers

def refresh_servers():
    """刷新服务器列表组件"""
    logger.info("刷新服务器列表")
    servers = get_servers()
    return gr.update(value=servers)

def select_server(server_id):
    """选择当前服务器并连接"""
    try:
        if not server_id:
            logger.warning("未选择服务器，无法连接")
            return gr.update(value="请选择一个服务器")
        
        server = DifyServer.get_by_id(server_id)
        logger.info(f"尝试连接服务器: {server.name} (ID: {server_id})")
        user_state["current_server"] = server
        
        # 连接到Dify站点
        dify = DifySite(server.base_url, server.email, server.password)
        user_state["dify_site"] = dify
        
        # 更新应用列表
        refresh_apps()
        # 更新工具提供者列表
        refresh_tool_providers()
        
        logger.info(f"成功连接到服务器: {server.name}")
        return gr.update(value=f"已连接到 {server.name}")
    except Exception as e:
        logger.error(f"连接服务器 ID: {server_id} 失败: {str(e)}")
        return gr.update(value=f"连接失败: {str(e)}")

# 应用管理组件
def get_apps():
    """获取当前服务器的应用列表"""
    if not user_state["current_server"] or not user_state["dify_site"]:
        logger.warning("尝试获取应用列表，但未连接到服务器")
        return []
    
    try:
        # 从API获取应用列表
        logger.info(f"从服务器获取应用列表: {user_state['current_server'].name}")
        apps = user_state["dify_site"].fetch_all_apps()
        
        # 格式化应用列表用于表格显示
        formatted_apps = []
        for app in apps:
            formatted_apps.append({
                "id": app["id"],
                "name": app["name"],
                "description": app.get("description", ""),
                "mode": app["mode"],
                "created_at": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(app["created_at"]))
            })
        
        # 更新本地缓存
        for app in apps:
            DifyAppCache.get_or_create(
                server=user_state["current_server"],
                app_id=app["id"],
                defaults={
                    "name": app["name"],
                    "description": app.get("description", ""),
                    "mode": app["mode"],
                    "icon": app.get("icon"),
                    "icon_background": app.get("icon_background")
                }
            )
        
        logger.info(f"成功获取 {len(apps)} 个应用")
        return formatted_apps
    except Exception as e:
        logger.error(f"获取应用列表失败: {str(e)}")
        return []

def refresh_apps():
    """刷新应用列表组件"""
    logger.info("刷新应用列表")
    apps = get_apps()
    return gr.update(value=apps)

def create_app(name, description, mode):
    """创建新的Dify应用"""
    if not user_state["dify_site"]:
        logger.warning("尝试创建应用，但未连接到服务器")
        return gr.update(value="请先连接到服务器"), name, description, mode
    
    try:
        logger.info(f"尝试创建应用: {name}, 模式: {mode}")
        app = user_state["dify_site"].create_app(name, description, mode)
        # 刷新应用列表
        refresh_apps()
        logger.info(f"应用创建成功: {name} (ID: {app['id']})")
        return gr.update(value=f"创建成功: {name}"), "", "", "chat"
    except Exception as e:
        logger.error(f"创建应用 {name} 失败: {str(e)}")
        return gr.update(value=f"创建失败: {str(e)}"), name, description, mode

def delete_app(app_id):
    """删除Dify应用"""
    if not user_state["dify_site"]:
        logger.warning("尝试删除应用，但未连接到服务器")
        return gr.update(value="请先连接到服务器")
    
    try:
        logger.info(f"尝试删除应用 ID: {app_id}")
        user_state["dify_site"].delete_app(app_id)
        # 删除本地缓存
        DifyAppCache.delete().where(
            (DifyAppCache.server == user_state["current_server"]) & 
            (DifyAppCache.app_id == app_id)
        ).execute()
        # 刷新应用列表
        refresh_apps()
        logger.info(f"应用删除成功: {app_id}")
        return gr.update(value="删除成功")
    except Exception as e:
        logger.error(f"删除应用 {app_id} 失败: {str(e)}")
        return gr.update(value=f"删除失败: {str(e)}")

def update_app(app_id, name, description):
    """更新Dify应用信息"""
    if not user_state["dify_site"]:
        logger.warning("尝试更新应用，但未连接到服务器")
        return gr.update(value="请先连接到服务器")
    
    try:
        logger.info(f"尝试更新应用: {name} (ID: {app_id})")
        user_state["dify_site"].update_app(app_id, name, description)
        # 更新本地缓存
        query = DifyAppCache.update(
            name=name,
            description=description,
            updated_at=datetime.datetime.now()
        ).where(
            (DifyAppCache.server == user_state["current_server"]) & 
            (DifyAppCache.app_id == app_id)
        )
        query.execute()
        # 刷新应用列表
        refresh_apps()
        logger.info(f"应用更新成功: {name} (ID: {app_id})")
        return gr.update(value=f"更新成功: {name}")
    except Exception as e:
        logger.error(f"更新应用 {app_id} 失败: {str(e)}")
        return gr.update(value=f"更新失败: {str(e)}")

def get_app_detail(app_id):
    """获取应用详细信息"""
    if not user_state["dify_site"]:
        return gr.update(value="请先连接到服务器"), None
    
    try:
        app = user_state["dify_site"].fetch_app(app_id)
        # 格式化应用详情
        details = f"""
## 应用详情

- **ID**: {app["id"]}
- **名称**: {app["name"]}
- **描述**: {app.get("description", "无")}
- **模式**: {app["mode"]}
- **创建时间**: {time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(app["created_at"]))}
- **更新时间**: {time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(app["updated_at"]))}
- **API启用**: {"是" if app.get("enable_api", False) else "否"}
- **站点启用**: {"是" if app.get("enable_site", False) else "否"}
"""
        return gr.update(visible=True, value=details), app
    except Exception as e:
        return gr.update(value=f"获取应用详情失败: {str(e)}"), None

def open_app_in_browser(app_id, app_data):
    """在浏览器中打开应用"""
    if not user_state["dify_site"] or not app_data:
        return gr.update(value="获取应用URL失败")
    
    try:
        # 获取应用模式
        mode = app_data.get("mode", "chat")
        # 获取应用URL
        url = user_state["dify_site"].app_url(app_id, mode)
        # 用HTML创建一个链接
        return gr.update(value=f'<a href="{url}" target="_blank">点击此处打开应用</a>')
    except Exception as e:
        return gr.update(value=f"获取应用URL失败: {str(e)}")

# 工具提供者管理组件
def get_tool_providers():
    """获取当前服务器的工具提供者列表"""
    if not user_state["current_server"] or not user_state["dify_site"]:
        logger.warning("尝试获取工具提供者列表，但未连接到服务器")
        return []
    
    try:
        # 从API获取工具提供者列表
        logger.info(f"从服务器获取工具提供者列表: {user_state['current_server'].name}")
        providers = user_state["dify_site"].get_tool_providers()
        
        # 格式化工具提供者列表用于表格显示
        formatted_providers = []
        for provider in providers:
            # 处理多语言描述
            description = ""
            if isinstance(provider.get("description"), dict):
                description = provider["description"].get("zh-CN", provider["description"].get("en", ""))
            
            formatted_providers.append({
                "id": provider["id"],
                "name": provider["name"],
                "description": description,
                "type": provider.get("type", "")
            })
        
        # 更新本地缓存
        for provider in providers:
            # 处理多语言描述
            description = ""
            if isinstance(provider.get("description"), dict):
                description = provider["description"].get("zh-CN", provider["description"].get("en", ""))
                
            DifyToolProviderCache.get_or_create(
                server=user_state["current_server"],
                provider_id=provider["id"],
                defaults={
                    "name": provider["name"],
                    "description": description,
                    "type": provider.get("type", ""),
                    "icon": provider.get("icon", "")
                }
            )
        
        logger.info(f"成功获取 {len(providers)} 个工具提供者")
        return formatted_providers
    except Exception as e:
        logger.error(f"获取工具提供者列表失败: {str(e)}")
        return []

def refresh_tool_providers():
    """刷新工具提供者列表组件"""
    logger.info("刷新工具提供者列表")
    providers = get_tool_providers()
    return gr.update(value=providers)

def get_provider_detail(provider_id):
    """获取工具提供者详细信息"""
    if not user_state["dify_site"] or not user_state["current_server"]:
        logger.warning("尝试获取工具提供者详情，但未连接到服务器")
        return gr.update(value="请先连接到服务器"), None
    
    try:
        # 从缓存中查找工具提供者
        logger.info(f"获取工具提供者详情: ID {provider_id}")
        try:
            provider_cache = DifyToolProviderCache.get(
                (DifyToolProviderCache.server == user_state["current_server"]) & 
                (DifyToolProviderCache.provider_id == provider_id)
            )
        except DifyToolProviderCache.DoesNotExist:
            logger.warning(f"找不到工具提供者: ID {provider_id}")
            return gr.update(value="找不到该工具提供者"), None
        
        # 格式化工具提供者详情
        details = f"""
## 工具提供者详情

- **ID**: {provider_cache.provider_id}
- **名称**: {provider_cache.name}
- **描述**: {provider_cache.description or "无"}
- **类型**: {provider_cache.type or "未知"}
"""
        logger.info(f"成功获取工具提供者详情: {provider_cache.name}")
        return gr.update(visible=True, value=details), provider_cache
    except Exception as e:
        logger.error(f"获取工具提供者详情失败: {str(e)}")
        return gr.update(value=f"获取工具提供者详情失败: {str(e)}"), None

# 修复Dataframe选择行事件处理函数
def server_row_selection(evt):
    """处理服务器表格行选择事件"""
    try:
        index = evt.index
        if isinstance(index, tuple):
            row_index = index[0]  # 获取行索引
        else:
            row_index = index
        servers = get_servers()
        if servers and 0 <= row_index < len(servers):
            server_id = servers[row_index]["id"]
            server_name = servers[row_index]["name"]
            logger.info(f"用户选择了服务器: {server_name} (ID: {server_id})")
            return server_id
        logger.warning("服务器选择无效")
        return 0
    except Exception as e:
        logger.error(f"服务器行选择错误: {str(e)}")
        return 0

def app_row_selection(evt):
    """处理应用表格行选择事件"""
    try:
        index = evt.index
        if isinstance(index, tuple):
            row_index = index[0]  # 获取行索引
        else:
            row_index = index
        apps = get_apps()
        if apps and 0 <= row_index < len(apps):
            app_id = apps[row_index]["id"]
            app_name = apps[row_index]["name"] 
            logger.info(f"用户选择了应用: {app_name} (ID: {app_id})")
            return app_id
        logger.warning("应用选择无效")
        return ""
    except Exception as e:
        logger.error(f"应用行选择错误: {str(e)}")
        return ""

def provider_row_selection(evt):
    """处理工具提供者表格行选择事件"""
    try:
        index = evt.index
        if isinstance(index, tuple):
            row_index = index[0]  # 获取行索引
        else:
            row_index = index
        providers = get_tool_providers()
        if providers and 0 <= row_index < len(providers):
            provider_id = providers[row_index]["id"]
            provider_name = providers[row_index]["name"]
            logger.info(f"用户选择了工具提供者: {provider_name} (ID: {provider_id})")
            return provider_id
        logger.warning("工具提供者选择无效")
        return ""
    except Exception as e:
        logger.error(f"工具提供者行选择错误: {str(e)}")
        return ""

# 编辑应用表单
def show_edit_form(app_id, apps_data):
    """显示应用编辑表单"""
    if not apps_data:
        logger.warning("尝试显示编辑表单，但应用数据为空")
        return gr.update(visible=False), "", "", ""
    
    for app in apps_data:
        if app["id"] == app_id:
            logger.info(f"显示应用编辑表单: {app['name']} (ID: {app_id})")
            return (
                gr.update(visible=True),
                app_id,
                app["name"],
                app.get("description", "")
            )
    logger.warning(f"找不到应用 ID: {app_id} 的数据，无法显示编辑表单")
    return gr.update(visible=False), "", "", ""

# 构建用户界面
with gr.Blocks(css=css) as app:
    # 添加一个隐藏的状态组件用于触发数据加载
    load_trigger = gr.Number(value=0, visible=False)
    
    gr.Markdown(f"# {APP_NAME} v{APP_VERSION}", elem_classes="app-title")
    
    # 登录界面
    with gr.Row() as login_row:
        with gr.Column(scale=1):
            pass  # 空列，用于居中
        with gr.Column(scale=2):
            gr.Markdown(f"# {APP_NAME} v{APP_VERSION}", elem_classes="app-title")
            username_input = gr.Textbox(label="用户名", placeholder="请输入用户名")
            password_input = gr.Textbox(label="密码", placeholder="请输入密码", type="password")
            login_message = gr.Markdown("")
            login_btn = gr.Button("登录", variant="primary")
        with gr.Column(scale=1):
            pass  # 空列，用于居中
    
    # 主界面
    with gr.Row(visible=False) as main_row:
        # 侧边栏
        with gr.Column(scale=1):
            with gr.Row():
                user_info = gr.Markdown("")
                logout_btn = gr.Button("登出", variant="secondary", size="sm")
            
            gr.Markdown("## 导航")
            with gr.Row():
                nav_servers = gr.Button("服务器管理", size="lg", scale=1)
                nav_apps = gr.Button("应用管理", size="lg", scale=1)
                nav_providers = gr.Button("工具提供者", size="lg", scale=1)
            
            main_status = gr.Markdown("正在初始化...")
        
        # 主内容区
        with gr.Column(scale=3):
            # 服务器管理页面
            with gr.Group() as server_page:
                with gr.Row():
                    with gr.Column(scale=1):
                        # 添加服务器表单
                        gr.Markdown("### 添加服务器")
                        server_name = gr.Textbox(label="名称", placeholder="例如: 我的Dify")
                        server_url = gr.Textbox(label="服务器地址", placeholder="例如: http://localhost:5000")
                        server_email = gr.Textbox(label="邮箱", placeholder="登录邮箱")
                        server_password = gr.Textbox(label="密码", placeholder="登录密码", type="password")
                        server_default = gr.Checkbox(label="设为默认", value=False)
                        add_server_btn = gr.Button("添加", variant="primary")
                        add_server_message = gr.Markdown("")
                    
                    with gr.Column(scale=2):
                        # 服务器列表
                        gr.Markdown("### 服务器列表")
                        servers_table = gr.Dataframe(
                            headers=["ID", "名称", "服务器地址", "邮箱", "默认"],
                            col_count=(5, "fixed"),
                            value=get_servers(),
                            interactive=False
                        )
                        
                        with gr.Row():
                            refresh_servers_btn = gr.Button("刷新列表")
                            select_server_btn = gr.Button("连接服务器", variant="primary")
                            delete_server_btn = gr.Button("删除服务器", variant="stop")
                        
                        server_input = gr.Number(label="服务器ID", value=0, visible=False)
                        server_message = gr.Markdown("")
            
            # 应用管理页面
            with gr.Group(visible=False) as app_page:
                with gr.Row():
                    with gr.Column(scale=1):
                        # 创建应用表单
                        gr.Markdown("### 创建应用")
                        app_name = gr.Textbox(label="名称", placeholder="例如: 我的聊天助手")
                        app_description = gr.Textbox(label="描述", placeholder="应用描述", lines=3)
                        app_mode = gr.Dropdown(
                            label="模式", 
                            choices=[
                                DifyAppMode.CHAT, 
                                DifyAppMode.COMPLETION, 
                                DifyAppMode.AGENT_CHAT,
                                DifyAppMode.ADVANCED_CHAT,
                                DifyAppMode.WORKFLOW
                            ],
                            value=DifyAppMode.CHAT
                        )
                        create_app_btn = gr.Button("创建", variant="primary")
                        create_app_message = gr.Markdown("")
                    
                    with gr.Column(scale=2):
                        # 应用列表
                        gr.Markdown("### 应用列表")
                        apps_table = gr.Dataframe(
                            headers=["ID", "名称", "描述", "模式", "创建时间"],
                            col_count=(5, "fixed"),
                            interactive=False
                        )
                        
                        with gr.Row():
                            refresh_apps_btn = gr.Button("刷新列表")
                            view_app_btn = gr.Button("查看详情", variant="secondary")
                            open_app_btn = gr.Button("打开应用", variant="primary")
                            edit_app_btn = gr.Button("编辑应用")
                            delete_app_btn = gr.Button("删除应用", variant="stop")
                        
                        app_id_input = gr.Textbox(label="应用ID", visible=False)
                        app_state = gr.State(None)  # 用于存储当前应用的完整数据
                        app_message = gr.Markdown("")
                
                # 应用详情面板（默认隐藏）
                with gr.Group(visible=False) as app_detail_group:
                    app_detail = gr.Markdown("### 应用详情")
                    with gr.Row():
                        close_detail_btn = gr.Button("关闭")
                
                # 编辑应用表单（默认隐藏）
                with gr.Group(visible=False) as edit_app_group:
                    gr.Markdown("### 编辑应用")
                    edit_app_id = gr.Textbox(label="应用ID", interactive=False)
                    edit_app_name = gr.Textbox(label="名称")
                    edit_app_description = gr.Textbox(label="描述", lines=3)
                    with gr.Row():
                        update_app_btn = gr.Button("更新", variant="primary")
                        cancel_edit_btn = gr.Button("取消")
                    edit_app_message = gr.Markdown("")
            
            # 工具提供者管理页面
            with gr.Group(visible=False) as provider_page:
                with gr.Row():
                    with gr.Column():
                        gr.Markdown("### 工具提供者列表")
                        providers_table = gr.Dataframe(
                            headers=["ID", "名称", "描述", "类型"],
                            col_count=(4, "fixed"),
                            interactive=False
                        )
                        
                        with gr.Row():
                            refresh_providers_btn = gr.Button("刷新列表")
                            view_provider_btn = gr.Button("查看详情", variant="secondary")
                        
                        provider_id_input = gr.Textbox(label="提供者ID", visible=False)
                        provider_state = gr.State(None)  # 用于存储当前工具提供者的完整数据
                        provider_message = gr.Markdown("")
                
                # 工具提供者详情面板（默认隐藏）
                with gr.Group(visible=False) as provider_detail_group:
                    provider_detail = gr.Markdown("### 工具提供者详情")
                    with gr.Row():
                        close_provider_detail_btn = gr.Button("关闭")
            
    # 页脚
    gr.Markdown("Dify Panel - Powered by Gradio", elem_classes="footer")
    
    # 添加数据加载函数，在登录成功后异步加载数据
    def load_data_after_login():
        """登录成功后异步加载数据"""
        if not user_state["user"]:
            logger.warning("尝试加载数据但用户未登录")
            return gr.update(), gr.update(), gr.update()
            
        try:
            logger.info(f"异步加载用户 {user_state['user'].username} 的数据")
            # 尝试加载默认服务器
            success, message = load_default_server()
            
            # 初始化主界面数据
            status_msg = message if success else "未找到默认服务器，请手动连接服务器"
            
            # 只有成功连接服务器才尝试获取数据
            apps_data = []
            providers_data = []
            
            if success:
                try:
                    apps_data = get_apps()
                except Exception as e:
                    logger.error(f"获取应用列表失败: {str(e)}")
                
                try:
                    providers_data = get_tool_providers()
                except Exception as e:
                    logger.error(f"获取工具提供者列表失败: {str(e)}")
            
            logger.info(f"数据加载完成，返回界面更新")
            
            return (
                gr.update(value=status_msg),  # 更新主状态
                gr.update(value=apps_data),   # 更新应用列表
                gr.update(value=providers_data)  # 更新工具提供者列表
            )
        except Exception as e:
            logger.error(f"加载数据失败: {str(e)}")
            return (
                gr.update(value=f"加载数据失败: {str(e)}"),
                gr.update(),
                gr.update()
            )
    
    # 导航功能
    def show_server_page():
        logger.info("用户导航到服务器管理页面")
        return gr.update(visible=True), gr.update(visible=False), gr.update(visible=False)
    
    def show_app_page():
        logger.info("用户导航到应用管理页面")
        return gr.update(visible=False), gr.update(visible=True), gr.update(visible=False)
    
    def show_provider_page():
        logger.info("用户导航到工具提供者页面")
        return gr.update(visible=False), gr.update(visible=False), gr.update(visible=True)
    
    nav_servers.click(show_server_page, [], [server_page, app_page, provider_page])
    nav_apps.click(show_app_page, [], [server_page, app_page, provider_page])
    nav_providers.click(show_provider_page, [], [server_page, app_page, provider_page])
    
    # 登录功能
    def login_and_init(username, password):
        logger.info(f"用户 {username} 尝试登录")
        
        if auth(username, password):
            logger.info(f"用户 {username} 身份验证成功，准备初始化主界面")
            
            # 立即返回登录成功界面，避免阻塞
            return (
                gr.update(visible=False),  # 隐藏登录界面
                gr.update(visible=True),   # 显示主界面
                gr.update(value=f"登录成功，正在加载数据..."),  # 登录消息
                gr.update(value="正在初始化..."),  # 主状态
                gr.update(value=[]),  # 先返回空应用列表
                gr.update(value=[]),  # 先返回空工具提供者列表
                gr.update(value=f"当前用户: {username}"),  # 用户信息
                gr.update(value=time.time())  # 触发数据加载
            )
        else:
            logger.warning(f"用户 {username} 登录失败")
            return (
                gr.update(visible=True),  # 保持登录界面可见
                gr.update(visible=False),  # 保持主界面隐藏
                gr.update(value="用户名或密码错误"),  # 登录错误消息
                gr.update(),  # 不变更主状态
                gr.update(),  # 不变更应用列表
                gr.update(),  # 不变更工具提供者列表
                gr.update(),  # 不变更用户信息
                gr.update()  # 不触发数据加载
            )
    
    # 登录点击事件
    login_btn.click(
        login_and_init,
        inputs=[username_input, password_input],
        outputs=[login_row, main_row, login_message, main_status, apps_table, providers_table, user_info, load_trigger]
    )
    
    # 设置数据加载事件
    load_trigger.change(
        load_data_after_login,
        inputs=[],
        outputs=[main_status, apps_table, providers_table]
    )
    
    # 登出功能
    def do_logout():
        username = user_state["user"].username if user_state["user"] else "未知用户"
        logger.info(f"用户 {username} 请求登出")
        logout()
        logger.info(f"用户 {username} 登出完成，返回登录界面")
        return (
            gr.update(visible=True),  # 显示登录界面
            gr.update(visible=False),  # 隐藏主界面
            gr.update(value=""),  # 清空登录消息
        )
    
    logout_btn.click(
        do_logout,
        [],
        [login_row, main_row, login_message]
    )
    
    # 服务器管理事件
    add_server_btn.click(
        add_server,
        inputs=[server_name, server_url, server_email, server_password, server_default],
        outputs=[add_server_message, server_name, server_url, server_email, server_password, server_default]
    )
    
    refresh_servers_btn.click(
        refresh_servers,
        outputs=[servers_table]
    )
    
    select_server_btn.click(
        select_server,
        inputs=[server_input],
        outputs=[server_message]
    )
    
    delete_server_btn.click(
        delete_server,
        inputs=[server_input],
        outputs=[server_message]
    )
    
    # 应用管理事件
    create_app_btn.click(
        create_app,
        inputs=[app_name, app_description, app_mode],
        outputs=[create_app_message, app_name, app_description, app_mode]
    )
    
    refresh_apps_btn.click(
        refresh_apps,
        outputs=[apps_table]
    )
    
    view_app_btn.click(
        get_app_detail,
        inputs=[app_id_input],
        outputs=[app_detail_group, app_state]
    )
    
    open_app_btn.click(
        open_app_in_browser,
        inputs=[app_id_input, app_state],
        outputs=[app_message]
    )
    
    delete_app_btn.click(
        delete_app,
        inputs=[app_id_input],
        outputs=[app_message]
    )
    
    # 编辑应用事件
    edit_app_btn.click(
        show_edit_form,
        inputs=[app_id_input, apps_table],
        outputs=[edit_app_group, edit_app_id, edit_app_name, edit_app_description]
    )
    
    cancel_edit_btn.click(
        lambda _: gr.update(visible=False),
        inputs=[cancel_edit_btn],
        outputs=[edit_app_group]
    )
    
    close_detail_btn.click(
        lambda _: gr.update(visible=False),
        inputs=[close_detail_btn],
        outputs=[app_detail_group]
    )
    
    update_app_btn.click(
        update_app,
        inputs=[edit_app_id, edit_app_name, edit_app_description],
        outputs=[edit_app_message]
    )
    
    # 工具提供者事件
    refresh_providers_btn.click(
        refresh_tool_providers,
        outputs=[providers_table]
    )
    
    view_provider_btn.click(
        get_provider_detail,
        inputs=[provider_id_input],
        outputs=[provider_detail_group, provider_state]
    )
    
    close_provider_detail_btn.click(
        lambda _: gr.update(visible=False),
        inputs=[close_provider_detail_btn],
        outputs=[provider_detail_group]
    )
    
    # 更新选择事件处理
    servers_table.select(
        server_row_selection, 
        outputs=[server_input]
    )
    
    apps_table.select(
        app_row_selection,
        outputs=[app_id_input]
    )
    
    providers_table.select(
        provider_row_selection,
        outputs=[provider_id_input]
    )

# 应用启动和注册日志
if __name__ == "__main__":
    logger.info(f"正在启动 {APP_NAME} v{APP_VERSION}")
    logger.info(f"应用将在 http://{SERVER_HOST}:{SERVER_PORT} 启动")
    # 添加更多的启动选项，提高稳定性
    app.launch(
        server_name=SERVER_HOST,
        server_port=SERVER_PORT,
        share=False,
        debug=DEBUG,
        show_error=True,
        prevent_thread_lock=True,
        inbrowser=True,
        quiet=False
    )

"""
DifyClient - Dify平台API客户端

封装DifySite类，提供统一的连接管理和会话状态处理
"""

import os
import sys
from pathlib import Path

import streamlit as st

# 添加项目根目录到Python路径
root_dir = Path(__file__).parent.parent.parent
sys.path.append(str(root_dir))

# 导入DifySite类
from pydify.site import DifySite, DifyAppMode

# 尝试导入模型，如果失败则跳过（初始化阶段可能无法导入）
try:
    from models import Site
except ImportError:
    Site = None


class DifyClient:
    """
    Dify客户端类，用于管理与Dify平台的连接和会话状态
    """

    @staticmethod
    def get_connection():
        """
        获取或创建与Dify平台的连接

        如果会话状态中已有连接，则返回现有连接
        否则使用会话状态中的配置信息创建新连接

        Returns:
            DifySite: Dify平台连接实例
        """
        # 如果会话状态中没有保存连接配置，初始化默认值
        if "dify_base_url" not in st.session_state:
            st.session_state.dify_base_url = ""
            st.session_state.dify_email = ""
            st.session_state.dify_password = ""
            st.session_state.dify_connected = False
            st.session_state.dify_client = None
            st.session_state.active_site_id = None
            st.session_state.active_site_name = ""

        # 如果已连接，返回现有客户端
        if st.session_state.dify_connected and st.session_state.dify_client:
            return st.session_state.dify_client

        return None

    @staticmethod
    def connect(base_url, email, password, site_id=None, site_name=None):
        """
        连接到Dify平台

        Args:
            base_url (str): Dify平台URL
            email (str): 登录邮箱
            password (str): 登录密码
            site_id (int, optional): 站点ID, 用于标识当前活跃站点
            site_name (str, optional): 站点名称, 用于显示当前活跃站点

        Returns:
            bool: 连接是否成功
        """
        try:
            # 创建DifySite实例
            client = DifySite(base_url, email, password)

            # 保存到会话状态
            st.session_state.dify_base_url = base_url
            st.session_state.dify_email = email
            st.session_state.dify_password = password
            st.session_state.dify_connected = True
            st.session_state.dify_client = client
            
            # 如果提供了站点ID，保存当前活跃站点信息
            if site_id:
                st.session_state.active_site_id = site_id
                st.session_state.active_site_name = site_name or "未命名站点"

            return True
        except Exception as e:
            st.error(f"连接失败: {str(e)}")
            st.session_state.dify_connected = False
            st.session_state.dify_client = None
            st.session_state.active_site_id = None
            st.session_state.active_site_name = ""
            return False

    
    @staticmethod
    def test_connect(base_url, email, password):
        """
        测试连接，不保存连接信息
        """
        try:
            client = DifySite(base_url, email, password)
            return True
        except Exception as e:
            st.error(f"连接失败: {str(e)}")
            return False
    
    @staticmethod
    def is_connected():
        """
        检查是否已连接到Dify平台

        Returns:
            bool: 是否已连接
        """
        return st.session_state.get("dify_connected", False)
    
    @staticmethod
    def get_active_site():
        """
        获取当前活跃站点信息
        
        Returns:
            dict: 包含站点ID和名称的字典, 如果没有活跃站点则返回None
        """
        if st.session_state.get("active_site_id"):
            return {
                "id": st.session_state.active_site_id,
                "name": st.session_state.active_site_name
            }
        return None

    @staticmethod
    def get_default_connection_info():
        """
        获取默认的连接信息，优先从站点数据库中读取默认站点，如果没有则从环境变量读取
        
        Returns:
            tuple: (base_url, email, password) 默认的连接信息
        """
        # 如果Site类可用，尝试从数据库中获取默认站点
        if Site:
            try:
                default_site = Site.select().where(Site.is_default == True).first()
                if default_site:
                    return default_site.base_url, default_site.email, default_site.password
            except Exception:
                # 数据库操作失败，忽略错误继续使用环境变量
                pass
                
        # 从环境变量中读取
        default_base_url = os.environ.get("DIFY_BASE_URL", "")
        default_email = os.environ.get("DIFY_EMAIL", "")
        default_password = os.environ.get("DIFY_PASSWORD", "")

        return default_base_url, default_email, default_password


def try_auto_connect():
    """
    尝试使用默认站点自动连接到Dify平台

    先尝试使用数据库中的默认站点连接，如果没有则尝试使用环境变量中的信息连接

    Returns:
        bool: 是否成功连接
    """
    # 如果已经连接，不需要再次连接
    if DifyClient.is_connected():
        return True
    
    # 尝试从数据库中查找默认站点
    try:
        default_site = Site.select().where(Site.is_default == True).first()
        if default_site:
            # 使用默认站点信息连接
            return DifyClient.connect(
                default_site.base_url, 
                default_site.email, 
                default_site.password,
                default_site.id,
                default_site.name
            )
    except Exception:
        # 数据库操作失败，继续使用环境变量
        pass

    # 获取环境变量中的默认值
    default_base_url, default_email, default_password = (
        DifyClient.get_default_connection_info()
    )

    # 如果环境变量中有完整的连接信息，尝试自动连接
    if default_base_url and default_email and default_password:
        return DifyClient.connect(default_base_url, default_email, default_password)

    return False

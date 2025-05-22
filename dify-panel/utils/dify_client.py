"""
DifyClient - Dify平台API客户端

封装DifySite类，提供统一的连接管理和会话状态处理
"""
import sys
import os
import streamlit as st
from pathlib import Path

# 添加项目根目录到Python路径
root_dir = Path(__file__).parent.parent.parent
sys.path.append(str(root_dir))

# 导入DifySite类
from pydify.site import DifySite, DifyAppMode

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
        if 'dify_base_url' not in st.session_state:
            st.session_state.dify_base_url = ""
            st.session_state.dify_email = ""
            st.session_state.dify_password = ""
            st.session_state.dify_connected = False
            st.session_state.dify_client = None
            
        # 如果已连接，返回现有客户端
        if st.session_state.dify_connected and st.session_state.dify_client:
            return st.session_state.dify_client
            
        return None
    
    @staticmethod
    def connect(base_url, email, password):
        """
        连接到Dify平台
        
        Args:
            base_url (str): Dify平台URL
            email (str): 登录邮箱
            password (str): 登录密码
            
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
            
            return True
        except Exception as e:
            st.error(f"连接失败: {str(e)}")
            st.session_state.dify_connected = False
            st.session_state.dify_client = None
            return False
    
    @staticmethod
    def disconnect():
        """
        断开与Dify平台的连接
        """
        st.session_state.dify_connected = False
        st.session_state.dify_client = None
        
    @staticmethod
    def is_connected():
        """
        检查是否已连接到Dify平台
        
        Returns:
            bool: 是否已连接
        """
        return st.session_state.get('dify_connected', False) 
        
    @staticmethod
    def get_default_connection_info():
        """
        从环境变量中获取默认的连接信息
        
        Returns:
            tuple: (base_url, email, password) 从环境变量中读取的默认值
        """
        default_base_url = os.environ.get('DIFY_BASE_URL', '')
        default_email = os.environ.get('DIFY_EMAIL', '')
        default_password = os.environ.get('DIFY_PASSWORD', '')
        
        return default_base_url, default_email, default_password 
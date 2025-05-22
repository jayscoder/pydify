"""
Dify管理面板 - 主页

提供Dify平台连接管理和功能导航
"""

import os
import sys
from pathlib import Path

import dotenv
import streamlit as st

# 添加当前目录到Python路径
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))

# 加载环境变量
dotenv.load_dotenv()

# 导入工具类
from utils.dify_client import DifyClient
from utils.ui_components import connection_form, page_header, success_message

# 设置页面配置
st.set_page_config(
    page_title="Dify管理面板",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)


def try_auto_connect():
    """
    尝试使用环境变量中的默认值自动连接到Dify平台

    如果环境变量中存在必要的连接信息，且尚未连接，则尝试自动连接

    Returns:
        bool: 是否成功连接
    """
    # 如果已经连接，不需要再次连接
    if DifyClient.is_connected():
        return True

    # 获取环境变量中的默认值
    default_base_url, default_email, default_password = (
        DifyClient.get_default_connection_info()
    )

    # 如果环境变量中有完整的连接信息，尝试自动连接
    if default_base_url and default_email and default_password:
        return DifyClient.connect(default_base_url, default_email, default_password)

    return False


def main():
    """主函数"""
    # 页面标题
    page_header("Dify管理面板", "通过此面板管理Dify平台上的应用、API密钥、标签和工具")

    # 尝试自动连接
    auto_connected = try_auto_connect()

    # 侧边栏导航
    with st.sidebar:
        st.title("Dify管理面板")
        st.divider()

        # 显示连接状态
        if DifyClient.is_connected():
            st.success("已连接到Dify平台")
            st.write(f"服务器: {st.session_state.dify_base_url}")
            st.write(f"账号: {st.session_state.dify_email}")

            if st.button("断开连接"):
                DifyClient.disconnect()
                st.rerun()
        else:
            st.warning("未连接到Dify平台")
            st.info("请在右侧连接表单中输入Dify平台的连接信息")

    # 主内容区域
    if not DifyClient.is_connected():
        # 显示连接表单
        st.write("### 欢迎使用Dify管理面板")
        st.write("请先连接到Dify平台，然后继续管理您的应用和资源。")

        # 如果尝试自动连接过但失败，显示错误信息
        if auto_connected is False:
            st.warning(
                "尝试使用环境变量中的连接信息自动连接失败，请手动输入正确的连接信息。"
            )

        # 显示连接表单
        base_url, email, password, submit = connection_form()

        if submit:
            with st.spinner("连接中..."):
                if DifyClient.connect(base_url, email, password):
                    success_message("连接成功！")
                    st.rerun()
    else:
        # 已连接状态，显示功能概览
        client = DifyClient.get_connection()

        # 获取应用信息
        try:
            apps = client.fetch_all_apps()
            st.write(f"### 平台概览")

            # 显示统计信息
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("应用总数", len(apps))

            # 统计不同类型的应用数量
            app_types = {}
            for app in apps:
                mode = app.get("mode", "unknown")
                app_types[mode] = app_types.get(mode, 0) + 1

            with col2:
                st.metric(
                    "聊天应用",
                    app_types.get("chat", 0) + app_types.get("agent-chat", 0),
                )

            with col3:
                st.metric(
                    "其他应用",
                    len(apps)
                    - app_types.get("chat", 0)
                    - app_types.get("agent-chat", 0),
                )

            # 显示功能导航
            st.divider()
            st.write("### 功能导航")

            # 创建三列导航区
            nav_col1, nav_col2, nav_col3 = st.columns(3)

            with nav_col1:
                st.subheader("应用管理")
                st.write("创建、编辑、删除应用，管理应用的DSL配置")
                if st.button("进入应用管理", key="nav_app"):
                    # 跳转到应用管理页面
                    st.switch_page("pages/app_management.py")

            with nav_col2:
                st.subheader("API密钥管理")
                st.write("管理应用的API密钥，创建新密钥或删除旧密钥")
                if st.button("进入API密钥管理", key="nav_api"):
                    # 跳转到API密钥管理页面
                    st.switch_page("pages/api_key_management.py")

            with nav_col3:
                st.subheader("标签管理")
                st.write("创建和管理标签，为应用添加或移除标签")
                if st.button("进入标签管理", key="nav_tags"):
                    # 跳转到标签管理页面
                    st.switch_page("pages/tag_management.py")

            # 第二行导航
            nav_col4, nav_col5, _ = st.columns(3)

            with nav_col4:
                st.subheader("工具管理")
                st.write("查看和管理工具提供者，更新工作流工具")
                if st.button("进入工具管理", key="nav_tools"):
                    # 跳转到工具管理页面
                    st.switch_page("pages/tool_management.py")

        except Exception as e:
            st.error(f"获取平台信息失败: {str(e)}")
            if st.button("重试"):
                st.rerun()


if __name__ == "__main__":
    main()

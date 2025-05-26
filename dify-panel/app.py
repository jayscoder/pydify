"""
Dify管理面板 - 主页

提供Dify平台连接管理和功能导航
"""

import json
import os
import sys
from pathlib import Path

import dotenv
import pandas as pd
import streamlit as st
from config import Pages
from utils.dsl_components import dsl_graph
from utils.ui_components import (
    action_bar,
    data_display,
    detail_dialog,
    page_header,
    show_detail_dialog,
    site_sidebar,
)

# 添加当前目录到Python路径
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))

# 加载环境变量
dotenv.load_dotenv()

# 导入工具类和模型
from models import Site, create_tables
from utils.dify_client import DifyClient
from utils.ui_components import connection_form, success_message

# 创建数据库表（如果不存在）
create_tables()

# 设置页面配置
st.set_page_config(
    page_title="Dify管理面板",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 初始化会话状态变量
if "dialog_open" not in st.session_state:
    st.session_state.dialog_open = False


def open_dialog():
    """打开对话框"""
    st.session_state.dialog_open = True


def close_dialog():
    """关闭对话框"""
    st.session_state.dialog_open = False


def test_callback(value):
    """测试回调函数"""
    st.session_state.selected_value = value
    st.toast(f"选择的值: {value}")


def show_detail_content(selected_row):
    """
    显示选中行的详细信息（在对话框中使用）

    Args:
        selected_row (DataFrame): 选中的行数据
    """
    if selected_row.empty:
        st.info("未选择数据")
        return

    # 显示所有列的信息
    for col in selected_row.columns:
        if col != "_id":  # 不显示内部ID字段
            st.write(f"**{col}**: {selected_row[col].iloc[0]}")

    # 可以在这里添加更多操作按钮
    st.divider()
    if st.button("编辑", key="dialog_edit"):
        st.write("编辑功能将在这里实现")

    if st.button("删除", key="dialog_delete"):
        st.write("删除功能将在这里实现")


def main():
    """主函数"""
    # 页面标题
    page_header("Dify管理面板", "通过此面板管理Dify平台上的应用、API密钥、标签和工具")

    site_sidebar()

    # 主内容区域
    if not DifyClient.is_connected():
        # 显示连接表单
        st.write("### 欢迎使用Dify管理面板")
        st.write("请先连接到Dify平台，然后继续管理您的应用和资源。")

        # 如果尝试自动连接过但失败，显示错误信息
        if auto_connected is False:
            st.warning("尝试使用默认站点连接失败，请手动输入正确的连接信息。")

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

            st.write("### 功能导航")

            # 创建三列导航区
            nav_col1, nav_col2, nav_col3 = st.columns(3)

            with nav_col1:
                st.subheader("应用管理")
                st.write("创建、编辑、删除应用，管理应用的DSL配置")
                if st.button("进入应用管理", key="nav_app"):
                    # 跳转到应用管理页面
                    st.switch_page(Pages.APP_MANAGEMENT)

            with nav_col2:
                st.subheader("API密钥管理")
                st.write("管理应用的API密钥，创建新密钥或删除旧密钥")
                if st.button("进入API密钥管理", key="nav_api"):
                    # 跳转到API密钥管理页面
                    st.switch_page(Pages.API_KEY_MANAGEMENT)

            with nav_col3:
                st.subheader("标签管理")
                st.write("创建和管理标签，为应用添加或移除标签")
                if st.button("进入标签管理", key="nav_tags"):
                    # 跳转到标签管理页面
                    st.switch_page(Pages.TAG_MANAGEMENT)

            # 第二行导航
            nav_col4, nav_col5, nav_col6 = st.columns(3)

            with nav_col4:
                st.subheader("工具管理")
                st.write("查看和管理工具提供者，更新工作流工具")
                if st.button("进入工具管理", key="nav_tools"):
                    # 跳转到工具管理页面
                    st.switch_page(Pages.TOOL_MANAGEMENT)

            with nav_col5:
                st.subheader("站点管理")
                st.write("管理和切换不同的Dify站点连接")
                if st.button("进入站点管理", key="nav_sites"):
                    # 跳转到站点管理页面
                    st.switch_page(Pages.SITE_MANAGEMENT)

        except Exception as e:
            st.error(f"获取平台信息失败: {str(e)}")
            if st.button("重试"):
                st.rerun()


if __name__ == "__main__":
    main()

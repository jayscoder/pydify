"""
Dify管理面板 - API密钥管理页面

提供查看、创建和删除API密钥的功能
"""

import sys
import time
from pathlib import Path

import pandas as pd
import streamlit as st
from config import Pages
from utils.ui_components import site_sidebar

# 添加项目根目录到Python路径
root_dir = Path(__file__).parent.parent
sys.path.append(str(root_dir))

# 导入工具类
from utils.dify_client import DifyClient
from utils.ui_components import (
    action_bar,
    app_selector,
    confirmation_dialog,
    data_display,
    detail_dialog,
    error_placeholder,
    loading_spinner,
    page_header,
    success_message,
)

# 设置页面配置
st.set_page_config(
    page_title="API密钥管理 - Dify管理面板",
    page_icon="🔑",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 初始化会话状态
if "api_key_view_mode" not in st.session_state:
    st.session_state.api_key_view_mode = "list"  # 可选值: list, create, delete
if "current_api_key_id" not in st.session_state:
    st.session_state.current_api_key_id = None
if "current_app_id" not in st.session_state:
    st.session_state.current_app_id = None
if "api_keys_cache" not in st.session_state:
    st.session_state.api_keys_cache = {}  # 键为app_id，值为API密钥列表
if "selected_api_key" not in st.session_state:
    st.session_state.selected_api_key = None


def get_apps():
    """获取应用列表"""
    if not DifyClient.is_connected():
        return []

    client = DifyClient.get_connection()
    try:
        with loading_spinner("加载应用列表..."):
            return client.fetch_all_apps()
    except Exception as e:
        st.error(f"获取应用列表失败: {str(e)}")
        return []


def get_api_keys(app_id):
    """获取指定应用的API密钥列表，带缓存机制"""
    if not app_id or not DifyClient.is_connected():
        return []

    client = DifyClient.get_connection()

    # 使用缓存
    if app_id not in st.session_state.api_keys_cache:
        try:
            with loading_spinner("加载API密钥..."):
                st.session_state.api_keys_cache[app_id] = client.fetch_app_api_keys(
                    app_id
                )
        except Exception as e:
            st.error(f"获取API密钥失败: {str(e)}")
            st.session_state.api_keys_cache[app_id] = []

    return st.session_state.api_keys_cache[app_id]


def reset_cache(app_id=None):
    """重置API密钥缓存"""
    if app_id:
        if app_id in st.session_state.api_keys_cache:
            del st.session_state.api_keys_cache[app_id]
    else:
        st.session_state.api_keys_cache = {}


def create_api_key():
    """创建API密钥"""
    st.session_state.api_key_view_mode = "create"
    st.rerun()


def delete_api_key():
    """确认删除API密钥"""
    if (
        st.session_state.selected_api_key is not None
        and not st.session_state.selected_api_key.empty
    ):
        api_key_id = st.session_state.selected_api_key.iloc[0]["_id"]
        st.session_state.api_key_view_mode = "delete"
        st.session_state.current_api_key_id = api_key_id
        st.rerun()


def back_to_list():
    """返回API密钥列表"""
    st.session_state.api_key_view_mode = "list"
    st.session_state.current_api_key_id = None
    st.session_state.selected_api_key = None
    st.rerun()


def select_app(app_id):
    """选择应用"""
    if app_id != st.session_state.current_app_id:
        st.session_state.current_app_id = app_id
        st.session_state.selected_api_key = None
        st.rerun()


def show_api_key_list():
    """显示API密钥列表"""
    page_header("API密钥管理", "管理应用的API密钥")

    # 应用选择器
    apps = get_apps()

    if not apps:
        st.warning("没有可用的应用")
        return

    # 选择应用
    selected_app_id = app_selector(apps)

    if selected_app_id:
        select_app(selected_app_id)

    # 显示当前应用的API密钥
    if st.session_state.current_app_id:
        app_name = next(
            (
                app["name"]
                for app in apps
                if app["id"] == st.session_state.current_app_id
            ),
            "未知应用",
        )

        st.subheader(f"应用 '{app_name}' 的API密钥")

        # 添加操作按钮
        actions = [
            {
                "label": "创建API密钥",
                "key": "btn_create_api_key",
                "on_click": create_api_key,
            },
            {
                "label": "刷新列表",
                "key": "btn_refresh_api_keys",
                "on_click": lambda: reset_cache(st.session_state.current_app_id)
                or st.rerun(),
            },
        ]
        action_bar(actions)

        # 获取API密钥列表
        api_keys = get_api_keys(st.session_state.current_app_id)

        # 定义表格列配置
        columns = [
            {"field": "token", "title": "API密钥"},
            {"field": "created_at", "title": "创建时间"},
            {"field": "last_used_at", "title": "最后使用时间"},
        ]

        # 处理时间戳
        for key in api_keys:
            if "created_at" in key:
                from utils.ui_components import format_timestamp

                key["created_at"] = format_timestamp(key["created_at"])
            if "last_used_at" in key and key["last_used_at"]:
                from utils.ui_components import format_timestamp

                key["last_used_at"] = format_timestamp(key["last_used_at"])
            elif "last_used_at" not in key or not key["last_used_at"]:
                key["last_used_at"] = "从未使用"

        # 显示数据表格
        selected_df = data_display(api_keys, columns, key="api_key_table")

        # 保存选中的行
        st.session_state.selected_api_key = selected_df

        # 如果选中了行，显示操作区域
        if not selected_df.empty:
            st.divider()
            st.subheader("操作")

            # 操作按钮
            key_actions = [
                {
                    "label": "删除API密钥",
                    "key": "btn_delete_selected",
                    "color": "danger",
                    "on_click": delete_api_key,
                }
            ]

            action_bar(key_actions)


def show_create_api_key():
    """显示创建API密钥表单"""
    if not st.session_state.current_app_id:
        st.error("未选择应用")
        back_to_list()
        return

    apps = get_apps()
    app_name = next(
        (app["name"] for app in apps if app["id"] == st.session_state.current_app_id),
        "未知应用",
    )

    page_header(f"创建API密钥: {app_name}", "为应用创建新的API密钥")

    # 返回按钮
    if st.button("返回", key="btn_back_create"):
        back_to_list()

    # 创建API密钥表单
    st.warning("注意：API密钥只会显示一次，请妥善保存。")

    if st.button("确认创建", key="btn_confirm_create"):
        try:
            client = DifyClient.get_connection()
            with loading_spinner("正在创建API密钥..."):
                new_api_key = client.create_app_api_key(st.session_state.current_app_id)

            # 重置缓存
            reset_cache(st.session_state.current_app_id)

            # 显示新API密钥
            st.success("API密钥创建成功！")
            st.subheader("新API密钥")
            st.code(new_api_key["token"], language=None)
            st.warning("请立即保存此API密钥，它不会再次显示。")

            # 提供返回列表的按钮
            if st.button("返回API密钥列表", key="btn_back_after_create"):
                back_to_list()
        except Exception as e:
            st.error(f"创建API密钥失败: {str(e)}")


def show_delete_api_key():
    """显示删除API密钥确认对话框"""
    if not st.session_state.current_app_id or not st.session_state.current_api_key_id:
        st.error("未选择应用或API密钥")
        back_to_list()
        return

    # 获取应用名称
    apps = get_apps()
    app_name = next(
        (app["name"] for app in apps if app["id"] == st.session_state.current_app_id),
        "未知应用",
    )

    # 获取API密钥信息
    api_keys = get_api_keys(st.session_state.current_app_id)
    api_key = next(
        (k for k in api_keys if k["id"] == st.session_state.current_api_key_id), None
    )

    if not api_key:
        st.error("找不到选定的API密钥")
        back_to_list()
        return

    # 显示确认对话框
    confirmation_dialog(
        title=f"确认删除API密钥",
        message=f"确定要删除应用 '{app_name}' 的API密钥吗？此操作不可撤销。",
        on_confirm=lambda: perform_delete(
            st.session_state.current_app_id, st.session_state.current_api_key_id
        ),
        on_cancel=back_to_list,
    )


def perform_delete(app_id, api_key_id):
    """执行删除API密钥操作"""
    try:
        client = DifyClient.get_connection()
        with loading_spinner("正在删除API密钥..."):
            client.delete_app_api_key(app_id, api_key_id)

        # 重置缓存
        reset_cache(app_id)

        # 显示成功消息
        success_message("API密钥删除成功！")

        # 延迟1秒，确保用户看到成功消息
        time.sleep(1)

        # 返回API密钥列表
        back_to_list()
    except Exception as e:
        st.error(f"删除API密钥失败: {str(e)}")


def main():
    """主函数"""
    site_sidebar()
    
    # 检查连接状态
    if not DifyClient.is_connected():
        st.warning("未连接到Dify平台")
        st.info("请先在主页连接到Dify平台")

        # 返回主页按钮
        if st.button("返回主页"):
            st.switch_page(Pages.HOME)
        return


    # 根据当前视图模式显示不同的内容
    if st.session_state.api_key_view_mode == "list":
        show_api_key_list()
    elif st.session_state.api_key_view_mode == "create":
        show_create_api_key()
    elif st.session_state.api_key_view_mode == "delete":
        show_delete_api_key()
    else:
        st.error("未知的视图模式")
        back_to_list()


if __name__ == "__main__":
    main()

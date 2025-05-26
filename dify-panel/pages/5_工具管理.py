"""
Dify管理面板 - 工具管理页面

提供工具提供者查看和工作流工具管理功能
"""

import json
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
    data_display,
    detail_dialog,
    error_placeholder,
    loading_spinner,
    page_header,
    success_message,
)

# 设置页面配置
st.set_page_config(
    page_title="工具管理 - Dify管理面板",
    page_icon="🛠️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 初始化会话状态
if "tool_view_mode" not in st.session_state:
    st.session_state.tool_view_mode = "list"  # 可选值: list, details, workflow_apps, workflow_tool, edit_workflow_tool
if "current_tool_provider" not in st.session_state:
    st.session_state.current_tool_provider = None
if "current_workflow_app_id" not in st.session_state:
    st.session_state.current_workflow_app_id = None
if "tool_providers_cache" not in st.session_state:
    st.session_state.tool_providers_cache = None
if "workflow_apps_cache" not in st.session_state:
    st.session_state.workflow_apps_cache = None
if "workflow_tool_cache" not in st.session_state:
    st.session_state.workflow_tool_cache = None
if "selected_provider" not in st.session_state:
    st.session_state.selected_provider = None
if "selected_workflow_app" not in st.session_state:
    st.session_state.selected_workflow_app = None


def get_tool_providers():
    """获取工具提供者列表，带缓存机制"""
    if not DifyClient.is_connected():
        return []

    client = DifyClient.get_connection()

    # 使用缓存
    if st.session_state.tool_providers_cache is None:
        try:
            with loading_spinner("加载工具提供者..."):
                st.session_state.tool_providers_cache = client.fetch_tool_providers()
        except Exception as e:
            st.error(f"获取工具提供者失败: {str(e)}")
            st.session_state.tool_providers_cache = []

    return st.session_state.tool_providers_cache


def get_workflow_apps():
    """获取工作流应用列表，带缓存机制"""
    if not DifyClient.is_connected():
        return []

    client = DifyClient.get_connection()

    # 使用缓存
    if st.session_state.workflow_apps_cache is None:
        try:
            with loading_spinner("加载工作流应用..."):
                apps = client.fetch_all_apps()
                # 过滤出工作流类型的应用
                workflow_apps = [app for app in apps if app.get("mode") == "workflow"]
                st.session_state.workflow_apps_cache = workflow_apps
        except Exception as e:
            st.error(f"获取工作流应用失败: {str(e)}")
            st.session_state.workflow_apps_cache = []

    return st.session_state.workflow_apps_cache


def get_workflow_tool(app_id):
    """获取工作流工具详情，带缓存机制"""
    if not app_id or not DifyClient.is_connected():
        return None

    client = DifyClient.get_connection()

    # 使用缓存
    if (
        st.session_state.workflow_tool_cache is None
        or st.session_state.current_workflow_app_id != app_id
    ):
        try:
            with loading_spinner("加载工作流工具详情..."):
                st.session_state.workflow_tool_cache = client.fetch_workflow_tool(
                    app_id
                )
                st.session_state.current_workflow_app_id = app_id
        except Exception as e:
            st.error(f"获取工作流工具详情失败: {str(e)}")
            st.session_state.workflow_tool_cache = None

    return st.session_state.workflow_tool_cache


def reset_cache(cache_type=None):
    """重置缓存

    Args:
        cache_type (str, optional): 缓存类型，可选值: provider, workflow_app, workflow_tool, all
    """
    if cache_type == "provider" or cache_type == "all":
        st.session_state.tool_providers_cache = None
    if cache_type == "workflow_app" or cache_type == "all":
        st.session_state.workflow_apps_cache = None
    if cache_type == "workflow_tool" or cache_type == "all":
        st.session_state.workflow_tool_cache = None
    if cache_type is None:
        st.session_state.tool_providers_cache = None


def view_provider_details():
    """查看工具提供者详情"""
    if (
        st.session_state.selected_provider is not None
        and not st.session_state.selected_provider.empty
    ):
        provider_id = st.session_state.selected_provider.iloc[0]["id"]
        provider = next(
            (p for p in get_tool_providers() if p["id"] == provider_id), None
        )
        if provider:
            st.session_state.tool_view_mode = "details"
            st.session_state.current_tool_provider = provider
            st.rerun()


def view_workflow_apps():
    """查看工作流应用列表"""
    st.session_state.tool_view_mode = "workflow_apps"
    st.rerun()


def view_workflow_tool():
    """查看工作流工具详情"""
    if (
        st.session_state.selected_workflow_app is not None
        and not st.session_state.selected_workflow_app.empty
    ):
        app_id = st.session_state.selected_workflow_app.iloc[0]["id"]
        st.session_state.tool_view_mode = "workflow_tool"
        st.session_state.current_workflow_app_id = app_id
        st.rerun()


def edit_workflow_tool():
    """编辑工作流工具"""
    if (
        st.session_state.selected_workflow_app is not None
        and not st.session_state.selected_workflow_app.empty
    ):
        app_id = st.session_state.selected_workflow_app.iloc[0]["id"]
        st.session_state.tool_view_mode = "edit_workflow_tool"
        st.session_state.current_workflow_app_id = app_id
        st.rerun()


def back_to_list():
    """返回工具提供者列表"""
    st.session_state.tool_view_mode = "list"
    st.session_state.current_tool_provider = None
    st.session_state.selected_provider = None
    st.rerun()


def back_to_workflow_apps():
    """返回工作流应用列表"""
    st.session_state.tool_view_mode = "workflow_apps"
    st.session_state.current_workflow_app_id = None
    st.session_state.selected_workflow_app = None
    st.rerun()


def show_tool_provider_list():
    """显示工具提供者列表"""
    page_header("工具管理", "管理Dify平台上的工具提供者和工作流工具")

    # 主要功能切换按钮区
    actions = [
        {
            "label": "管理工作流工具",
            "key": "btn_workflow_tools",
            "on_click": view_workflow_apps,
        },
        {
            "label": "刷新列表",
            "key": "btn_refresh_providers",
            "on_click": lambda: reset_cache() or st.rerun(),
        },
    ]
    action_bar(actions)

    # 获取工具提供者列表
    providers = get_tool_providers()

    # 创建筛选类型的复选框
    provider_types = sorted(
        list(set(provider.get("type", "unknown") for provider in providers))
    )
    selected_types = st.multiselect(
        "筛选工具提供者类型", options=provider_types, default=provider_types
    )

    # 筛选工具提供者
    filtered_providers = [
        p for p in providers if p.get("type", "unknown") in selected_types
    ]

    # 显示数据表格
    selected_df = data_display(filtered_providers, columns=None, key="provider_table")

    # 保存选中的行
    st.session_state.selected_provider = selected_df

    # 如果选中了行，显示操作区域
    if not selected_df.empty:
        st.divider()
        st.subheader("操作")

        # 操作按钮
        provider_actions = [
            {
                "label": "查看详情",
                "key": "btn_view_provider",
                "on_click": view_provider_details,
            }
        ]

        action_bar(provider_actions)


def show_provider_details():
    """显示工具提供者详情"""
    if not st.session_state.current_tool_provider:
        st.error("未选择工具提供者")
        if st.button("返回", key="btn_back_noselect"):
            back_to_list()
        return

    provider = st.session_state.current_tool_provider

    page_header(f"工具提供者: {provider['name']}", f"查看工具提供者的详细信息")

    # 返回按钮
    actions = [
        {"label": "返回列表", "key": "btn_back_details", "on_click": back_to_list}
    ]
    action_bar(actions)

    # 提供者基本信息
    st.subheader("基本信息")
    tabs = st.tabs(["Provider信息", "工具信息"])
    with tabs[0]:
        st.json(provider)
    with tabs[1]:
        if provider["type"] == "workflow":
            tool_info = DifyClient.get_connection().fetch_workflow_tool(
                workflow_tool_id=provider["id"]
            )
            st.json(tool_info)
        else:
            st.error("不支持的工具提供者类型")

    # 显示工具列表
    tools = provider.get("tools", [])
    if tools:
        st.subheader(f"提供的工具 ({len(tools)})")

        # 定义表格列配置
        tool_columns = [
            {"field": "name", "title": "工具名称"},
            {"field": "description", "title": "描述"},
        ]

        # 显示工具表格
        data_display(tools, tool_columns, key="tool_list_table")


def show_workflow_apps():
    """显示工作流应用列表"""
    page_header("工作流工具管理", "管理可作为工具的工作流应用")

    # 返回按钮和刷新按钮
    actions = [
        {"label": "返回工具列表", "key": "btn_back_workflow", "on_click": back_to_list},
        {
            "label": "刷新列表",
            "key": "btn_refresh_workflow",
            "on_click": lambda: reset_cache("workflow_app") or st.rerun(),
        },
    ]
    action_bar(actions)

    # 获取工作流应用列表
    workflow_apps = get_workflow_apps()

    # 定义表格列配置
    columns = [
        {"field": "name", "title": "应用名称"},
        {"field": "description", "title": "描述"},
        {"field": "published_tool", "title": "已发布为工具"},
    ]

    # 处理已发布状态
    for app in workflow_apps:
        app["published_tool"] = "是" if app.get("published_as_tool", False) else "否"

    # 显示数据表格
    selected_df = data_display(workflow_apps, columns, key="workflow_app_table")

    # 保存选中的行
    st.session_state.selected_workflow_app = selected_df

    # 如果选中了行，显示操作区域
    if not selected_df.empty:
        st.divider()
        st.subheader("操作")

        app_id = selected_df.iloc[0]["id"]
        app = next((a for a in workflow_apps if a["id"] == app_id), None)

        if app:
            # 根据应用是否已发布为工具提供不同的操作
            if app.get("published_as_tool", False):
                app_actions = [
                    {
                        "label": "查看工具详情",
                        "key": "btn_view_tool",
                        "on_click": view_workflow_tool,
                    },
                    {
                        "label": "编辑工具",
                        "key": "btn_edit_tool",
                        "on_click": edit_workflow_tool,
                    },
                ]
            else:
                app_actions = [
                    {
                        "label": "发布为工具",
                        "key": "btn_publish_tool",
                        "on_click": lambda: publish_workflow_app(app_id),
                    }
                ]

            action_bar(app_actions)


def publish_workflow_app(app_id):
    """发布工作流应用为工具"""
    try:
        client = DifyClient.get_connection()
        with loading_spinner("正在发布工作流工具..."):
            client.publish_workflow_tool(app_id)

        # 重置缓存
        reset_cache("workflow_app")

        # 显示成功消息
        success_message("工作流已成功发布为工具！")

        # 延迟1秒
        time.sleep(1)

        # 查看工具详情
        st.session_state.tool_view_mode = "workflow_tool"
        st.session_state.current_workflow_app_id = app_id
        st.rerun()
    except Exception as e:
        st.error(f"发布工作流工具失败: {str(e)}")


def show_workflow_tool_details():
    """显示工作流工具详情"""
    if not st.session_state.current_workflow_app_id:
        st.error("未选择工作流应用")
        if st.button("返回", key="btn_back_noworkflow"):
            back_to_workflow_apps()
        return

    # 获取工作流工具详情
    tool_data = get_workflow_tool(st.session_state.current_workflow_app_id)
    if not tool_data:
        st.error("获取工作流工具详情失败")
        if st.button("返回", key="btn_back_nofetch"):
            back_to_workflow_apps()
        return

    # 获取应用信息
    app = next(
        (
            a
            for a in get_workflow_apps()
            if a["id"] == st.session_state.current_workflow_app_id
        ),
        None,
    )
    if not app:
        st.error("获取应用信息失败")
        if st.button("返回", key="btn_back_noapp"):
            back_to_workflow_apps()
        return

    page_header(f"工作流工具: {app['name']}", "查看工作流工具的详细配置")

    # 操作按钮
    actions = [
        {
            "label": "返回列表",
            "key": "btn_back_tool",
            "on_click": back_to_workflow_apps,
        },
        {
            "label": "编辑工具",
            "key": "btn_edit_from_view",
            "on_click": edit_workflow_tool,
        },
    ]
    action_bar(actions)

    # 工具基本信息
    st.subheader("基本信息")
    st.json(tool_data)
    # 显示参数
    params = tool_data.get("parameters", [])
    if params:
        st.subheader(f"参数配置 ({len(params)})")

        # 定义表格列配置
        param_columns = [
            {"field": "name", "title": "参数名称"},
            {"field": "description", "title": "描述"},
            {"field": "type", "title": "类型"},
            {"field": "required", "title": "是否必须"},
        ]

        # 处理参数数据
        for param in params:
            param["required"] = "是" if param.get("required", False) else "否"

        # 显示参数表格
        data_display(params, param_columns, key="param_table")

    # 显示工具输出
    outputs = tool_data.get("outputs", {})
    if outputs:
        st.subheader("输出配置")
        st.json(outputs)


def show_edit_workflow_tool():
    """显示编辑工作流工具表单"""
    if not st.session_state.current_workflow_app_id:
        st.error("未选择工作流应用")
        if st.button("返回", key="btn_back_noedit"):
            back_to_workflow_apps()
        return

    # 获取工作流工具详情
    tool_data = get_workflow_tool(st.session_state.current_workflow_app_id)
    if not tool_data:
        st.error("获取工作流工具详情失败")
        if st.button("返回", key="btn_back_nofetch_edit"):
            back_to_workflow_apps()
        return

    # 获取应用信息
    app = next(
        (
            a
            for a in get_workflow_apps()
            if a["id"] == st.session_state.current_workflow_app_id
        ),
        None,
    )
    if not app:
        st.error("获取应用信息失败")
        if st.button("返回", key="btn_back_noapp_edit"):
            back_to_workflow_apps()
        return

    page_header(f"编辑工作流工具: {app['name']}", "修改工作流工具的配置信息")

    # 返回按钮
    if st.button("返回工具详情", key="btn_back_edit"):
        view_workflow_tool()
        return

    # 编辑表单
    with st.form("编辑工作流工具"):
        # 基本信息
        st.subheader("基本信息")
        name = st.text_input("工具名称", value=tool_data.get("name", ""))
        description = st.text_area("工具描述", value=tool_data.get("description", ""))
        qualified_name = st.text_input(
            "工具标识", value=tool_data.get("qualified_name", "")
        )

        # 参数配置
        st.subheader("参数配置")
        st.info("参数配置由工作流定义，在此只能调整参数描述")

        params = tool_data.get("parameters", [])
        param_descriptions = {}

        for i, param in enumerate(params):
            param_name = param.get("name", f"参数{i+1}")
            param_descriptions[param_name] = st.text_input(
                f"参数 {param_name} 描述",
                value=param.get("description", ""),
                key=f"param_desc_{i}",
            )

        # 提交按钮
        submitted = st.form_submit_button("保存")

        if submitted:
            # 更新参数描述
            for i, param in enumerate(params):
                param_name = param.get("name", f"参数{i+1}")
                param["description"] = param_descriptions[param_name]

            # 准备更新数据
            update_data = {
                "name": name,
                "description": description,
                "qualified_name": qualified_name,
                "parameters": params,
                # 保留原有的其他数据
                "outputs": tool_data.get("outputs", {}),
            }

            try:
                client = DifyClient.get_connection()
                with loading_spinner("正在更新工作流工具..."):
                    client.update_workflow_tool(
                        st.session_state.current_workflow_app_id, update_data
                    )

                # 重置缓存
                reset_cache("workflow_tool")

                # 显示成功消息
                success_message("工作流工具更新成功！")

                # 延迟1秒
                time.sleep(1)

                # 返回工具详情
                view_workflow_tool()
            except Exception as e:
                st.error(f"更新工作流工具失败: {str(e)}")


def main():
    """主函数"""
    site_sidebar()

    # 根据当前视图模式显示不同的内容
    if st.session_state.tool_view_mode == "list":
        show_tool_provider_list()
    elif st.session_state.tool_view_mode == "details":
        show_provider_details()
    elif st.session_state.tool_view_mode == "workflow_apps":
        show_workflow_apps()
    elif st.session_state.tool_view_mode == "workflow_tool":
        show_workflow_tool_details()
    elif st.session_state.tool_view_mode == "edit_workflow_tool":
        show_edit_workflow_tool()
    else:
        st.error("未知的视图模式")
        back_to_list()


if __name__ == "__main__":
    main()

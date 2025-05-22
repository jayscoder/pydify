"""
Dify管理面板 - 应用管理页面

提供应用的创建、查看、编辑、删除和DSL管理功能
"""

import os
import sys
import time
from pathlib import Path

import pandas as pd
import streamlit as st

# 添加项目根目录到Python路径
root_dir = Path(__file__).parent.parent
sys.path.append(str(root_dir))

# 导入工具类
from utils.dify_client import DifyAppMode, DifyClient
from utils.ui_components import (
    action_bar,
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
    page_title="应用管理 - Dify管理面板",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 初始化会话状态
if "app_view_mode" not in st.session_state:
    st.session_state.app_view_mode = (
        "list"  # 可选值: list, create, view, edit, delete, dsl_export, dsl_import
    )
if "current_app_id" not in st.session_state:
    st.session_state.current_app_id = None
if "apps_cache" not in st.session_state:
    st.session_state.apps_cache = None
if "app_details_cache" not in st.session_state:
    st.session_state.app_details_cache = None
if "selected_app" not in st.session_state:
    st.session_state.selected_app = None


def get_apps():
    """获取应用列表，带缓存机制"""
    # 如果未连接，返回空列表
    if not DifyClient.is_connected():
        return []

    client = DifyClient.get_connection()
    try:
        # 使用缓存
        if st.session_state.apps_cache is None:
            with loading_spinner("正在加载应用列表..."):
                st.session_state.apps_cache = client.fetch_all_apps()
        return st.session_state.apps_cache
    except Exception as e:
        st.error(f"获取应用列表失败: {str(e)}")
        return []


def get_app_details(app_id):
    """获取应用详情，带缓存机制"""
    if not app_id or not DifyClient.is_connected():
        return None

    client = DifyClient.get_connection()

    # 检查缓存
    if (
        st.session_state.app_details_cache is not None
        and "id" in st.session_state.app_details_cache
        and st.session_state.app_details_cache["id"] == app_id
    ):
        return st.session_state.app_details_cache

    try:
        with loading_spinner("正在加载应用详情..."):
            app_details = client.fetch_app(app_id)
            st.session_state.app_details_cache = app_details
            return app_details
    except Exception as e:
        st.error(f"获取应用详情失败: {str(e)}")
        return None


def reset_cache():
    """重置应用数据缓存"""
    st.session_state.apps_cache = None
    st.session_state.app_details_cache = None


def view_app():
    """查看应用详情"""
    if (
        st.session_state.selected_app is not None
        and not st.session_state.selected_app.empty
    ):
        app_id = st.session_state.selected_app.iloc[0]["_id"]
        st.session_state.app_view_mode = "view"
        st.session_state.current_app_id = app_id
        st.rerun()


def edit_app():
    """编辑应用"""
    if (
        st.session_state.selected_app is not None
        and not st.session_state.selected_app.empty
    ):
        app_id = st.session_state.selected_app.iloc[0]["_id"]
        st.session_state.app_view_mode = "edit"
        st.session_state.current_app_id = app_id
        st.rerun()


def delete_app():
    """删除应用"""
    if (
        st.session_state.selected_app is not None
        and not st.session_state.selected_app.empty
    ):
        app_id = st.session_state.selected_app.iloc[0]["_id"]
        st.session_state.app_view_mode = "delete"
        st.session_state.current_app_id = app_id
        st.rerun()


def create_app():
    """创建新应用"""
    st.session_state.app_view_mode = "create"
    st.rerun()


def back_to_list():
    """返回应用列表"""
    st.session_state.app_view_mode = "list"
    st.session_state.current_app_id = None
    st.session_state.selected_app = None
    st.rerun()


def export_dsl():
    """导出应用DSL"""
    if (
        st.session_state.selected_app is not None
        and not st.session_state.selected_app.empty
    ):
        app_id = st.session_state.selected_app.iloc[0]["_id"]
        st.session_state.app_view_mode = "dsl_export"
        st.session_state.current_app_id = app_id
        st.rerun()


def import_dsl():
    """导入应用DSL"""
    st.session_state.app_view_mode = "dsl_import"
    st.rerun()


def manage_api_keys():
    """管理API密钥"""
    if (
        st.session_state.selected_app is not None
        and not st.session_state.selected_app.empty
    ):
        app_id = st.session_state.selected_app.iloc[0]["_id"]
        st.session_state.current_app_id = app_id
        st.switch_page("pages/api_key_management.py")


def manage_tags():
    """管理标签"""
    if (
        st.session_state.selected_app is not None
        and not st.session_state.selected_app.empty
    ):
        app_id = st.session_state.selected_app.iloc[0]["_id"]
        st.session_state.current_app_id = app_id
        st.switch_page("pages/tag_management.py")


def show_app_list():
    """显示应用列表"""
    page_header("应用管理", "管理您在Dify平台上的所有应用")

    # 获取应用列表
    apps = get_apps()

    # 添加操作按钮
    actions = [
        {"label": "创建新应用", "key": "btn_create_app", "on_click": create_app},
        {"label": "导入应用DSL", "key": "btn_import_dsl", "on_click": import_dsl},
        {
            "label": "刷新列表",
            "key": "btn_refresh_apps",
            "on_click": lambda: reset_cache() or st.rerun(),
        },
    ]
    action_bar(actions)

    # 定义表格列配置
    columns = [
        {"field": "name", "title": "应用名称"},
        {"field": "mode", "title": "应用类型"},
        {"field": "description", "title": "描述"},
        {"field": "created_at", "title": "创建时间"},
    ]

    # 处理时间戳
    for app in apps:
        if "created_at" in app:
            from utils.ui_components import format_timestamp

            app["created_at"] = format_timestamp(app["created_at"])

    # 显示数据表格
    selected_df = data_display(apps, columns, key="app_table")

    # 保存选中的行
    st.session_state.selected_app = selected_df

    # 如果选中了行，显示操作区域
    if not selected_df.empty:
        st.divider()
        st.subheader("操作")

        # 操作按钮
        app_actions = [
            {"label": "查看详情", "key": "btn_view_selected", "on_click": view_app},
            {"label": "编辑应用", "key": "btn_edit_selected", "on_click": edit_app},
            {
                "label": "API密钥",
                "key": "btn_api_keys_selected",
                "on_click": manage_api_keys,
            },
            {"label": "标签管理", "key": "btn_tags_selected", "on_click": manage_tags},
            {
                "label": "导出DSL",
                "key": "btn_export_dsl_selected",
                "on_click": export_dsl,
            },
            {
                "label": "删除应用",
                "key": "btn_delete_selected",
                "color": "danger",
                "on_click": delete_app,
            },
        ]

        action_bar(app_actions)


def show_app_details():
    """显示应用详情"""
    if not st.session_state.current_app_id:
        st.error("未选择应用")
        if st.button("返回", key="btn_back_noapp"):
            back_to_list()
        return

    app_details = get_app_details(st.session_state.current_app_id)
    if not app_details:
        st.error("获取应用详情失败")
        if st.button("返回", key="btn_back_fail"):
            back_to_list()
        return

    # 显示应用详情
    page_header(f"应用详情: {app_details['name']}", f"查看应用的详细信息")

    # 操作按钮行
    back_actions = [
        {"label": "返回列表", "key": "btn_back_detail", "on_click": back_to_list}
    ]
    action_bar(back_actions)

    # 应用基本信息
    st.subheader("基本信息")
    col1, col2 = st.columns(2)
    with col1:
        st.write(f"**应用ID**: {app_details['id']}")
        st.write(f"**应用名称**: {app_details['name']}")
        st.write(f"**应用类型**: {app_details['mode']}")
        st.write(f"**创建者**: {app_details.get('created_by', '未知')}")
    with col2:
        from utils.ui_components import format_timestamp

        st.write(f"**创建时间**: {format_timestamp(app_details.get('created_at', 0))}")
        st.write(f"**更新时间**: {format_timestamp(app_details.get('updated_at', 0))}")

        # 显示标签
        tags = app_details.get("tags", [])
        if tags:
            tag_str = ", ".join([tag.get("name", "") for tag in tags])
            st.write(f"**标签**: {tag_str}")

    # 应用描述
    st.subheader("描述")
    st.write(app_details.get("description", "无描述"))

    # 操作按钮
    st.divider()
    detail_actions = [
        {
            "label": "编辑应用",
            "key": "btn_edit_from_detail",
            "on_click": lambda: edit_app(),
        },
        {
            "label": "导出DSL",
            "key": "btn_export_dsl_from_detail",
            "on_click": lambda: export_dsl(),
        },
        {
            "label": "删除应用",
            "key": "btn_delete_from_detail",
            "color": "danger",
            "on_click": lambda: delete_app(),
        },
    ]
    action_bar(detail_actions)


def show_create_app():
    """显示创建应用表单"""
    page_header("创建新应用", "创建一个新的Dify应用")

    # 返回按钮
    if st.button("返回列表", key="btn_back_create"):
        back_to_list()

    # 创建应用表单
    with st.form("创建应用"):
        name = st.text_input("应用名称", placeholder="给应用起个名字")
        description = st.text_area("应用描述", placeholder="描述应用的功能和用途")

        # 应用类型选择
        mode_options = {
            DifyAppMode.CHAT: "聊天助手 (Chat)",
            DifyAppMode.AGENT_CHAT: "代理模式 (Agent Chat)",
            DifyAppMode.COMPLETION: "文本生成 (Completion)",
            DifyAppMode.ADVANCED_CHAT: "高级聊天流 (Advanced Chat)",
            DifyAppMode.WORKFLOW: "工作流 (Workflow)",
        }
        mode = st.selectbox(
            "应用类型",
            options=list(mode_options.keys()),
            format_func=lambda x: mode_options[x],
        )

        submitted = st.form_submit_button("创建")

        if submitted:
            if not name:
                st.error("应用名称不能为空")
                return

            # 创建应用
            try:
                client = DifyClient.get_connection()
                with loading_spinner("正在创建应用..."):
                    new_app = client.create_app(name, description, mode)

                # 重置缓存
                reset_cache()

                # 显示成功消息
                success_message("应用创建成功！")

                # 延迟1秒，确保用户看到成功消息
                time.sleep(1)

                # 跳转回列表
                back_to_list()
            except Exception as e:
                st.error(f"创建应用失败: {str(e)}")


def show_edit_app():
    """显示编辑应用表单"""
    if not st.session_state.current_app_id:
        st.error("未选择应用")
        if st.button("返回", key="btn_back_noedit"):
            back_to_list()
        return

    app_details = get_app_details(st.session_state.current_app_id)
    if not app_details:
        st.error("获取应用详情失败")
        if st.button("返回", key="btn_back_edit_fail"):
            back_to_list()
        return

    page_header(f"编辑应用: {app_details['name']}", "修改应用的名称和描述")

    # 返回按钮
    if st.button("返回应用详情", key="btn_back_edit"):
        view_app()
        return

    # 编辑应用表单
    with st.form("编辑应用"):
        name = st.text_input("应用名称", value=app_details["name"])
        description = st.text_area("应用描述", value=app_details.get("description", ""))

        submitted = st.form_submit_button("更新")

        if submitted:
            if not name:
                st.error("应用名称不能为空")
                return

            # 更新应用
            try:
                client = DifyClient.get_connection()
                with loading_spinner("正在更新应用..."):
                    updated_app = client.update_app(
                        st.session_state.current_app_id, name, description
                    )

                # 重置缓存
                reset_cache()

                # 显示成功消息
                success_message("应用更新成功！")

                # 延迟1秒，确保用户看到成功消息
                time.sleep(1)

                # 查看更新后的应用详情
                view_app()
            except Exception as e:
                st.error(f"更新应用失败: {str(e)}")


def show_delete_app():
    """显示删除应用确认对话框"""
    if not st.session_state.current_app_id:
        st.error("未选择应用")
        if st.button("返回", key="btn_back_nodelete"):
            back_to_list()
        return

    app_details = get_app_details(st.session_state.current_app_id)
    if not app_details:
        st.error("获取应用详情失败")
        if st.button("返回", key="btn_back_delete_fail"):
            back_to_list()
        return

    # 显示确认对话框
    confirmation_dialog(
        title=f"确认删除应用 '{app_details['name']}'",
        message="此操作不可逆，删除后应用将无法恢复。是否确认删除？",
        on_confirm=lambda: perform_delete(st.session_state.current_app_id),
        on_cancel=back_to_list,
    )


def perform_delete(app_id):
    """执行删除应用操作"""
    try:
        client = DifyClient.get_connection()
        with loading_spinner("正在删除应用..."):
            client.delete_app(app_id)

        # 重置缓存
        reset_cache()

        # 显示成功消息
        success_message("应用删除成功！")

        # 延迟1秒，确保用户看到成功消息
        time.sleep(1)

        # 返回应用列表
        back_to_list()
    except Exception as e:
        st.error(f"删除应用失败: {str(e)}")


def show_dsl_export():
    """显示导出DSL界面"""
    if not st.session_state.current_app_id:
        st.error("未选择应用")
        if st.button("返回", key="btn_back_nodsl"):
            back_to_list()
        return

    app_details = get_app_details(st.session_state.current_app_id)
    if not app_details:
        st.error("获取应用详情失败")
        if st.button("返回", key="btn_back_dsl_fail"):
            back_to_list()
        return

    page_header(f"导出应用DSL: {app_details['name']}", "导出应用的DSL配置")

    # 返回按钮
    if st.button("返回应用详情", key="btn_back_dsl"):
        view_app()
        return

    # 导出应用DSL
    try:
        client = DifyClient.get_connection()
        with loading_spinner("正在导出DSL..."):
            dsl_content = client.fetch_app_dsl(st.session_state.current_app_id)

        # 显示DSL内容
        st.subheader("DSL内容")
        st.code(dsl_content, language="yaml")

        # 下载按钮
        st.download_button(
            label="下载DSL文件",
            data=dsl_content,
            file_name=f"{app_details['name']}_dsl.yaml",
            mime="text/yaml",
        )
    except Exception as e:
        st.error(f"导出DSL失败: {str(e)}")


def show_dsl_import():
    """显示导入DSL界面"""
    page_header("导入应用DSL", "从DSL配置导入应用")

    # 返回按钮
    if st.button("返回列表", key="btn_back_import"):
        back_to_list()

    # 导入应用DSL表单
    st.info("您可以上传DSL文件或直接粘贴DSL内容来导入应用")

    # 上传DSL文件
    uploaded_file = st.file_uploader("上传DSL文件", type=["yaml", "yml"])

    # 或直接粘贴DSL内容
    dsl_content = st.text_area("或直接粘贴DSL内容", height=300)

    # 导入为新应用或更新现有应用
    st.subheader("导入选项")
    import_options = ["创建新应用", "更新现有应用"]
    import_option = st.radio("导入方式", options=import_options)

    # 如果选择更新现有应用，提供应用选择器
    app_id_to_update = None
    if import_option == "更新现有应用":
        apps = get_apps()
        app_options = {app["name"]: app["id"] for app in apps}
        selected_app_name = st.selectbox(
            "选择要更新的应用", options=list(app_options.keys())
        )
        if selected_app_name:
            app_id_to_update = app_options[selected_app_name]

    # 导入按钮
    if st.button("导入", key="btn_confirm_import"):
        # 获取DSL内容
        import_dsl_content = None
        if uploaded_file is not None:
            import_dsl_content = uploaded_file.getvalue().decode("utf-8")
        elif dsl_content.strip():
            import_dsl_content = dsl_content
        else:
            st.error("请上传DSL文件或输入DSL内容")
            return

        try:
            client = DifyClient.get_connection()
            with loading_spinner("正在导入DSL..."):
                if import_option == "更新现有应用" and app_id_to_update:
                    result = client.import_app_dsl(import_dsl_content, app_id_to_update)
                else:
                    result = client.import_app_dsl(import_dsl_content)

            # 重置缓存
            reset_cache()

            # 显示成功消息
            success_message("DSL导入成功！")

            # 延迟1秒，确保用户看到成功消息
            time.sleep(1)

            # 返回应用列表
            back_to_list()
        except Exception as e:
            st.error(f"导入DSL失败: {str(e)}")


def main():
    """主函数"""
    # 检查连接状态
    if not DifyClient.is_connected():
        st.warning("未连接到Dify平台")
        st.info("请先在主页连接到Dify平台")

        # 返回主页按钮
        if st.button("返回主页"):
            st.switch_page("app.py")
        return

    # 根据当前视图模式显示不同的内容
    if st.session_state.app_view_mode == "list":
        show_app_list()
    elif st.session_state.app_view_mode == "view":
        show_app_details()
    elif st.session_state.app_view_mode == "create":
        show_create_app()
    elif st.session_state.app_view_mode == "edit":
        show_edit_app()
    elif st.session_state.app_view_mode == "delete":
        show_delete_app()
    elif st.session_state.app_view_mode == "dsl_export":
        show_dsl_export()
    elif st.session_state.app_view_mode == "dsl_import":
        show_dsl_import()
    else:
        st.error("未知的视图模式")
        back_to_list()


if __name__ == "__main__":
    main()

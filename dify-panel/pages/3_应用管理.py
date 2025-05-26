"""
Dify管理面板 - 应用管理页面

提供应用的创建、查看、编辑、删除和DSL管理功能
"""
import streamlit as st
import os
import sys
import time
import io
import zipfile
import re
import json
import yaml
from pathlib import Path

import pandas as pd

# 添加项目根目录到Python路径
root_dir = Path(__file__).parent.parent
sys.path.append(str(root_dir))

# 导入工具和组件
from config import Pages
from utils.dify_client import DifyAppMode, DifyClient
from utils.ui_components import (
    page_header, 
    action_bar, 
    data_display, 
    loading_spinner,
    json_viewer,
    confirmation_dialog,
    format_timestamp,
    site_sidebar,
    set_sesstion_state
)

from utils.app_components import app_details, edit_app, delete_app, export_dsl
from utils.dsl_components import dsl_graph

# 设置页面配置
st.set_page_config(
    page_title="应用管理 - Dify管理面板",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 初始化会话状态
if "apps_cache" not in st.session_state:
    st.session_state.apps_cache = None
if "app_details_cache" not in st.session_state:
    st.session_state.app_details_cache = None
if "selected_app" not in st.session_state:
    st.session_state.selected_app = None
if "multi_select_mode" not in st.session_state:
    st.session_state.multi_select_mode = False
if "filter_mode" not in st.session_state:
    st.session_state.filter_mode = "all"
if "filter_tag" not in st.session_state:
    st.session_state.filter_tag = None
if "show_app_details" not in st.session_state:
    st.session_state.show_app_details = False
if "show_create_app_dialog" not in st.session_state:
    st.session_state.show_create_app_dialog = False
if "show_import_dsl_dialog" not in st.session_state:
    st.session_state.show_import_dsl_dialog = False
if "show_batch_export_dialog" not in st.session_state:
    st.session_state.show_batch_export_dialog = False
if "show_batch_rename_dialog" not in st.session_state:
    st.session_state.show_batch_rename_dialog = False
if "show_batch_delete_dialog" not in st.session_state:
    st.session_state.show_batch_delete_dialog = False


def reset_cache():
    """重置应用数据缓存"""
    st.session_state.apps_cache = None
    st.session_state.app_details_cache = None


def reset_dialogs():
    """重置所有对话框状态"""
    st.session_state.show_create_app_dialog = False
    st.session_state.show_import_dsl_dialog = False
    st.session_state.show_batch_export_dialog = False
    st.session_state.show_batch_rename_dialog = False
    st.session_state.show_batch_delete_dialog = False
    st.session_state.show_app_details = False


def get_apps():
    """
    获取应用列表，带缓存机制
    
    返回:
        list: 应用列表
    """
    # 如果未连接，返回空列表
    if not DifyClient.is_connected():
        return []

    client = DifyClient.get_connection()
    try:
        # 使用缓存
        if st.session_state.apps_cache is None:
            with loading_spinner("正在加载应用列表..."):
                st.session_state.apps_cache = client.fetch_all_apps()
        
        # 根据过滤条件筛选应用
        filtered_apps = []
        for app in st.session_state.apps_cache:
            # 根据应用类型过滤
            if st.session_state.filter_mode != "all" and app["mode"] != st.session_state.filter_mode:
                continue
            
            # 根据标签过滤
            if st.session_state.filter_tag is not None:
                tags = app.get("tags", [])
                tag_ids = [tag["id"] for tag in tags]
                if st.session_state.filter_tag not in tag_ids:
                    continue
            
            filtered_apps.append(app)
        
        return filtered_apps
    except Exception as e:
        st.error(f"获取应用列表失败: {str(e)}")
        return []


def get_app_details(app_id):
    """
    获取应用详情，带缓存机制
    
    参数:
        app_id: 应用ID
        
    返回:
        dict: 应用详情
    """
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


@st.dialog("创建新应用")
def create_app_dialog():
    """显示创建应用的对话框"""
    # 创建应用表单
    with st.form("创建应用表单"):
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

                
        submit_button = st.form_submit_button("创建", type="primary")
        
        if submit_button:
            if not name:
                st.error("应用名称不能为空")
            else:
                # 创建应用
                try:
                    client = DifyClient.get_connection()
                    with st.spinner("正在创建应用..."):
                        new_app = client.create_app(name, description, mode)

                    # 重置缓存
                    reset_cache()

                    # 显示成功消息
                    st.success("应用创建成功！")
                    
                    # 关闭对话框
                    st.session_state.show_create_app_dialog = False
                except Exception as e:
                    st.error(f"创建应用失败: {str(e)}")


@st.dialog("导入应用DSL")
def import_dsl_dialog():
    """显示导入DSL的对话框"""
    st.info("您可以上传DSL文件或直接粘贴DSL内容来导入应用")

    # 上传DSL文件
    uploaded_file = st.file_uploader("上传DSL文件", type=["yaml", "yml", "json"])

    # 或直接粘贴DSL内容
    dsl_content = st.text_area("或直接粘贴DSL内容", height=300)

    # 导入为新应用或更新现有应用
    st.subheader("导入选项")
    import_options = ["创建新应用", "更新现有应用"]
    import_option = st.radio("导入方式", options=import_options, horizontal=True)

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

    # 操作按钮
    col1, col2 = st.columns(2)
    with col1:
        if st.button("取消", key="cancel_import", use_container_width=True):
            st.session_state.show_import_dsl_dialog = False
    
    with col2:
        if st.button("导入", key="confirm_import", type="primary", use_container_width=True):
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
                with st.spinner("正在导入DSL..."):
                    if import_option == "更新现有应用" and app_id_to_update:
                        result = client.import_app_dsl(import_dsl_content, app_id_to_update)
                    else:
                        result = client.import_app_dsl(import_dsl_content)

                # 重置缓存
                reset_cache()

                # 显示成功消息
                st.success("DSL导入成功！")
                
                # 关闭对话框
                st.session_state.show_import_dsl_dialog = False
            except Exception as e:
                st.error(f"导入DSL失败: {str(e)}")


@st.dialog("批量导出DSL")
def batch_export_dsl_dialog():
    """显示批量导出DSL对话框"""
    if st.session_state.selected_app is None or len(st.session_state.selected_app) < 1:
        st.error("未选择应用")
        st.session_state.show_batch_export_dialog = False
        return
    
    app_ids = st.session_state.selected_app["id"].tolist()
    app_names = st.session_state.selected_app["应用名称"].tolist()
    
    st.subheader("批量导出DSL")
    st.info(f"您选择了 {len(app_ids)} 个应用进行DSL导出")
    
    # 创建导出按钮
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("导出为ZIP格式", key="btn_confirm_export_zip", use_container_width=True):
            try:
                client = DifyClient.get_connection()
                progress_bar = st.progress(0)
                
                # 创建内存中的ZIP文件
                zip_buffer = io.BytesIO()
                with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    with st.spinner("正在导出DSL..."):
                        for i, (app_id, app_name) in enumerate(zip(app_ids, app_names)):
                            try:
                                # 获取DSL内容
                                dsl_content = client.fetch_app_dsl(app_id)
                                
                                # 确保文件名是合法的
                                safe_name = re.sub(r'[^\w\-\.]', '_', app_name)
                                
                                # 添加到ZIP文件
                                zipf.writestr(f"{safe_name}.yaml", dsl_content)
                                
                                # 更新进度条
                                progress_bar.progress((i + 1) / len(app_ids))
                            except Exception as e:
                                # 如果某个应用导出失败，添加错误信息文件
                                error_info = f"导出失败: {str(e)}"
                                zipf.writestr(f"{safe_name}_error.txt", error_info)
                
                # 准备下载
                zip_buffer.seek(0)
                timestamp = time.strftime("%Y%m%d%H%M%S")
                
                # 下载按钮
                st.success(f"已成功准备 {len(app_ids)} 个应用的DSL文件")
                st.download_button(
                    label="下载ZIP文件",
                    data=zip_buffer.getvalue(),
                    file_name=f"dify_apps_dsl_{timestamp}.zip",
                    mime="application/zip",
                )
            except Exception as e:
                st.error(f"批量导出DSL失败: {str(e)}")
    
    with col2:
        if st.button("导出为JSON格式", key="btn_confirm_export_json", use_container_width=True):
            try:
                client = DifyClient.get_connection()
                progress_bar = st.progress(0)
                
                # 将所有的dsl内容写入一个json
                dsl_data = {}
                
                with st.spinner("正在导出DSL..."):
                    for i, (app_id, app_name) in enumerate(zip(app_ids, app_names)):
                        try:
                            # 获取DSL内容
                            dsl_content = client.fetch_app_dsl(app_id)
                            
                            # 确保键名是合法的
                            safe_name = re.sub(r'[^\w\-\.]', '_', app_name)
                            
                            # 添加到字典
                            dsl_data[safe_name] = dsl_content
                            
                            # 更新进度条
                            progress_bar.progress((i + 1) / len(app_ids))
                        except Exception as e:
                            # 如果某个应用导出失败，记录错误信息
                            dsl_data[f"{safe_name}_error"] = f"导出失败: {str(e)}"
                
                # 时间戳
                timestamp = time.strftime("%Y%m%d%H%M%S")
                
                # 下载按钮
                st.success(f"已成功准备 {len(app_ids)} 个应用的DSL文件")
                st.download_button(
                    label="下载JSON文件",
                    data=json.dumps(dsl_data, indent=2, ensure_ascii=False),
                    file_name=f"dify_apps_dsl_{timestamp}.json",
                    mime="application/json",
                )
            except Exception as e:
                st.error(f"批量导出DSL失败: {str(e)}")
    
    # 返回按钮
    if st.button("返回", key="btn_back_batch_export"):
        st.session_state.show_batch_export_dialog = False


@st.dialog("批量重命名应用")
def batch_rename_dialog():
    """显示批量重命名对话框"""
    if st.session_state.selected_app is None or len(st.session_state.selected_app) < 1:
        st.error("未选择应用")
        st.session_state.show_batch_rename_dialog = False
        return
    
    app_ids = st.session_state.selected_app["id"].tolist()
    app_names = st.session_state.selected_app["应用名称"].tolist()
    
    st.subheader(f"批量重命名 ({len(app_ids)} 个应用)")
    
    # 显示当前选中的应用
    with st.expander("已选择的应用", expanded=False):
        for i, name in enumerate(app_names):
            st.text(f"{i+1}. {name}")
    
    # 批量修改选项
    st.subheader("修改选项")
    edit_mode = st.radio(
        "修改模式", 
        ["添加前缀", "添加后缀", "查找替换", "重命名模式"],
        horizontal=True
    )
    
    # 根据不同模式显示不同输入框
    if edit_mode == "添加前缀":
        prefix = st.text_input("前缀", placeholder="输入要添加的前缀")
        preview = [f"{prefix}{name}" for name in app_names]
    elif edit_mode == "添加后缀":
        suffix = st.text_input("后缀", placeholder="输入要添加的后缀")
        preview = [f"{name}{suffix}" for name in app_names]
    elif edit_mode == "查找替换":
        find_text = st.text_input("查找文本", placeholder="输入要查找的文本")
        replace_text = st.text_input("替换为", placeholder="输入要替换的文本")
        preview = [name.replace(find_text, replace_text) if find_text else name for name in app_names]
    elif edit_mode == "重命名模式":
        pattern = st.text_input(
            "重命名模式", 
            placeholder="例如: 应用{index} 或 {name}_新版本",
            help="使用 {index} 表示序号，{name} 表示原名称"
        )
        preview = []
        for i, name in enumerate(app_names):
            if pattern:
                new_name = pattern.replace("{index}", str(i+1)).replace("{name}", name)
                preview.append(new_name)
            else:
                preview.append(name)
    
    # 预览新名称
    if any(preview):
        st.subheader("名称预览")
        
        # 创建预览数据
        preview_data = []
        for i, (old_name, new_name) in enumerate(zip(app_names, preview)):
            preview_data.append({
                "序号": i + 1,
                "原名称": old_name,
                "新名称": new_name,
                "是否变更": "是" if old_name != new_name else "否"
            })
        
        # 显示预览表格
        st.dataframe(preview_data, use_container_width=True)
    
    # 按钮区域
    col1, col2 = st.columns(2)
    with col1:
        if st.button("取消", key="btn_cancel_batch_rename", use_container_width=True):
            st.session_state.show_batch_rename_dialog = False
    
    with col2:
        if st.button("应用修改", key="btn_apply_batch_rename", type="primary", use_container_width=True):
            if not any(a != b for a, b in zip(app_names, preview)):
                st.warning("未检测到名称变更，请先设置修改选项")
            else:
                client = DifyClient.get_connection()
                progress_bar = st.progress(0)
                success_count = 0
                error_messages = []
                
                with st.spinner("正在批量修改应用名称..."):
                    for i, (app_id, old_name, new_name) in enumerate(zip(app_ids, app_names, preview)):
                        try:
                            # 获取应用当前详情以保留描述
                            app_details = client.fetch_app(app_id)
                            description = app_details.get("description", "")
                            
                            # 如果名称有变化才更新
                            if old_name != new_name:
                                client.update_app(app_id, new_name, description)
                                success_count += 1
                            
                            # 更新进度条
                            progress_bar.progress((i + 1) / len(app_ids))
                        except Exception as e:
                            error_messages.append(f"应用 '{old_name}' 更新失败: {str(e)}")
                
                # 显示结果
                if success_count > 0:
                    st.success(f"成功修改 {success_count} 个应用的名称")
                
                if error_messages:
                    st.error("部分应用更新失败")
                    for error in error_messages:
                        st.write(f"- {error}")
                
                # 重置缓存，确保数据刷新
                reset_cache()
                
                # 关闭对话框
                st.session_state.show_batch_rename_dialog = False


@st.dialog("批量删除应用")
def batch_delete_dialog():
    """显示批量删除对话框"""
    if st.session_state.selected_app is None or len(st.session_state.selected_app) < 1:
        st.error("未选择应用")
        st.session_state.show_batch_delete_dialog = False
        return
    
    app_ids = st.session_state.selected_app["id"].tolist()
    app_names = st.session_state.selected_app["应用名称"].tolist()
    
    st.subheader(f"批量删除 ({len(app_ids)} 个应用)")
    
    # 显示警告
    st.warning("⚠️ 批量删除是一个危险操作，删除后应用将无法恢复！")
    
    # 显示当前选中的应用
    with st.expander("已选择的应用", expanded=True):
        for i, name in enumerate(app_names):
            st.text(f"{i+1}. {name}")
    
    # 要求用户输入确认
    confirm_text = st.text_input(
        "请输入 'DELETE' 以确认删除",
        key="batch_delete_confirm"
    )
    
    # 按钮区域
    col1, col2 = st.columns(2)
    with col1:
        if st.button("取消", key="btn_cancel_batch_delete", use_container_width=True):
            st.session_state.show_batch_delete_dialog = False
    
    with col2:
        if st.button("确认删除", key="btn_confirm_batch_delete", type="primary", use_container_width=True):
            if confirm_text != "DELETE":
                st.error("请输入 'DELETE' 确认删除操作")
            else:
                client = DifyClient.get_connection()
                progress_bar = st.progress(0)
                success_count = 0
                error_messages = []
                
                with st.spinner("正在批量删除应用..."):
                    for i, (app_id, app_name) in enumerate(zip(app_ids, app_names)):
                        try:
                            client.delete_app(app_id)
                            success_count += 1
                            
                            # 更新进度条
                            progress_bar.progress((i + 1) / len(app_ids))
                        except Exception as e:
                            error_messages.append(f"应用 '{app_name}' 删除失败: {str(e)}")
                
                # 显示结果
                if success_count > 0:
                    st.success(f"成功删除 {success_count} 个应用")
                
                if error_messages:
                    st.error("部分应用删除失败")
                    for error in error_messages:
                        st.write(f"- {error}")
                
                # 重置缓存，确保数据刷新
                reset_cache()
                
                # 关闭对话框
                st.session_state.show_batch_delete_dialog = False


def toggle_multi_select():
    """切换多选模式"""
    st.session_state.multi_select_mode = not st.session_state.multi_select_mode
    st.session_state.selected_app = None
    st.session_state.show_app_details = False
    st.rerun()

def show_filter_panel():
    """显示过滤面板"""
    st.sidebar.markdown("---")
    st.sidebar.subheader("应用过滤")
    
    # 应用类型过滤
    mode_options = {
        "all": "所有类型",
        DifyAppMode.CHAT: "聊天助手 (Chat)",
        DifyAppMode.AGENT_CHAT: "代理模式 (Agent Chat)",
        DifyAppMode.COMPLETION: "文本生成 (Completion)",
        DifyAppMode.ADVANCED_CHAT: "高级聊天流 (Advanced Chat)",
        DifyAppMode.WORKFLOW: "工作流 (Workflow)",
    }
    
    selected_mode = st.sidebar.selectbox(
        "应用类型",
        options=list(mode_options.keys()),
        format_func=lambda x: mode_options[x],
        index=list(mode_options.keys()).index(st.session_state.filter_mode)
    )
    
    if selected_mode != st.session_state.filter_mode:
        st.session_state.filter_mode = selected_mode
        st.session_state.selected_app = None
        st.session_state.show_app_details = False
    
    # 标签过滤
    if DifyClient.is_connected():
        try:
            client = DifyClient.get_connection()
            all_tags = client.fetch_tags()
            
            if all_tags:
                tag_options = {"none": "不过滤标签"}
                for tag in all_tags:
                    tag_options[tag["id"]] = tag["name"]
                
                selected_tag = st.sidebar.selectbox(
                    "标签过滤",
                    options=list(tag_options.keys()),
                    format_func=lambda x: tag_options[x],
                    index=0 if st.session_state.filter_tag is None else list(tag_options.keys()).index(st.session_state.filter_tag)
                )
                
                if selected_tag == "none":
                    if st.session_state.filter_tag is not None:
                        st.session_state.filter_tag = None
                        st.session_state.selected_app = None
                        st.session_state.show_app_details = False
                elif selected_tag != st.session_state.filter_tag:
                    st.session_state.filter_tag = selected_tag
                    st.session_state.selected_app = None
                    st.session_state.show_app_details = False
        except Exception:
            pass


def show_batch_operations_panel():
    """显示批量操作面板"""
    if st.session_state.selected_app is None or len(st.session_state.selected_app) < 2:
        return
    
    app_ids = st.session_state.selected_app["id"].tolist()
    
    st.subheader(f"批量操作 ({len(app_ids)} 个应用)")
    
    # 批量操作按钮
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("批量导出DSL", key="btn_batch_export", use_container_width=True):
            st.session_state.show_batch_export_dialog = True
    
    with col2:
        if st.button("批量重命名", key="btn_batch_rename", use_container_width=True):
            st.session_state.show_batch_rename_dialog = True
    
    with col3:
        if st.button("批量删除", key="btn_batch_delete", type="primary", use_container_width=True):
            st.session_state.show_batch_delete_dialog = True


def show_app_list():
    """显示应用列表界面"""
    # 页面标题
    page_header("应用管理", "")
    
    # 获取应用列表
    apps = get_apps()
    primary_actions_container = st.container()
    secondary_actions_container = st.container()
    # 操作按钮
    primary_actions = [
        {
            "label": "创建新应用", 
            "key": "btn_create_app", 
            "on_click": lambda: setattr(st.session_state, "show_create_app_dialog", True),
        },
        {
            "label": "导入应用DSL", 
            "key": "btn_import_dsl", 
            "on_click": lambda: setattr(st.session_state, "show_import_dsl_dialog", True),
        },
        {
            "label": "刷新列表",
            "key": "btn_refresh_apps",
            "on_click": reset_cache,
        },
        {
            "label": "多选模式" if st.session_state.multi_select_mode else "单选模式",
            "key": "btn_multi_select",
            "on_click": toggle_multi_select,
        }
    ]
    with primary_actions_container:
        action_bar(primary_actions)
    
    # 显示统计信息
    if apps:
        st.info(f"共 {len(apps)} 个应用")
    
    # 定义表格列配置
    columns = [
        {"field": "id", "title": "id"},
        {"field": "name", "title": "应用名称"},
        {"field": "mode", "title": "应用类型"},
        {"field": "description", "title": "描述"},
        {"field": "created_at", "title": "创建时间"},
        {'field': lambda app: format_timestamp(app.get("updated_at", 0)), 'title': '更新时间'}
    ]

    # 处理时间戳
    for app in apps:
        if "created_at" in app:
            app["created_at"] = format_timestamp(app["created_at"])

    # 显示数据表格
    selected_df = data_display(
        apps, 
        columns, 
        key="app_table", 
        multi_select=st.session_state.multi_select_mode
    )

    # 保存选中的行
    st.session_state.selected_app = selected_df

    # 如果是多选模式且选中了多个应用，显示批量操作面板
    if st.session_state.multi_select_mode and len(selected_df) >= 2:
        with secondary_actions_container:
            show_batch_operations_panel()
    
    # 如果选中了单个应用，显示详情按钮
    if len(selected_df) == 1:
        with st.container():
            app_id = selected_df.iloc[0]["id"]
            
            # 应用操作按钮
            secondary_actions = [
                # {"label": "编辑应用", "key": "btn_edit_app", 
                # "on_click": lambda: edit_app(app_id)},
                # {"label": "DSL导出", "key": "btn_export_dsl", 
                # "on_click": lambda: export_dsl(app_id)},
                # {
                #     "label": "删除应用",
                #     "key": "btn_delete_app",
                #     "color": "danger",
                #     "on_click": lambda: delete_app(app_id, on_success=reset_cache),
                # },
            ]

            # action_bar(secondary_actions)
            
            # 显示应用详情页面
            show_app_details()


def show_app_details():
    """显示应用详情界面"""
    if st.session_state.selected_app is None or len(st.session_state.selected_app) != 1:
        st.error("未选择应用或选择了多个应用")
        st.session_state.show_app_details = False
        return
    
    app_id = st.session_state.selected_app.iloc[0]["id"]
    app_details(app_id, on_back=lambda: set_sesstion_state("show_app_details", False, rerun=True))


def main():
    """主函数"""
    site_sidebar()
    
    # 添加过滤面板
    show_filter_panel()
    
    # 检查连接状态
    if not DifyClient.is_connected():
        st.warning("未连接到Dify平台")
        st.info("请先在主页连接到Dify平台")

        # 返回主页按钮
        if st.button("返回主页"):
            st.switch_page(Pages.HOME)
        return
    
    
    show_app_list()
    
    
    # 显示各类对话框
    if st.session_state.show_create_app_dialog:
        st.session_state.show_create_app_dialog = False
        create_app_dialog()

    if st.session_state.show_import_dsl_dialog:
        st.session_state.show_import_dsl_dialog = False
        import_dsl_dialog()
    
    if st.session_state.show_batch_export_dialog:
        st.session_state.show_batch_export_dialog = False
        batch_export_dsl_dialog()
    
    if st.session_state.show_batch_rename_dialog:
        st.session_state.show_batch_rename_dialog = False
        batch_rename_dialog()
    
    if st.session_state.show_batch_delete_dialog:
        st.session_state.show_batch_delete_dialog = False
        batch_delete_dialog()


if __name__ == "__main__":
    main()

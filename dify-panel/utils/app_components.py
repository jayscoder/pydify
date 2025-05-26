import streamlit as st
import json
import yaml
from utils.ui_components import page_header, action_bar, format_timestamp, json_viewer, confirmation_dialog
from utils.dsl_components import dsl_graph
from utils.dify_client import DifyClient


def app_details(app_id, on_back=None):
    """
    显示应用详情页面
    
    参数:
        app_id: 应用ID
        on_back: 返回按钮的回调函数
    """
    # 获取应用详情
    client = DifyClient.get_connection()
    if not client:
        st.error("未连接到Dify API，请先在设置中配置连接")
        return
    
    try:
        app_details = client.fetch_app(app_id)
        if not app_details:
            st.error("获取应用详情失败")
            if st.button("返回", key="btn_back_fail"):
                if on_back:
                    on_back()
            return
        
        # 保存当前应用ID到会话状态
        st.session_state.current_app_id = app_id
        # 操作按钮行
        detail_actions = [
            {
                "label": "编辑应用",
                "key": "btn_edit_app",
                "on_click": lambda: setattr(st.session_state, "show_edit_app_dialog", True),
            },
            {
                "label": "导出DSL",
                "key": "btn_export_dsl",
                "on_click": lambda: export_dsl(app_id),
            },
            {
                "label": "删除应用",
                "key": "btn_delete_app",
                "color": "danger",
                "on_click": lambda: delete_app(app_id, on_back),
            },
        ]
        action_bar(detail_actions)

        # 应用基本信息选项卡
        tabs = st.tabs(['基本详情', '详情JSON', 'API密钥', '标签管理', 'DSL可视化', '工具展示'])
        
        # Tab 1: 基本详情
        with tabs[0]:
            st.subheader("基本信息")
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**应用ID**: {app_details['id']}")
                st.write(f"**应用名称**: {app_details['name']}")
                st.write(f"**应用类型**: {app_details['mode']}")
                st.write(f"**创建者**: {app_details.get('created_by', '未知')}")
                # 应用链接：点击后可以跳转
                app_url = client.app_url(app_id=app_details['id'], app_mode=app_details['mode'])
                st.write(f"**应用链接**: {app_url}")
            with col2:
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
            
            # 应用图标和配置
            st.subheader("应用配置")
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**图标类型**: {app_details.get('icon_type', '无')}")
                st.write(f"**图标内容**: {app_details.get('icon', '无')}")
                st.write(f"**图标背景色**: {app_details.get('icon_background', '无')}")
                st.write(f"**启用网站**: {'是' if app_details.get('enable_site', False) else '否'}")
            with col2:
                st.write(f"**启用API**: {'是' if app_details.get('enable_api', False) else '否'}")
                st.write(f"**API基础URL**: {app_details.get('api_base_url', '无')}")
                st.write(f"**使用图标作为回答图标**: {'是' if app_details.get('use_icon_as_answer_icon', False) else '否'}")
        
        # Tab 2: 详情JSON
        with tabs[1]:
            st.subheader("应用详情JSON")
            json_viewer(app_details)
            
            # 提供下载JSON的功能
            st.download_button(
                label="下载JSON",
                data=json.dumps(app_details, indent=2, ensure_ascii=False),
                file_name=f"{app_details['name']}_details.json",
                mime="application/json"
            )
        
        # Tab 3: API密钥
        with tabs[2]:
            display_api_keys(app_id)
        
        # Tab 4: 标签管理
        with tabs[3]:
            display_tags(app_id, app_details)
        
        # Tab 5: DSL可视化
        with tabs[4]:
            display_dsl_visualization(app_id, app_details)
        
        # Tab 6: 工具展示
        with tabs[5]:
            display_tools(app_details)
            
        # 显示编辑应用对话框
        if st.session_state.get("show_edit_app_dialog", False):
            edit_app_dialog(app_id, app_details)

    except Exception as e:
        st.error(f"加载应用详情失败: {str(e)}")
        import traceback
        st.error(traceback.format_exc())
        if st.button("返回", key="btn_back_error"):
            if on_back:
                on_back()


def display_api_keys(app_id):
    """显示API密钥管理界面"""
    st.subheader("API密钥管理")
    
    client = DifyClient.get_connection()
    # 获取API密钥列表
    try:
        api_keys = client.fetch_app_api_keys(app_id)
        
        # 创建新API密钥的按钮
        if st.button("创建新API密钥", key="btn_create_api_key"):
            try:
                new_key = client.create_app_api_key(app_id)
                st.success(f"API密钥创建成功: {new_key['token']}")
                # 刷新页面以显示新密钥
                st.rerun()
            except Exception as e:
                st.error(f"创建API密钥失败: {str(e)}")
        
        # 显示API密钥列表
        if api_keys:
            api_key_data = []
            for key in api_keys:
                api_key_data.append({
                    "ID": key['id'],
                    "类型": key['type'],
                    "令牌": key['token'],
                    "最后使用时间": key['last_used_at'] or "从未使用",
                    "创建时间": format_timestamp(key['created_at'])
                })
            
            # 使用dataframe显示
            st.dataframe(api_key_data, use_container_width=True)
            
            # 删除API密钥
            with st.expander("删除API密钥"):
                api_key_to_delete = st.selectbox(
                    "选择要删除的API密钥", 
                    options=[key['id'] for key in api_keys],
                    format_func=lambda x: next((k['token'] for k in api_keys if k['id'] == x), x)
                )
                
                if st.button("删除选中的API密钥", key="btn_delete_api_key"):
                    try:
                        client.delete_app_api_key(app_id, api_key_to_delete)
                        st.success("API密钥删除成功")
                        # 刷新页面
                        st.rerun()
                    except Exception as e:
                        st.error(f"删除API密钥失败: {str(e)}")
        else:
            st.info("该应用暂无API密钥")
    except Exception as e:
        st.error(f"获取API密钥列表失败: {str(e)}")


def display_tags(app_id, app_details):
    """显示标签管理界面"""
    st.subheader("标签管理")
    
    client = DifyClient.get_connection()
    # 获取所有标签
    try:
        all_tags = client.fetch_tags()
        
        # 当前应用的标签
        app_tags = app_details.get("tags", [])
        app_tag_ids = [tag['id'] for tag in app_tags]
        
        # 显示当前应用的标签
        st.write("**当前应用的标签**")
        if app_tags:
            for tag in app_tags:
                st.write(f"- {tag['name']}")
        else:
            st.info("该应用暂无标签")
        
        # 添加标签
        with st.expander("添加标签"):
            # 显示可用标签
            available_tags = [tag for tag in all_tags if tag['id'] not in app_tag_ids]
            
            if available_tags:
                tag_to_add = st.selectbox(
                    "选择要添加的标签",
                    options=[tag['id'] for tag in available_tags],
                    format_func=lambda x: next((t['name'] for t in available_tags if t['id'] == x), x)
                )
                
                if st.button("添加选中的标签", key="btn_add_tag"):
                    try:
                        client.bind_tag_to_app(app_id, tag_to_add)
                        st.success("标签添加成功")
                        # 刷新页面
                        st.rerun()
                    except Exception as e:
                        st.error(f"添加标签失败: {str(e)}")
            else:
                st.info("没有更多可添加的标签")
            
            # 创建新标签
            st.write("**创建新标签**")
            new_tag_name = st.text_input("新标签名称", key="new_tag_name")
            if new_tag_name and st.button("创建新标签", key="btn_create_tag"):
                try:
                    new_tag = client.create_tag(new_tag_name)
                    # 创建后立即绑定到应用
                    client.bind_tag_to_app(app_id, new_tag['id'])
                    st.success(f"标签 '{new_tag_name}' 创建并添加到应用成功")
                    # 刷新页面
                    st.rerun()
                except Exception as e:
                    st.error(f"创建标签失败: {str(e)}")
        
        # 移除标签
        if app_tags:
            with st.expander("移除标签"):
                tag_to_remove = st.selectbox(
                    "选择要移除的标签",
                    options=[tag['id'] for tag in app_tags],
                    format_func=lambda x: next((t['name'] for t in app_tags if t['id'] == x), x)
                )
                
                if st.button("移除选中的标签", key="btn_remove_tag"):
                    try:
                        client.remove_tag_from_app(app_id, tag_to_remove)
                        st.success("标签移除成功")
                        # 刷新页面
                        st.rerun()
                    except Exception as e:
                        st.error(f"移除标签失败: {str(e)}")
    except Exception as e:
        st.error(f"获取标签失败: {str(e)}")


def display_dsl_visualization(app_id, app_details):
    """显示DSL可视化界面"""
    st.subheader("DSL图形可视化")
    
    client = DifyClient.get_connection()
    # 获取应用DSL
    try:
        app_dsl = client.fetch_app_dsl(app_id)
        
        # 转换DSL格式进行可视化 
        if app_dsl:
            # 提供下载DSL的功能
            st.download_button(
                label="下载DSL",
                data=app_dsl,
                file_name=f"{app_details['name']}_dsl.yaml",
                mime="text/yaml"
            )
            
            # 使用dsl_graph函数可视化
            st.write("**DSL图形可视化**")
            dsl_content = yaml.safe_load(app_dsl)
            nodes_df, edges_df = dsl_graph(dsl_content)
        else:
            st.info("无法获取应用DSL数据")
    except Exception as e:
        st.error(f"获取或可视化DSL失败: {str(e)}")
        import traceback
        st.error(traceback.format_exc())  # 显示完整错误堆栈


def display_tools(app_details):
    """显示引用的工具信息"""
    st.subheader("引用的工具")
    
    try:
        # 从应用详情中获取工具信息
        if app_details['mode'] == 'workflow':
            workflow_data = app_details.get('workflow', {})
            dependencies = workflow_data.get('dependencies', [])
            
            if dependencies:
                tool_data = []
                for dep in dependencies:
                    tool_type = dep.get('type', '')
                    value = dep.get('value', {})
                    
                    if tool_type == 'marketplace':
                        tool_data.append({
                            "类型": "市场插件",
                            "标识符": value.get('marketplace_plugin_unique_identifier', ''),
                            "来源": "插件市场"
                        })
                    elif tool_type == 'workflow':
                        tool_data.append({
                            "类型": "工作流工具",
                            "标识符": value.get('workflow_unique_identifier', ''),
                            "来源": "自定义工作流"
                        })
                    else:
                        tool_data.append({
                            "类型": tool_type,
                            "标识符": str(value),
                            "来源": "其他来源"
                        })
                
                # 显示工具列表
                st.dataframe(tool_data, use_container_width=True)
            else:
                st.info("该应用未引用任何工具")
        else:
            st.info("非工作流应用，不包含工具引用信息")
    except Exception as e:
        st.error(f"获取工具信息失败: {str(e)}")


@st.dialog("编辑应用")
def edit_app_dialog(app_id, app_info=None):
    """
    编辑应用信息对话框
    
    参数:
        app_id: 应用ID
        app_info: 应用信息（可选）
    """
    # 初始化session state
    if "show_edit_app_dialog" not in st.session_state:
        st.session_state.show_edit_app_dialog = False
        
    client = DifyClient.get_connection()
    
    if not app_info:
        try:
            # 获取应用当前信息
            app_info = client.fetch_app(app_id)
        except Exception as e:
            st.error(f"加载应用信息失败: {str(e)}")
            st.session_state.show_edit_app_dialog = False
            return
    
    # 编辑表单
    with st.form("edit_app_form"):
        app_name = st.text_input("应用名称", value=app_info['name'])
        app_description = st.text_area("应用描述", value=app_info.get('description', ''))
        
        col1, col2 = st.columns(2)
        with col1:
            cancel_button = st.form_submit_button("取消", type="secondary")
        with col2:
            save_button = st.form_submit_button("保存", type="primary")
        
        if cancel_button:
            st.session_state.show_edit_app_dialog = False
        
        if save_button:
            try:
                client.update_app(app_id, app_name, app_description)
                st.success("应用信息更新成功")
                # 关闭对话框
                st.session_state.show_edit_app_dialog = False
                # 清除缓存
                if "app_details_cache" in st.session_state:
                    st.session_state.app_details_cache = None
                # 刷新页面
                st.rerun()
            except Exception as e:
                st.error(f"更新应用失败: {str(e)}")


def edit_app(app_id):
    """
    打开编辑应用对话框
    
    参数:
        app_id: 应用ID
    """
    # 初始化dialog状态变量
    if "show_edit_app_dialog" not in st.session_state:
        st.session_state.show_edit_app_dialog = False
    
    # 设置对话框打开状态
    st.session_state.show_edit_app_dialog = True
    st.rerun()


def delete_app(app_id, on_success=None):
    """
    删除应用
    
    参数:
        app_id: 应用ID
        on_success: 删除成功后的回调函数
    """
    # 初始化确认状态
    if "confirm_delete_app" not in st.session_state:
        st.session_state.confirm_delete_app = False
    
    # 显示确认按钮
    if st.button("确认删除此应用?", key=f"confirm_delete_{app_id}"):
        st.session_state.confirm_delete_app = True
    
    # 如果确认删除
    if st.session_state.confirm_delete_app:
        with st.container():
            st.warning("⚠️ 删除操作不可恢复，请确认!")
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("取消", key=f"cancel_delete_{app_id}"):
                    st.session_state.confirm_delete_app = False
                    st.rerun()
            
            with col2:
                if st.button("确认删除", key=f"proceed_delete_{app_id}", type="primary"):
                    client = DifyClient.get_connection()
                    try:
                        client.delete_app(app_id)
                        st.success("应用删除成功")
                        # 执行成功回调，例如返回应用列表页面
                        if on_success:
                            on_success()
                    except Exception as e:
                        st.error(f"删除应用失败: {str(e)}")
                    
                    # 重置确认状态
                    st.session_state.confirm_delete_app = False


def export_dsl(app_id):
    """
    导出应用DSL
    
    参数:
        app_id: 应用ID
    """
    client = DifyClient.get_connection()
    try:
        # 获取应用信息用于文件名
        app_info = client.fetch_app(app_id)
        app_name = app_info['name']
        
        # 获取DSL
        app_dsl = client.fetch_app_dsl(app_id)
        
        # 使用Streamlit的下载功能
        st.download_button(
            label="下载DSL",
            data=app_dsl,
            file_name=f"{app_name}_dsl.yaml",
            mime="text/yaml"
        )
    except Exception as e:
        st.error(f"导出DSL失败: {str(e)}")


def st_app_detail(app_id: str, on_click_back=None):
    """
    显示应用详情
    
    Args:
        app_id (_type_): _description_
        on_click_back (_type_, optional): _description_. Defaults to None.
    """
    
    app_details = get_app_details(st.session_state.current_app_id)
    if not app_details:
        st.error("获取应用详情失败")
        if st.button("返回", key="btn_back_fail"):
            if on_click_back:
                on_click_back()
        return
    
    # 显示应用详情
    page_header(f"应用详情: {app_details['name']}", f"查看应用的详细信息")
    
    # 应用基本信息
    tabs = ['基本信息', '编辑', '详情JSON', 'API密钥', '标签管理', 'DSL导出', 'DSL可视化']
    tabs = st.tabs(tabs)
    
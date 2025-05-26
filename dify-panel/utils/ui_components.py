"""
UI组件工具类 - 提供可复用的Streamlit界面组件
"""

from typing import Any, Callable, Dict, List, Optional, Union

import pandas as pd
import streamlit as st
from utils.dify_client import DifyClient
from config import Pages
import time
import json
import uuid

def connection_form():
    """
    显示连接表单，用于配置和连接到Dify平台
    """
    # 获取默认连接信息
    default_base_url, default_email, default_password = DifyClient.get_default_connection_info()

    # 创建连接表单
    with st.form("dify_connection_form"):
        st.subheader("Dify平台连接")
        
        base_url = st.text_input("平台URL", value=default_base_url, placeholder="例如: https://cloud.dify.ai 或 http://localhost:5001")
        email = st.text_input("邮箱", value=default_email, placeholder="登录邮箱")
        password = st.text_input("密码", value=default_password, type="password", placeholder="登录密码")
        
        # 测试连接和保存按钮
        col1, col2 = st.columns(2)
        with col1:
            test_connection = st.form_submit_button("测试连接", use_container_width=True)
        with col2:
            save_connection = st.form_submit_button("连接", use_container_width=True, type="primary")
        
        # 测试连接
        if test_connection:
            if not base_url or not email or not password:
                st.error("请填写所有必填字段")
            else:
                with st.spinner("正在测试连接..."):
                    connection_successful = DifyClient.test_connect(base_url, email, password)
                    if connection_successful:
                        st.success("连接测试成功!")
                    else:
                        st.error("连接测试失败，请检查连接信息")
        
        # 保存连接
        if save_connection:
            if not base_url or not email or not password:
                st.error("请填写所有必填字段")
            else:
                with st.spinner("正在连接..."):
                    connection_successful = DifyClient.connect(base_url, email, password)
                    if connection_successful:
                        st.success("连接成功!")
                        st.rerun()  # 重新加载页面以更新连接状态
                    else:
                        st.error("连接失败，请检查连接信息")


def app_selector(apps: List[Dict[str, Any]], key: str = "app_selector"):
    """
    显示应用选择器

    Args:
        apps (List[Dict]): 应用列表
        key (str): 组件唯一标识

    Returns:
        str: 选中的应用ID
    """
    if not apps:
        st.warning("没有可用的应用")
        return None

    # 构建应用选择列表
    app_options = {f"{app['name']} ({app['mode']})": app["id"] for app in apps}

    # 显示选择器
    selected_app_name = st.selectbox(
        "选择应用", options=list(app_options.keys()), key=key
    )

    if selected_app_name:
        return app_options[selected_app_name]
    return None


def app_card(
    app: Dict[str, Any],
    on_view=None,
    on_edit=None,
    on_delete=None,
    on_api_keys=None,
    on_tags=None,
):
    """
    显示应用卡片

    Args:
        app (Dict): 应用信息
        on_view (Callable): 查看应用详情的回调
        on_edit (Callable): 编辑应用的回调
        on_delete (Callable): 删除应用的回调
        on_api_keys (Callable): 管理API密钥的回调
        on_tags (Callable): 管理标签的回调
    """
    with st.container():
        # 应用标题行
        col1, col2 = st.columns([3, 1])
        with col1:
            st.subheader(f"{app['name']} ({app['mode']})")

        # 应用描述
        st.write(app.get("description", "无描述"))

        # 应用详情区域
        details_cols = st.columns(3)
        with details_cols[0]:
            st.write(f"**创建时间**: {format_timestamp(app.get('created_at', 0))}")
        with details_cols[1]:
            st.write(f"**更新时间**: {format_timestamp(app.get('updated_at', 0))}")
        with details_cols[2]:
            # 显示标签(如果有)
            tags = app.get("tags", [])
            if tags:
                tag_str = ", ".join([tag.get("name", "") for tag in tags])
                st.write(f"**标签**: {tag_str}")

        # 操作按钮
        action_cols = st.columns(5)

        if on_view:
            with action_cols[0]:
                if st.button("查看", key=f"view_{app['id']}"):
                    on_view(app["id"])

        if on_edit:
            with action_cols[1]:
                if st.button("编辑", key=f"edit_{app['id']}"):
                    on_edit(app["id"])

        if on_api_keys:
            with action_cols[2]:
                if st.button("API密钥", key=f"api_{app['id']}"):
                    on_api_keys(app["id"])

        if on_tags:
            with action_cols[3]:
                if st.button("标签", key=f"tags_{app['id']}"):
                    on_tags(app["id"])

        if on_delete:
            with action_cols[4]:
                if st.button("删除", key=f"delete_{app['id']}"):
                    on_delete(app["id"])

        st.divider()


def format_timestamp(timestamp):
    """
    将时间戳格式化为可读的时间格式
    
    参数:
        timestamp: 时间戳（秒）
    
    返回:
        格式化后的时间字符串
    """
    if not timestamp:
        return "未知时间"
    
    try:
        # 将时间戳转换为可读时间
        time_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timestamp))
        return time_str
    except Exception:
        return str(timestamp)


def confirmation_dialog(title, message, on_confirm, on_cancel=None):
    """
    显示确认对话框

    Args:
        title (str): 对话框标题
        message (str): 对话框消息
        on_confirm (Callable): 确认回调
        on_cancel (Callable, optional): 取消回调
    """
    st.subheader(title)
    st.write(message)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("确认", key="confirm_yes"):
            on_confirm()

    with col2:
        if st.button("取消", key="confirm_no"):
            if on_cancel:
                on_cancel()
            return False

    return True


def api_key_card(api_key, on_delete=None):
    """
    显示API密钥卡片

    Args:
        api_key (Dict): API密钥信息
        on_delete (Callable): 删除API密钥的回调
    """
    with st.container():
        col1, col2 = st.columns([3, 1])

        with col1:
            st.code(api_key["token"], language=None)
            st.write(f"创建时间: {format_timestamp(api_key.get('created_at', 0))}")

            last_used = api_key.get("last_used_at")
            if last_used:
                st.write(f"最后使用: {last_used}")
            else:
                st.write("最后使用: 从未使用")

        with col2:
            if on_delete:
                if st.button("删除", key=f"delete_api_{api_key['id']}"):
                    on_delete(api_key["id"])

        st.divider()


def tag_card(tag, on_edit=None, on_delete=None):
    """
    显示标签卡片

    Args:
        tag (Dict): 标签信息
        on_edit (Callable): 编辑标签的回调
        on_delete (Callable): 删除标签的回调
    """
    with st.container():
        col1, col2, col3 = st.columns([2, 1, 1])

        with col1:
            st.write(f"**{tag['name']}** (引用: {tag.get('binding_count', 0)})")

        if on_edit:
            with col2:
                if st.button("编辑", key=f"edit_tag_{tag['id']}"):
                    on_edit(tag["id"], tag["name"])

        if on_delete:
            with col3:
                if st.button("删除", key=f"delete_tag_{tag['id']}"):
                    on_delete(tag["id"])

        st.divider()


def page_header(title, description=""):
    """
    显示页面标题和描述
    
    参数:
        title: 页面标题
        description: 页面描述
    """
    st.title(title)
    if description:
        st.markdown(description)
    
def error_placeholder(error_message=None):
    """
    显示错误占位符

    Args:
        error_message (str, optional): 错误消息
    """
    if error_message:
        st.error(error_message)
    else:
        st.error("出错了！请检查输入或联系管理员。")


def success_message(message):
    """
    显示成功消息

    Args:
        message (str): 成功消息
    """
    st.success(message)


def loading_spinner(message="处理中，请稍候..."):
    """
    显示加载动画

    Args:
        message (str): 加载消息
    """
    return st.spinner(message)


# 新增表格式UI组件


def data_display(
    data: List[Dict[str, Any]],
    columns: List[Dict[str, str]],
    key: str,
    height: int = 500,
    on_select: Callable = None,
    multi_select: bool = False,
):
    """
    显示数据表格并支持行选择

    Args:
        data (List[Dict]): 数据列表
        columns (List[Dict]): 列配置，格式为 [{"field": "字段名" | 函数, "title": "显示名"}]
            field可以是嵌套路径，如a.b表示获取item['a']['b']，a.b.c表示获取item['a']['b']['c']
        key (str): 表格唯一标识
        height (int): 表格高度
        on_select (Callable): 选中行时的回调函数，参数为选中的行数据
        multi_select (bool): 是否启用多选
    Returns:
        pandas.DataFrame: 选中的行数据，如果未选择则返回空DataFrame
    """
    if not data:
        st.info("没有可显示的数据")
        return pd.DataFrame()
    
    def get_nested_value(item, field_path):
        """递归获取嵌套字段值"""
        try:
            keys = field_path.split('.')
            value = item
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return None
    # 转换为DataFrame
    if columns is not None:
        df_data = []
        for item in data:
            row = {}
            for col in columns:
                field = col["field"]
                if callable(field):
                    row[col["title"]] = field(item)
                elif '.' in field:  # 处理嵌套字段
                    value = get_nested_value(item, field)
                    if isinstance(value, (dict, list)):
                        row[col["title"]] = str(value)
                    else:
                        row[col["title"]] = value if value is not None else "-"
                elif field in item:
                    if isinstance(item[field], (dict, list)):
                        row[col["title"]] = str(item[field])
                    else:
                        row[col["title"]] = item[field]
                else:
                    row[col["title"]] = "-"
            df_data.append(row)

        df = pd.DataFrame(df_data)
    else:
        df = pd.DataFrame(data)
    
    # 搜索
    search = st.text_input("搜索", key=f"search_{key}")
    
    if search and not df.empty:
        # 使用更安全的方式过滤DataFrame
        try:
            mask = pd.Series(False, index=df.index)
            search_lower = search.lower()
            
            # 对每一列应用搜索
            for col in df.columns:
                # 将列转换为字符串并转为小写进行比较
                col_mask = df[col].astype(str).str.lower().str.contains(search_lower, na=False)
                mask = mask | col_mask
            
            # 应用过滤
            filtered_df = df[mask]
            
            # 如果过滤后有结果，则使用过滤后的DataFrame
            if not filtered_df.empty:
                df = filtered_df
            else:
                st.info("未找到匹配的记录")
        except Exception as e:
            st.error(f"搜索时发生错误: {str(e)}")
        
    # 显示表格，使用适合Streamlit新版本的数据表格组件
    event = st.dataframe(
        df, height=height, on_select='rerun', use_container_width=True, selection_mode="single-row" if not multi_select else "multi-row", key=key
    )

    selected_df = df.iloc[event.selection.rows]
    
    # 处理选择行事件
    if not selected_df.empty and on_select:
        on_select(selected_df)
        
    # 返回选中的行
    return selected_df


@st.dialog("详情查看", width="large")
def show_detail_dialog(title, content_func=None, key=None):
    """
    使用st.dialog显示详情弹窗

    Args:
        title (str): 对话框标题
        content_func (Callable): 生成对话框内容的函数
        key (str): 组件唯一标识
    """
    st.subheader(title)
    
    # 显示内容
    if content_func:
        content_func()
   


def detail_dialog(title, content_func=None, on_close=None):
    """
    显示详情弹窗

    Args:
        title (str): 弹窗标题
        content_func (Callable): 生成弹窗内容的函数
        on_close (Callable, optional): 关闭按钮回调
    """
    with st.container():
        st.subheader(title)

        # 显示内容
        if content_func:
            content_func()

        # 关闭按钮
        if on_close and st.button("关闭", key="close_dialog"):
            on_close()


def action_bar(actions):
    """
    创建操作按钮栏
    
    参数:
        actions: 操作按钮列表，每个按钮是一个字典，包含label, key, on_click等
        alignment: 按钮对齐方式，默认右对齐
    """
    # 创建按钮容器
    cols = st.columns([1] * len(actions))
    
    for i, action in enumerate(actions):
        label = action.get("label", "")
        key = action.get("key", f"btn_{uuid.uuid4()}")
        on_click = action.get("on_click", None)
        color = action.get("color", "primary")
        rerun = action.get("rerun", False)
        if color == "danger":
            if cols[i].button(label, key=key, type="primary", use_container_width=True):
                if on_click:
                    on_click()
                    if rerun:
                        st.rerun()
        else:
            if cols[i].button(label, key=key, use_container_width=True):
                if on_click:
                    on_click()
                    if rerun:
                        st.rerun()


def site_sidebar():
    # 主要的侧边栏
    from models import Site
    from utils.dify_client import DifyClient, try_auto_connect
    
    if not DifyClient.is_connected():
        try_auto_connect()
    
    with st.sidebar:
        # 显示连接状态
        if DifyClient.is_connected():
            # 从数据库获取所有站点
            active_site = DifyClient.get_active_site()
            try:
                sites = list(Site.select().dicts())
                site_id_mapping = {site['id']: site for site in sites}
                
                if sites:
                    # 构建站点选择列表
                    site_ids = [site['id'] for site in sites]
                    def site_option_formart(site_id):
                        site_option = site_id_mapping[site_id]
                        return f"{site_option['name']} ({site_option['base_url']})"

                    active_site_index = 0
                    if active_site:
                        active_site_index = site_ids.index(active_site['id'])
                    
                    # 显示选择器，默认值为"- 选择要切换的站点 -"
                    selected_site_id = st.selectbox(
                        "选择站点",
                        options=site_ids,
                        format_func=site_option_formart,
                        key="site_selector",
                        index=active_site_index
                    )
                    
                    # 如果用户选择了一个站点，且与当前站点不同，则连接到新站点
                    if selected_site_id != active_site.get("id"):
                        # 查找选中的站点信息
                        selected_site = site_id_mapping[selected_site_id]
                        
                        # 如果选中的站点与当前站点不同，则连接到新站点
                        if not active_site or selected_site_id != active_site.get("id"):
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                if st.button("连接", key="connect_selected_site"):
                                    with st.spinner(f"正在连接到站点 {selected_site['name']}..."):
                                        if DifyClient.connect(
                                            selected_site["base_url"],
                                            selected_site["email"],
                                            selected_site["password"],
                                            selected_site["id"],
                                            selected_site["name"]
                                        ):
                                            st.success(f"已连接到站点: {selected_site['name']}")
                                            st.rerun()
                            
                            with col2:
                                if not selected_site.get("is_default") and st.button("设为默认", key="set_default_site"):
                                    try:
                                        # 将所有站点的is_default设为False
                                        Site.update(is_default=False).execute()
                                        
                                        # 将选中的站点设为默认
                                        site_obj = Site.get_by_id(selected_site_id)
                                        site_obj.is_default = True
                                        site_obj.save()
                                        
                                        st.success(f"已将 {selected_site['name']} 设为默认站点")
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"设置默认站点失败: {str(e)}")
                else:
                    st.info("没有可用的站点")
                    if st.button("添加站点"):
                        st.switch_page(Pages.SITE_MANAGEMENT)
            except Exception as e:
                st.error(f"获取站点列表失败: {str(e)}")
                if st.button("管理站点", key="manage_sites_error"):
                    st.switch_page(Pages.SITE_MANAGEMENT)

            active_site = DifyClient.get_active_site()

            if active_site:
                # 如果有活跃站点信息，显示当前站点
                st.write(f"当前站点: {active_site['name']}")
            
            st.write(f"服务器: {st.session_state.dify_base_url}")
            st.write(f"账号: {st.session_state.dify_email}")
            
        else:
            st.warning("未连接到Dify平台")
            st.info("请在右侧连接表单中输入Dify平台的连接信息")
            
            # 站点管理按钮
            if st.button("站点管理"):
                st.switch_page(Pages.SITE_MANAGEMENT)


def json_viewer(data):
    """
    显示格式化的JSON数据
    
    参数:
        data: 要显示的JSON数据
    """
    # 转换为格式化的JSON字符串
    if data:
        try:
            if isinstance(data, str):
                data = json.loads(data)
            
            formatted_json = json.dumps(data, indent=2, ensure_ascii=False)
            st.code(formatted_json, language="json")
        except Exception as e:
            st.error(f"JSON格式化失败: {str(e)}")
            st.write(data)
    else:
        st.info("无数据")


def confirmation_dialog(title, message, key=None):
    """
    显示确认对话框
    
    参数:
        title: 对话框标题
        message: 对话框消息
        key: 组件key
    
    返回:
        bool: 是否确认
    """
    # 使用expander作为简单的确认对话框
    with st.expander(title, expanded=True):
        st.write(message)
        col1, col2 = st.columns(2)
        confirmed = col1.button("确认", key=f"{key}_confirm" if key else None, type="primary")
        cancelled = col2.button("取消", key=f"{key}_cancel" if key else None)
        
        if cancelled:
            return False
        
        return confirmed


def set_sesstion_state(key, value, rerun=False):
    """
    设置session状态
    """
    st.session_state[key] = value
    if rerun:
        st.rerun()
        
def toggle_session_state(key, rerun=False):
    """
    切换session状态
    """
    if key not in st.session_state:
        st.session_state[key] = True
    else:
        st.session_state[key] = not st.session_state[key]
    if rerun:
        st.rerun()

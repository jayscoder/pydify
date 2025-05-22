"""
UI组件工具类 - 提供可复用的Streamlit界面组件
"""
import streamlit as st
import pandas as pd
from typing import List, Dict, Any, Callable, Optional, Union
from utils.dify_client import DifyClient

def connection_form():
    """
    显示Dify平台连接表单
    
    从环境变量中读取默认值，并显示在表单中
    返回用户输入的连接信息和是否点击了连接按钮
    
    Returns:
        tuple: (base_url, email, password, submit_clicked)
    """
    # 获取环境变量中的默认值
    default_base_url, default_email, default_password = DifyClient.get_default_connection_info()
    
    # 优先使用session_state中的值，再使用环境变量中的默认值
    base_url_value = st.session_state.get("dify_base_url", default_base_url)
    email_value = st.session_state.get("dify_email", default_email)
    password_value = st.session_state.get("dify_password", default_password)
    
    with st.form("连接Dify平台"):
        st.subheader("连接到Dify平台")
        base_url = st.text_input("服务器地址", 
                               value=base_url_value,
                               placeholder="例如: http://example.com:11080")
        email = st.text_input("邮箱账号", 
                            value=email_value,
                            placeholder="例如: admin@example.com")
        password = st.text_input("密码", 
                               value=password_value,
                               type="password")
        
        if default_base_url or default_email:
            st.info("已从环境变量中加载连接信息作为默认值")
        
        submit = st.form_submit_button("连接")
        
    return base_url, email, password, submit

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
    app_options = {f"{app['name']} ({app['mode']})": app['id'] for app in apps}
    
    # 显示选择器
    selected_app_name = st.selectbox(
        "选择应用",
        options=list(app_options.keys()),
        key=key
    )
    
    if selected_app_name:
        return app_options[selected_app_name]
    return None

def app_card(app: Dict[str, Any], on_view=None, on_edit=None, on_delete=None, on_api_keys=None, on_tags=None):
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
        st.write(app.get('description', '无描述'))
        
        # 应用详情区域
        details_cols = st.columns(3)
        with details_cols[0]:
            st.write(f"**创建时间**: {format_timestamp(app.get('created_at', 0))}")
        with details_cols[1]:
            st.write(f"**更新时间**: {format_timestamp(app.get('updated_at', 0))}")
        with details_cols[2]:
            # 显示标签(如果有)
            tags = app.get('tags', [])
            if tags:
                tag_str = ", ".join([tag.get('name', '') for tag in tags])
                st.write(f"**标签**: {tag_str}")
        
        # 操作按钮
        action_cols = st.columns(5)
        
        if on_view:
            with action_cols[0]:
                if st.button("查看", key=f"view_{app['id']}"):
                    on_view(app['id'])
        
        if on_edit:
            with action_cols[1]:
                if st.button("编辑", key=f"edit_{app['id']}"):
                    on_edit(app['id'])
        
        if on_api_keys:
            with action_cols[2]:
                if st.button("API密钥", key=f"api_{app['id']}"):
                    on_api_keys(app['id'])
        
        if on_tags:
            with action_cols[3]:
                if st.button("标签", key=f"tags_{app['id']}"):
                    on_tags(app['id'])
        
        if on_delete:
            with action_cols[4]:
                if st.button("删除", key=f"delete_{app['id']}"):
                    on_delete(app['id'])
        
        st.divider()

def format_timestamp(timestamp):
    """
    格式化时间戳为可读字符串
    
    Args:
        timestamp (int): Unix时间戳(毫秒)
        
    Returns:
        str: 格式化后的日期时间
    """
    if not timestamp:
        return "未知"
    
    import datetime
    # 将时间戳转换为日期时间对象
    dt = datetime.datetime.fromtimestamp(timestamp / 1000.0)
    return dt.strftime("%Y-%m-%d %H:%M:%S")

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
            st.code(api_key['token'], language=None)
            st.write(f"创建时间: {format_timestamp(api_key.get('created_at', 0))}")
            
            last_used = api_key.get('last_used_at')
            if last_used:
                st.write(f"最后使用: {last_used}")
            else:
                st.write("最后使用: 从未使用")
        
        with col2:
            if on_delete:
                if st.button("删除", key=f"delete_api_{api_key['id']}"):
                    on_delete(api_key['id'])
        
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
                    on_edit(tag['id'], tag['name'])
        
        if on_delete:
            with col3:
                if st.button("删除", key=f"delete_tag_{tag['id']}"):
                    on_delete(tag['id'])
        
        st.divider()

def page_header(title, description=None):
    """
    显示页面标题和描述
    
    Args:
        title (str): 页面标题
        description (str, optional): 页面描述
    """
    st.title(title)
    if description:
        st.write(description)
    st.divider()

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

def data_display(data: List[Dict[str, Any]], columns: List[Dict[str, str]], 
                 key: str, height: int = 500):
    """
    显示数据表格并支持行选择
    
    Args:
        data (List[Dict]): 数据列表
        columns (List[Dict]): 列配置，格式为 [{"field": "字段名", "title": "显示名"}]
        key (str): 表格唯一标识
        height (int): 表格高度
        
    Returns:
        pandas.DataFrame: 选中的行数据，如果未选择则返回空DataFrame
    """
    if not data:
        st.info("没有可显示的数据")
        return pd.DataFrame()
    
    # 转换为DataFrame
    df_data = []
    for item in data:
        row = {}
        for col in columns:
            field = col["field"]
            if field in item:
                if isinstance(item[field], (dict, list)):
                    row[col["title"]] = str(item[field])
                else:
                    row[col["title"]] = item[field]
            else:
                row[col["title"]] = "-"
        # 添加原始ID方便后续操作
        row["_id"] = item.get("id", "")
        df_data.append(row)
    
    df = pd.DataFrame(df_data)
    
    # 显示表格，使用适合Streamlit新版本的数据表格组件
    event = st.dataframe(df, height=height, use_container_width=True,
                         selection_mode="single", key=key)
    
    # 处理选择行事件
    if event.selected_rows:
        # 返回选中的行
        selected_index = event.selected_rows[0]
        return df.iloc[[selected_index]]
    
    return pd.DataFrame()

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

def action_bar(actions: List[Dict[str, Any]]):
    """
    显示操作栏
    
    Args:
        actions (List[Dict]): 操作按钮配置
            格式: [{"label": "按钮文本", "key": "唯一标识", "color": "primary", "on_click": callback_func}]
    """
    cols = st.columns(len(actions))
    
    for i, action in enumerate(actions):
        with cols[i]:
            button_type = action.get("color", "primary")
            if button_type == "primary":
                if st.button(action["label"], key=action["key"]):
                    if "on_click" in action and callable(action["on_click"]):
                        action["on_click"]()
            elif button_type == "secondary":
                if st.button(action["label"], key=action["key"], type="secondary"):
                    if "on_click" in action and callable(action["on_click"]):
                        action["on_click"]()
            elif button_type == "danger":
                danger_button = st.empty()
                if danger_button.button(action["label"], key=action["key"], type="primary", use_container_width=True):
                    if "on_click" in action and callable(action["on_click"]):
                        action["on_click"]() 
"""
Dify管理面板 - 标签管理页面

提供标签的创建、编辑、删除和应用关联功能
"""
import streamlit as st
import time
import sys
import pandas as pd
from pathlib import Path

# 添加项目根目录到Python路径
root_dir = Path(__file__).parent.parent
sys.path.append(str(root_dir))

# 导入工具类
from utils.dify_client import DifyClient
from utils.ui_components import (
    page_header, app_selector, confirmation_dialog,
    success_message, error_placeholder, loading_spinner,
    data_display, detail_dialog, action_bar
)

# 设置页面配置
st.set_page_config(
    page_title="标签管理 - Dify管理面板",
    page_icon="🏷️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 初始化会话状态
if 'tag_view_mode' not in st.session_state:
    st.session_state.tag_view_mode = 'list'  # 可选值: list, create, edit, delete, bind
if 'current_tag_id' not in st.session_state:
    st.session_state.current_tag_id = None
if 'current_tag_name' not in st.session_state:
    st.session_state.current_tag_name = None
if 'current_app_id' not in st.session_state:
    st.session_state.current_app_id = None
if 'tags_cache' not in st.session_state:
    st.session_state.tags_cache = None
if 'selected_tags' not in st.session_state:
    st.session_state.selected_tags = []
if 'selected_tag' not in st.session_state:
    st.session_state.selected_tag = None

def get_tags():
    """获取标签列表，带缓存机制"""
    if not DifyClient.is_connected():
        return []
    
    client = DifyClient.get_connection()
    
    # 使用缓存
    if st.session_state.tags_cache is None:
        try:
            with loading_spinner("加载标签列表..."):
                st.session_state.tags_cache = client.fetch_tags()
        except Exception as e:
            st.error(f"获取标签列表失败: {str(e)}")
            st.session_state.tags_cache = []
    
    return st.session_state.tags_cache

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

def reset_cache():
    """重置标签缓存"""
    st.session_state.tags_cache = None

def create_tag():
    """创建新标签"""
    st.session_state.tag_view_mode = 'create'
    st.rerun()

def edit_tag():
    """编辑标签"""
    if st.session_state.selected_tag is not None and not st.session_state.selected_tag.empty:
        tag_id = st.session_state.selected_tag.iloc[0]["_id"]
        tag_name = st.session_state.selected_tag.iloc[0]["标签名称"]
        st.session_state.tag_view_mode = 'edit'
        st.session_state.current_tag_id = tag_id
        st.session_state.current_tag_name = tag_name
        st.rerun()

def delete_tag():
    """删除标签"""
    if st.session_state.selected_tag is not None and not st.session_state.selected_tag.empty:
        tag_id = st.session_state.selected_tag.iloc[0]["_id"]
        st.session_state.tag_view_mode = 'delete'
        st.session_state.current_tag_id = tag_id
        st.rerun()

def bind_tag_to_app():
    """为应用绑定标签"""
    st.session_state.tag_view_mode = 'bind'
    st.rerun()

def back_to_list():
    """返回标签列表"""
    st.session_state.tag_view_mode = 'list'
    st.session_state.current_tag_id = None
    st.session_state.current_tag_name = None
    st.session_state.selected_tag = None
    st.rerun()

def show_tag_list():
    """显示标签列表"""
    page_header("标签管理", "管理Dify平台上的标签")
    
    # 获取标签列表
    tags = get_tags()
    
    # 添加操作按钮
    actions = [
        {"label": "创建新标签", "key": "btn_create_tag", "on_click": create_tag},
        {"label": "应用标签关联", "key": "btn_tag_binding", "on_click": bind_tag_to_app},
        {"label": "刷新列表", "key": "btn_refresh_tags", "on_click": lambda: reset_cache() or st.rerun()}
    ]
    action_bar(actions)
    
    # 定义表格列配置
    columns = [
        {"field": "name", "title": "标签名称"},
        {"field": "binding_count", "title": "引用数量"}
    ]
    
    # 显示数据表格
    selected_df = data_display(tags, columns, key="tag_table")
    
    # 保存选中的行
    st.session_state.selected_tag = selected_df
    
    # 如果选中了行，显示操作区域
    if not selected_df.empty:
        st.divider()
        st.subheader("操作")
        
        # 操作按钮
        tag_actions = [
            {"label": "编辑标签", "key": "btn_edit_selected", "on_click": edit_tag},
            {"label": "删除标签", "key": "btn_delete_selected", "color": "danger", "on_click": delete_tag}
        ]
        
        action_bar(tag_actions)

def show_create_tag():
    """显示创建标签表单"""
    page_header("创建新标签", "创建一个新的标签")
    
    # 返回按钮
    if st.button("返回列表", key="btn_back_create"):
        back_to_list()
    
    # 创建标签表单
    with st.form("创建标签"):
        name = st.text_input("标签名称", placeholder="请输入标签名称")
        submitted = st.form_submit_button("创建")
        
        if submitted:
            if not name:
                st.error("标签名称不能为空")
                return
            
            # 创建标签
            try:
                client = DifyClient.get_connection()
                with loading_spinner("正在创建标签..."):
                    new_tag = client.create_tag(name)
                
                # 重置缓存
                reset_cache()
                
                # 显示成功消息
                success_message("标签创建成功！")
                
                # 延迟1秒，确保用户看到成功消息
                time.sleep(1)
                
                # 跳转到标签列表
                back_to_list()
            except Exception as e:
                st.error(f"创建标签失败: {str(e)}")

def show_edit_tag():
    """显示编辑标签表单"""
    if not st.session_state.current_tag_id or not st.session_state.current_tag_name:
        st.error("未选择标签")
        back_to_list()
        return
    
    page_header(f"编辑标签: {st.session_state.current_tag_name}", "编辑标签名称")
    
    # 返回按钮
    if st.button("返回列表", key="btn_back_edit"):
        back_to_list()
    
    # 编辑标签表单
    with st.form("编辑标签"):
        name = st.text_input("标签名称", value=st.session_state.current_tag_name)
        submitted = st.form_submit_button("更新")
        
        if submitted:
            if not name:
                st.error("标签名称不能为空")
                return
            
            # 更新标签
            try:
                client = DifyClient.get_connection()
                with loading_spinner("正在更新标签..."):
                    updated_tag = client.update_tag(st.session_state.current_tag_id, name)
                
                # 重置缓存
                reset_cache()
                
                # 显示成功消息
                success_message("标签更新成功！")
                
                # 延迟1秒，确保用户看到成功消息
                time.sleep(1)
                
                # 返回标签列表
                back_to_list()
            except Exception as e:
                st.error(f"更新标签失败: {str(e)}")

def show_delete_tag():
    """显示删除标签确认对话框"""
    if not st.session_state.current_tag_id:
        st.error("未选择标签")
        back_to_list()
        return
    
    # 获取标签名称
    tag = next((t for t in get_tags() if t['id'] == st.session_state.current_tag_id), None)
    if not tag:
        st.error("找不到选定的标签")
        back_to_list()
        return
    
    # 显示确认对话框
    confirmation_dialog(
        title=f"确认删除标签 '{tag['name']}'",
        message=f"此操作不可逆，标签将从所有关联的应用中移除。是否确认删除？",
        on_confirm=lambda: perform_delete(st.session_state.current_tag_id),
        on_cancel=back_to_list
    )

def perform_delete(tag_id):
    """执行删除标签操作"""
    try:
        client = DifyClient.get_connection()
        with loading_spinner("正在删除标签..."):
            client.delete_tag(tag_id)
        
        # 重置缓存
        reset_cache()
        
        # 显示成功消息
        success_message("标签删除成功！")
        
        # 延迟1秒，确保用户看到成功消息
        time.sleep(1)
        
        # 返回标签列表
        back_to_list()
    except Exception as e:
        st.error(f"删除标签失败: {str(e)}")

def show_tag_binding():
    """显示应用标签关联界面"""
    page_header("应用标签关联", "为应用添加或移除标签")
    
    # 返回按钮
    if st.button("返回列表", key="btn_back_binding"):
        back_to_list()
    
    # 获取应用和标签列表
    apps = get_apps()
    tags = get_tags()
    
    if not apps:
        st.warning("没有可用的应用")
        return
    
    if not tags:
        st.warning("没有可用的标签")
        return
    
    # 选择应用
    selected_app_id = app_selector(apps)
    if not selected_app_id:
        st.info("请选择一个应用")
        return
    
    # 获取选定应用
    app = next((a for a in apps if a['id'] == selected_app_id), None)
    if not app:
        st.error("找不到选定的应用")
        return
    
    st.subheader(f"应用: {app['name']} ({app['mode']})")
    
    # 获取应用当前的标签
    app_tags = app.get('tags', [])
    app_tag_ids = [tag['id'] for tag in app_tags]
    
    # 显示当前标签
    if app_tags:
        st.write("**当前标签**")
        tag_names = [tag['name'] for tag in app_tags]
        st.write(", ".join(tag_names))
    else:
        st.write("**当前标签**: 无")
    
    # 定义表格列配置
    columns = [
        {"field": "name", "title": "标签名称"},
        {"field": "binding_count", "title": "引用数量"}
    ]
    
    # 额外添加一列表示是否绑定
    for tag in tags:
        tag['is_bound'] = tag['id'] in app_tag_ids
    
    # 添加is_bound列到显示列表
    columns.append({"field": "is_bound", "title": "已关联"})
    
    # 显示数据表格
    st.write("**可用标签列表**")
    selected_tag_df = data_display(tags, columns, key="binding_tag_table")
    
    # 如果选中了标签，提供绑定/解绑操作
    if not selected_tag_df.empty:
        selected_tag_id = selected_tag_df.iloc[0]["_id"]
        selected_tag = next((t for t in tags if t['id'] == selected_tag_id), None)
        
        if selected_tag:
            st.divider()
            st.subheader(f"标签: {selected_tag['name']}")
            
            is_bound = selected_tag['is_bound']
            
            if is_bound:
                # 提供解绑按钮
                if st.button("解除关联", key="btn_unbind_tag"):
                    try:
                        client = DifyClient.get_connection()
                        with loading_spinner("正在解除标签关联..."):
                            client.unbind_tag_from_app(selected_app_id, selected_tag_id)
                        
                        # 显示成功消息
                        success_message("标签关联解除成功！")
                        
                        # 延迟1秒，确保用户看到成功消息
                        time.sleep(1)
                        
                        # 刷新页面
                        st.session_state.tag_view_mode = 'bind'
                        st.rerun()
                    except Exception as e:
                        st.error(f"解除标签关联失败: {str(e)}")
            else:
                # 提供绑定按钮
                if st.button("添加关联", key="btn_bind_tag"):
                    try:
                        client = DifyClient.get_connection()
                        with loading_spinner("正在添加标签关联..."):
                            client.bind_tag_to_app(selected_app_id, selected_tag_id)
                        
                        # 显示成功消息
                        success_message("标签关联添加成功！")
                        
                        # 延迟1秒，确保用户看到成功消息
                        time.sleep(1)
                        
                        # 刷新页面
                        st.session_state.tag_view_mode = 'bind'
                        st.rerun()
                    except Exception as e:
                        st.error(f"添加标签关联失败: {str(e)}")

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
    if st.session_state.tag_view_mode == 'list':
        show_tag_list()
    elif st.session_state.tag_view_mode == 'create':
        show_create_tag()
    elif st.session_state.tag_view_mode == 'edit':
        show_edit_tag()
    elif st.session_state.tag_view_mode == 'delete':
        show_delete_tag()
    elif st.session_state.tag_view_mode == 'bind':
        show_tag_binding()
    else:
        st.error("未知的视图模式")
        back_to_list()

if __name__ == "__main__":
    main() 
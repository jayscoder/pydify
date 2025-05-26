"""
Dify管理面板 - 站点管理页面

提供Dify站点的增删改查功能，支持多站点管理和切换
"""

import os
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

# 添加当前目录到Python路径
current_dir = Path(__file__).parent.parent
sys.path.append(str(current_dir))

# 导入工具类和模型
from models import Site, create_tables, db
from utils.dify_client import DifyClient
from utils.ui_components import (
    action_bar,
    data_display,
    error_placeholder,
    page_header,
    success_message,
)

# 创建数据库表（如果不存在）
create_tables()

# 设置页面配置
st.set_page_config(
    page_title="Dify站点管理",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="expanded",
)


def fetch_sites():
    """获取所有站点列表"""
    try:
        return list(Site.select().dicts())
    except Exception as e:
        st.error(f"获取站点列表失败: {str(e)}")
        return []


def save_site(
    name, base_url, email, password, description="", is_default=False, site_id=None
):
    """
    保存站点信息（新增或更新）

    Args:
        name: 站点名称
        base_url: 站点URL
        email: 登录邮箱
        password: 登录密码
        description: 站点描述
        is_default: 是否为默认站点
        site_id: 站点ID（更新时使用）

    Returns:
        bool: 是否保存成功
    """
    try:
        with db.atomic():
            # 如果设置为默认站点，先将所有站点的is_default设为False
            if is_default:
                Site.update(is_default=False).execute()

            if site_id:  # 更新现有站点
                site = Site.get_by_id(site_id)
                site.name = name
                site.base_url = base_url
                site.email = email
                site.password = password
                site.description = description
                site.is_default = is_default
                site.save()
            else:  # 创建新站点
                Site.create(
                    name=name,
                    base_url=base_url,
                    email=email,
                    password=password,
                    description=description,
                    is_default=is_default,
                )
        return True
    except Exception as e:
        st.error(f"保存站点失败: {str(e)}")
        return False


def delete_site(site_id):
    """
    删除站点

    Args:
        site_id: 要删除的站点ID

    Returns:
        bool: 是否删除成功
    """
    try:
        site = Site.get_by_id(site_id)

        # 如果删除的是默认站点，需要设置另一个站点为默认
        if site.is_default:
            # 查找是否有其他站点可以设为默认
            other_sites = Site.select().where(Site.id != site_id)
            if other_sites.exists():
                # 将第一个找到的其他站点设为默认
                other_site = other_sites.get()
                other_site.is_default = True
                other_site.save()

        # 删除站点
        site.delete_instance()
        return True
    except Exception as e:
        st.error(f"删除站点失败: {str(e)}")
        return False


def set_default_site(site_id):
    """
    设置默认站点

    Args:
        site_id: 要设为默认的站点ID

    Returns:
        bool: 是否设置成功
    """
    try:
        with db.atomic():
            # 先将所有站点的is_default设为False
            Site.update(is_default=False).execute()

            # 将指定站点设为默认
            site = Site.get_by_id(site_id)
            site.is_default = True
            site.save()
        return True
    except Exception as e:
        st.error(f"设置默认站点失败: {str(e)}")
        return False


def connect_site(site_id):
    """
    连接到指定站点

    Args:
        site_id: 要连接的站点ID

    Returns:
        bool: 是否连接成功
    """
    try:
        site = Site.get_by_id(site_id)
        with st.spinner(f"正在连接到站点 {site.name}..."):
            if DifyClient.connect(
                site.base_url, site.email, site.password, site.id, site.name
            ):
                success_message(f"成功连接到站点: {site.name}")
                return True
    except Exception as e:
        st.error(f"连接站点失败: {str(e)}")
    return False


@st.dialog("站点", width="large")
def show_site_form_dialog(site_id=None):
    """
    显示站点表单（新增或编辑）
    """
    show_site_form(site_id)


def show_site_form(site_id=None):
    """
    显示站点表单（新增或编辑）

    Args:
        site_id: 要编辑的站点ID，为None时表示新增
    """
    # 获取要编辑的站点信息
    site_data = {
        "name": "",
        "base_url": "",
        "email": "",
        "password": "",
        "description": "",
        "is_default": False,
    }

    if site_id:
        try:
            site = Site.get_by_id(site_id)
            site_data = {
                "name": site.name,
                "base_url": site.base_url,
                "email": site.email,
                "password": site.password,
                "description": site.description or "",
                "is_default": site.is_default,
            }
        except Exception as e:
            st.error(f"获取站点信息失败: {str(e)}")
            return

    # 显示表单
    with st.form(key="site_form"):
        name = st.text_input(
            "站点名称", value=site_data["name"], placeholder="例如: 生产环境"
        )
        base_url = st.text_input(
            "站点URL",
            value=site_data["base_url"],
            placeholder="例如: http://example.com:11080",
        )

        # 分两列显示邮箱和密码
        col1, col2 = st.columns(2)
        with col1:
            email = st.text_input(
                "登录邮箱",
                value=site_data["email"],
                placeholder="例如: admin@example.com",
            )
        with col2:
            password = st.text_input(
                "登录密码", value=site_data["password"], type="password"
            )

        description = st.text_area(
            "站点描述(可选)",
            value=site_data["description"],
            placeholder="输入站点的描述信息",
        )

        is_default = st.checkbox(
            "设为默认站点",
            value=site_data["is_default"],
            help="默认站点将在启动时自动连接",
        )

        # 测试连接和保存按钮
        col1, col2, col3 = st.columns(3)
        with col1:
            test_connection = st.form_submit_button("测试连接")
        with col2:
            submit = st.form_submit_button("保存")

        with col3:
            if site_id:
                delete = st.form_submit_button("删除")
                if delete:
                    if delete_site(site_id):
                        st.success("站点删除成功！")
                        st.rerun()

        # 处理测试连接请求
        if test_connection and base_url and email and password:
            with st.spinner("正在测试连接..."):
                success = DifyClient.test_connect(base_url, email, password)
                if success:
                    st.success("连接成功！")
                else:
                    st.error("连接失败，请检查连接信息")

        # 处理保存请求
        if submit:
            if not name or not base_url or not email or not password:
                st.error("请填写必填字段")
            else:
                if save_site(
                    name, base_url, email, password, description, is_default, site_id
                ):
                    st.success("站点保存成功！")
                    st.rerun()


def main():
    """主函数"""
    # 页面标题
    page_header("Dify站点管理", "管理和切换不同的Dify站点连接")

    # 获取站点列表
    sites = fetch_sites()

    # 操作按钮区域
    with st.container():
        actions = [
            {
                "label": "添加站点",
                "key": "add_site",
                "color": "primary",
                "on_click": lambda: show_site_form_dialog(),
            }
        ]

        action_bar(actions)

    # 站点表格展示 - 不使用on_select参数，避免嵌套对话框
    selected_row = data_display(
        sites,
        [
            {"field": "id", "title": "id"},
            {"field": "name", "title": "站点名称"},
            {"field": "base_url", "title": "站点URL"},
            {"field": "email", "title": "登录邮箱"},
            {"field": "is_default", "title": "默认站点"},
            {"field": "description", "title": "站点描述"},
        ],
        key="sites_table",
    )

    # 如果有选中行，显示详情对话框
    if not selected_row.empty:
        site_id = selected_row.iloc[0]["id"]
        show_site_form_dialog(site_id)


if __name__ == "__main__":
    main()

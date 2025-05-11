import streamlit as st
import sys
from pathlib import Path
import json
import pandas as pd

# 添加当前目录到 Python 路径
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))

st.title("Dify Panel")

base_url = st.text_input("请输入基础URL", type="default", value="http://sandanapp.com:38080")
account = st.text_input("请输入账号", type="default", value="admin@bohn.com")
password = st.text_input("请输入密码", type="password", value="agentsgo123")

from pydify.site import DifySite

try:
    site_handler = DifySite(base_url, account, password)
    st.write("登录成功")
except Exception as e:
    st.error(f"登录失败: {e}")

tabs = st.tabs(["应用列表", "应用详情", '工具提供者'])

with tabs[0]:
    apps = site_handler.fetch_all_apps()
    st.write(apps)

with tabs[1]:
    app_id = st.text_input("请输入应用ID", type="default", value="")
    if app_id:
        app = site_handler.fetch_app(app_id)
        st.write(app)

with tabs[2]:
    providers = site_handler.fetch_tool_providers()
    st.write(providers)





"""
配置文件
"""

import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATABASE_PATH = os.path.join(BASE_DIR, "database.db")

class Pages:
    HOME = 'app.py'
    
    SITE_MANAGEMENT = "pages/1_站点管理.py"
    API_KEY_MANAGEMENT = "pages/2_API密钥管理.py"
    APP_MANAGEMENT = "pages/3_应用管理.py"
    TAG_MANAGEMENT = "pages/4_标签管理.py"
    TOOL_MANAGEMENT = "pages/5_工具管理.py"

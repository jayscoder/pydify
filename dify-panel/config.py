"""
Dify Panel 配置文件
"""
import os
from pathlib import Path

# 项目根目录
BASE_DIR = Path(__file__).parent

# 数据库配置
DATABASE_PATH = os.path.join(BASE_DIR, 'dify_panel.db')

# 应用配置
APP_NAME = "Dify 管理平台"
APP_VERSION = "1.0.0"

# 服务器配置
SERVER_HOST = "127.0.0.1"
SERVER_PORT = 8080

# 调试模式
DEBUG = True


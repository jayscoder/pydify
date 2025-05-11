#!/usr/bin/env python
"""
Dify Panel 启动脚本
"""
import os
import sys
from pathlib import Path

# 添加当前目录到 Python 路径
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))

def main():
    """启动 Dify Panel"""
    print("正在启动 Dify Panel...")
    
    # 初始化数据库
    from models import initialize_database
    initialize_database()
    
    # 启动应用
    from app import app
    from config import SERVER_HOST, SERVER_PORT, DEBUG
    
    print(f"应用将在 http://{SERVER_HOST}:{SERVER_PORT} 启动")
    app.launch(
        server_name=SERVER_HOST, 
        server_port=SERVER_PORT,
        debug=DEBUG,
        show_error=True,
        prevent_thread_lock=True,
        quiet=False
    )

if __name__ == "__main__":
    main() 
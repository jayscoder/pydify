#!/bin/bash
# Dify管理面板启动脚本

# 显示帮助信息
show_help() {
    echo "Dify管理面板启动脚本"
    echo "用法: ./run.sh [选项]"
    echo "选项:"
    echo "  -h, --help           显示此帮助信息"
    echo "  --port PORT          设置Streamlit应用端口(默认8501)"
    echo
    echo "示例:"
    echo "  ./run.sh --port 8888"
}

# 默认端口
PORT=8501

# 解析命令行参数
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        --port)
            PORT="$2"
            shift 2
            ;;
        *)
            echo "未知选项: $1"
            show_help
            exit 1
            ;;
    esac
done

# 显示当前配置
echo "Dify管理面板启动配置:"
echo "端口: $PORT"
echo "正在启动应用..."

# 启动Streamlit应用
streamlit run app.py --server.port $PORT 
#!/bin/bash
# 构建和测试Pydify包的脚本

set -e  # 遇到错误立即退出

echo "=== 清理旧的构建文件 ==="
rm -rf build/ dist/ *.egg-info/

echo "=== 安装开发依赖 ==="
pip install -e ".[dev]"

echo "=== 运行代码格式化 ==="
black .
isort .

echo "=== 运行测试 ==="
pytest

echo "=== 构建包 ==="
pip install build
python -m build

echo "=== 检查包 ==="
pip install twine
twine check dist/*

echo "=== 完成! ==="
echo "如果要发布到PyPI，请运行:"
echo "twine upload dist/*"
echo "或者测试发布到TestPyPI:"
echo "twine upload --repository-url https://test.pypi.org/legacy/ dist/*" 
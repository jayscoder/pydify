import os

import setuptools

# 优先读取README.rst，如果不存在则读取README.md
# readme_file = "README.rst" if os.path.exists("README.rst") else "README.md"
readme_file = "README.md"
with open(readme_file, "r", encoding="utf-8") as fh:
    long_description = fh.read()

# 根据文件扩展名确定内容类型
long_description_content_type = (
    "text/x-rst" if readme_file.endswith(".rst") else "text/markdown"
)

# 定义项目依赖
install_requires = [
    "requests>=2.25.0",
]

# 可选依赖
extras_require = {
    "dev": [
        "black",
        "isort",
        "pytest",
        "pytest-cov",
    ],
    "examples": [
        "Pillow>=8.0.0",  # 用于示例中的图像处理
    ],
}

setuptools.setup(
    name="pydify",
    version="0.1.4",
    author="Dify SDK Team",
    author_email="example@domain.com",
    description="A Python SDK for interacting with Dify API",
    long_description=long_description,
    long_description_content_type=long_description_content_type,
    url="https://github.com/jayscoder/pydify",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.7",
    install_requires=install_requires,
    extras_require=extras_require,
)

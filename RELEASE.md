# 发布指南

本文档提供了如何发布 Pydify 包到 PyPI 的指南。

## 准备发布

1. 确保所有测试通过：

   ```bash
   pytest
   ```

2. 更新版本号：

   - 在`pydify/__init__.py`中更新`__version__`
   - 在`setup.py`中更新`version`

3. 更新 CHANGELOG.md（如果有）

## 构建包

```bash
# 安装构建工具
pip install --upgrade build

# 构建包
python -m build
```

这将在`dist/`目录下创建源代码分发包（.tar.gz）和轮子分发包（.whl）。

## 检查包

```bash
# 安装twine
pip install --upgrade twine

# 检查包
twine check dist/*
```

## 测试发布到 TestPyPI（可选）

```bash
# 上传到TestPyPI
twine upload --repository-url https://test.pypi.org/legacy/ dist/*

# 从TestPyPI安装测试
pip install --index-url https://test.pypi.org/simple/ pydify
```

## 发布到 PyPI

```bash
# 上传到PyPI
twine upload dist/*
```

## 创建 GitHub 发布

1. 在 GitHub 上创建一个新的发布
2. 标记版本号（例如 v0.1.0）
3. 添加发布说明
4. 发布

## 发布后

1. 安装发布的包并进行验证：

   ```bash
   pip install pydify
   python test_install.py
   ```

2. 更新文档（如果有）

3. 通知用户新版本发布

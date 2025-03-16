# Pydify 发布指南

## 已完成的工作

1. **项目结构设置**

   - 创建了正确的包目录结构 (`pydify/`)
   - 添加了必要的包元数据文件 (`setup.py`, `pyproject.toml`, `MANIFEST.in`)
   - 创建了测试目录结构 (`tests/`)
   - 添加了版本信息 (`__version__`)

2. **文档**

   - 创建了详细的 `README.md` 和 `README.rst`
   - 添加了 `CHANGELOG.md` 记录版本变更
   - 添加了 `RELEASE.md` 提供发布流程指南
   - 创建了安装测试脚本 `test_install.py`

3. **CI/CD 配置**

   - 添加了 GitHub Actions 工作流配置
   - 创建了构建和测试脚本 `build_and_test.sh`

4. **包构建和测试**
   - 成功构建了源代码分发包和轮子分发包
   - 通过了 `twine check` 检查
   - 在开发模式下安装并测试了包

## 发布到 PyPI 的步骤

1. **准备发布**

   - 确保所有测试通过：`pytest`
   - 确认版本号正确：
     - `pydify/__init__.py` 中的 `__version__`
     - `setup.py` 中的 `version`
   - 更新 `CHANGELOG.md`

2. **构建包**

   ```bash
   # 清理旧的构建文件
   rm -rf build/ dist/ *.egg-info/

   # 构建包
   python -m build
   ```

3. **检查包**

   ```bash
   twine check dist/*
   ```

4. **发布到 TestPyPI（推荐先测试）**

   ```bash
   # 上传到 TestPyPI
   twine upload --repository-url https://test.pypi.org/legacy/ dist/*

   # 从 TestPyPI 安装测试
   pip install --index-url https://test.pypi.org/simple/ pydify
   ```

5. **发布到 PyPI**

   ```bash
   # 上传到 PyPI
   twine upload dist/*
   ```

6. **创建 GitHub 发布**
   - 在 GitHub 上创建一个新的发布
   - 标记版本号（例如 v0.1.0）
   - 添加发布说明
   - 发布

## 发布后检查

1. **安装和验证**

   ```bash
   pip install pydify
   python test_install.py
   ```

2. **更新文档**
   - 确保文档与最新版本一致

## 注意事项

- 首次发布到 PyPI 需要注册账号
- 确保包名 `pydify` 在 PyPI 上未被占用
- 如果需要更新包，请增加版本号后重新构建和上传
- 发布前确保所有敏感信息（如 API 密钥）已从代码中移除

# Dify 管理面板

一个用于管理 Dify 平台的 Streamlit 应用，提供直观的 Web 界面来管理应用、API 密钥、标签和工具。

## 功能概述

Dify 管理面板提供以下主要功能：

- **连接管理**: 连接到 Dify 平台并保持会话状态
- **应用管理**: 创建、查看、编辑、删除应用，导入/导出 DSL 配置
- **API 密钥管理**: 创建和删除应用的 API 密钥
- **标签管理**: 创建、编辑、删除标签，管理应用与标签的关联
- **工具管理**: 查看工具提供者和工具详情，管理工作流工具

## 项目结构

```
dify-panel/
├── app.py                # 主页，提供连接管理和功能导航
├── utils/                # 工具类目录
│   ├── dify_client.py    # Dify客户端封装
│   └── ui_components.py  # 可复用UI组件
├── pages/                # 功能页面目录
│   ├── app_management.py      # 应用管理页面
│   ├── api_key_management.py  # API密钥管理页面
│   ├── tag_management.py      # 标签管理页面
│   └── tool_management.py     # 工具管理页面
├── run.sh                # 启动脚本
├── README.md             # 项目说明文档
└── Streamlit使用文档.md   # Streamlit参考文档
```

## 界面特点

管理面板采用现代化的表格+选择+弹窗界面风格，具有以下特点：

- **数据表格化展示**: 所有列表数据使用表格形式展示，支持行选择
- **操作区集中管理**: 选择行后在操作区显示可执行的操作按钮
- **统一的交互模式**: 所有页面保持一致的交互体验 - 选择数据行后进行操作
- **响应式界面**: 适应不同屏幕尺寸，布局合理
- **清晰的导航路径**: 简化导航层次，减少页面跳转次数

## 安装和运行

### 前提条件

- Python 3.8 或更高版本
- 一个可访问的 Dify 平台实例

### 安装依赖

```bash
pip install streamlit requests python-dotenv
```

### 运行应用

#### 使用启动脚本

推荐使用提供的启动脚本，可以方便地设置连接信息：

```bash
# 使用命令行参数设置连接信息
./run.sh -u http://your-dify-url.com -e your-email@example.com -p your-password

# 或使用环境变量设置连接信息
DIFY_BASE_URL=http://your-dify-url.com DIFY_EMAIL=your-email@example.com DIFY_PASSWORD=your-password ./run.sh
```

启动脚本支持的参数：

- `-h, --help`: 显示帮助信息
- `-u, --url URL`: 设置 Dify 平台 URL
- `-e, --email EMAIL`: 设置登录邮箱
- `-p, --password PWD`: 设置登录密码
- `--port PORT`: 设置 Streamlit 应用端口(默认 8501)

#### 直接使用 Streamlit 命令

```bash
cd dify-panel
streamlit run app.py
```

应用将在浏览器中自动打开，默认地址为 http://localhost:8501

## 环境变量配置

应用支持通过环境变量设置默认的连接信息，这在容器化部署或持续运行环境中非常有用：

- `DIFY_BASE_URL`: Dify 平台的 URL (例如: http://example.com:11080)
- `DIFY_EMAIL`: 登录邮箱账号
- `DIFY_PASSWORD`: 登录密码

当设置了这些环境变量后，应用将在启动时自动尝试连接到 Dify 平台，无需手动输入连接信息。

### 使用 .env 文件

您也可以创建一个 `.env` 文件来存储这些环境变量：

```
DIFY_BASE_URL=http://your-dify-instance:11080
DIFY_EMAIL=your-email@example.com
DIFY_PASSWORD=your-password
```

应用会自动加载这个文件中的环境变量。

## 使用说明

### 1. 连接到 Dify 平台

1. 在首页填写 Dify 平台的 URL、邮箱和密码 (如果设置了环境变量，这些字段将自动填充)
2. 点击"连接"按钮
3. 连接成功后，您将看到平台概览和功能导航区域

### 2. 应用管理

- **查看应用列表**: 应用以表格形式展示
- **创建新应用**: 点击"创建新应用"按钮，填写应用名称、描述和选择应用类型
- **查看应用详情**: 在表格中选择应用，然后点击"查看详情"按钮
- **编辑应用**: 在表格中选择应用，然后点击"编辑应用"按钮
- **删除应用**: 在表格中选择应用，然后点击"删除应用"按钮
- **导出 DSL**: 在表格中选择应用，然后点击"导出 DSL"按钮
- **导入 DSL**: 点击"导入应用 DSL"按钮，上传 DSL 文件

### 3. API 密钥管理

- **选择应用**: 在下拉菜单中选择要管理 API 密钥的应用
- **查看 API 密钥**: 所有 API 密钥以表格形式展示
- **创建 API 密钥**: 点击"创建 API 密钥"按钮
- **删除 API 密钥**: 在表格中选择 API 密钥，然后点击"删除 API 密钥"按钮

### 4. 标签管理

- **查看标签列表**: 标签以表格形式展示
- **创建新标签**: 点击"创建新标签"按钮，填写标签名称
- **编辑标签**: 在表格中选择标签，然后点击"编辑标签"按钮
- **删除标签**: 在表格中选择标签，然后点击"删除标签"按钮
- **应用标签关联**: 点击"应用标签关联"按钮，选择应用和管理标签关联

### 5. 工具管理

- **查看工具提供者**: 工具提供者以表格形式展示
- **筛选工具提供者**: 使用多选框筛选不同类型的工具提供者
- **查看工具详情**: 在表格中选择工具提供者，然后点击"查看详情"按钮
- **工作流工具管理**:
  - 点击"管理工作流工具"按钮，查看所有工作流应用表格
  - 选择未发布的工作流应用，可以点击"发布为工具"按钮
  - 选择已发布的工作流应用，可以点击"查看工具详情"或"编辑工具"按钮
  - 工具编辑界面支持修改名称、描述、标识和参数描述

## 技术实现

- **前端**: 使用 Streamlit 构建用户界面，采用表格+选择+弹窗模式
- **后端**: 使用 Python 请求库与 Dify API 交互
- **状态管理**: 使用 Streamlit 的会话状态(session_state)管理应用状态
- **数据缓存**: 实现简单的缓存机制减少 API 请求
- **环境变量**: 支持从环境变量和.env 文件读取连接信息

## 注意事项

- API 密钥创建后只会显示一次，请妥善保存
- 删除应用或标签等操作无法撤销，请谨慎操作
- 长时间未操作可能导致会话过期，需要重新连接
- 为安全起见，建议不要在共享环境中使用包含密码的环境变量

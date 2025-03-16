# Pydify

Pydify 是一个用于与 Dify API 交互的 Python 客户端库。

## 关于 Dify

[Dify](https://github.com/langgenius/dify) 是一个开源的 LLM 应用开发平台，提供直观的界面将 AI 工作流、RAG 管道、代理能力、模型管理、可观察性功能等结合在一起，使您能够快速从原型转向生产环境。

Dify 平台主要特点：

- 🤖 **AI 工作流**：支持构建和部署复杂的 AI 应用流程
- 📚 **RAG 管道**：内置检索增强生成能力，轻松连接到您的数据
- 🧠 **代理能力**：支持创建自动化智能代理
- 🔄 **模型管理**：集成多种 LLM 模型（OpenAI、Anthropic、Gemini、LLaMA 等）
- 📊 **可观察性**：应用性能和使用情况的监控与分析

目前，Dify 在 GitHub 上拥有超过 82k 星标，是 LLM 应用开发领域备受欢迎的开源项目。

## 简介

Pydify 提供了一个简洁、易用的接口，用于访问 Dify 平台的各种功能，包括：

- 对话管理 (Chatbot/Agent/Chatflow)
- 文本生成 (Text Generation)
- 工作流执行 (Workflow)
- 文件处理
- 多模态功能 (语音转文字、文字转语音)
- 会话管理
- 应用信息查询

## 安装

```bash
pip install pydify
```

## 快速开始

### 创建客户端

有两种方式创建 pydify 客户端：

```python
# 方式一：直接创建 DifyClient 实例
from pydify import DifyClient

client = DifyClient(
    api_key="your_api_key_here",
    base_url="https://api.dify.ai/v1"  # 可选，默认为 https://api.dify.ai/v1
)

# 方式二：使用便捷函数创建（支持从环境变量读取配置）
from pydify import create_client

# 从环境变量 DIFY_API_KEY 和 DIFY_API_BASE_URL 读取
client = create_client()

# 或者直接提供参数
client = create_client(api_key="your_api_key_here")
```

### 基本用法示例

#### 1. 发送对话消息

```python
# 阻塞式响应
response = client.chat.create_message(
    query="你好，请介绍一下自己",
    user="user_123",
    response_mode="blocking"
)
print(response.data)

# 流式响应
stream = client.chat.create_message(
    query="讲一个故事",
    user="user_123",
    response_mode="streaming"
)

# 方式一：逐个事件处理
for event in stream:
    if event.get("type") == "message":
        print(event.get("answer", ""), end="", flush=True)

# 方式二：收集完整响应
full_text = stream.collect_response()
print(f"\n完整回答: {full_text}")
```

#### 2. 执行文本生成任务

```python
response = client.completion.create_completion(
    inputs={"query": "写一篇关于人工智能的短文"},
    user="user_123",
    response_mode="streaming"
)

for event in response:
    if event.get("type") == "message":
        print(event.get("answer", ""), end="", flush=True)
```

#### 3. 执行工作流

```python
response = client.workflow.run_workflow(
    inputs={"query": "分析这段文字的情感"},
    user="user_123"
)

for event in response:
    print(event)
```

#### 4. 文件上传

```python
# 上传本地文件
response = client.file.upload(
    file="/path/to/document.pdf",
    user="user_123"
)
file_id = response.data.get("id")

# 或上传文件对象
with open("/path/to/image.jpg", "rb") as f:
    response = client.file.upload(
        file=f,
        user="user_123",
        filename="image.jpg"
    )
```

#### 5. 多模态功能

```python
# 语音转文字
response = client.multimodal.audio_to_text(
    file="/path/to/audio.mp3",
    user="user_123"
)
text = response.data.get("text")
print(f"转写结果: {text}")

# 文字转语音
audio_data = client.multimodal.text_to_audio(
    text="这是一段测试文本",
    user="user_123"
)

# 保存音频到本地
with open("output.wav", "wb") as f:
    f.write(audio_data)
```

#### 6. 会话管理

```python
# 获取会话列表
conversations = client.conversation.list_conversations(user="user_123")
print(conversations.data)

# 删除会话
client.conversation.delete_conversation(
    conversation_id="conv_123",
    user="user_123"
)

# 重命名会话
client.conversation.rename_conversation(
    conversation_id="conv_123",
    name="新会话名称",
    user="user_123"
)
```

#### 7. 获取应用信息

```python
# 应用基本信息
info = client.info.get_app_info()
print(f"应用名称: {info.data.get('name')}")

# 应用参数
params = client.info.get_parameters()
print(params.data)

# 元数据
meta = client.info.get_meta()
print(meta.data)
```

## 异常处理

pydify 定义了几种异常类型用于处理不同错误情况：

```python
from pydify import DifyClient, DifyRequestError, DifyServerError, DifyAuthError

try:
    client = DifyClient("invalid_api_key")
    response = client.chat.create_message(
        query="你好",
        user="user_123"
    )
except DifyAuthError as e:
    print(f"认证错误: {e.message}")
except DifyRequestError as e:
    print(f"请求错误: {e.message}, 状态码: {e.status_code}")
except DifyServerError as e:
    print(f"服务器错误: {e.message}")
```

## 配置

### 环境变量

为了便于开发和测试，pydify 支持从环境变量加载配置：

- `DIFY_API_KEY`: API 密钥
- `DIFY_API_BASE_URL`: API 基础 URL (默认为 "https://api.dify.ai/v1")

您可以在项目根目录创建一个 `.env` 文件来设置这些变量：

```
DIFY_API_KEY=your_api_key_here
DIFY_API_BASE_URL=https://api.dify.ai/v1
```

> **注意**: 请确保将 `.env` 文件添加到 `.gitignore` 中，避免将敏感信息提交到版本控制系统。

## 运行测试

pydify 包含了单元测试和集成测试。

### 准备工作

1. 复制 `.env.example` 文件为 `.env`，并更新其中的 API 密钥：

```bash
cp .env.example .env
# 编辑 .env 文件，设置 DIFY_API_KEY
```

2. 安装测试依赖：

```bash
pip install -r tests/requirements_test.txt
```

### 运行测试

使用以下命令运行测试：

```bash
# 运行所有测试
python tests/run_tests.py

# 只运行单元测试（不需要有效的 API 密钥）
python tests/run_tests.py unit

# 只运行集成测试（需要有效的 API 密钥）
python tests/run_tests.py integration
```

## 完整 API 文档

请查看 [API 文档](https://github.com/yourusername/pydify/docs) 以获取更详细的 API 使用说明。

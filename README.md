# Pydify

Pydify 是一个用于与 Dify API 交互的 Python 客户端库。它提供了两个主要的客户端类：

- `DifyClient`：用于与原始 Dify API 交互
- `DifyChatClient`：用于与聊天 API 交互，支持标准的对话模型应用

## 安装

```bash
# 通过 pip 安装
pip install pydify
```

## 功能特点

### DifyClient 主要功能：

- 执行工作流（阻塞模式和流式模式）
- 异步执行工作流
- 上传文件
- 获取工作流状态
- 停止工作流执行
- 获取应用信息和参数

### DifyChatClient 新增功能：

- 发送聊天消息（阻塞模式和流式模式）
- 异步发送聊天消息
- 文件上传（支持图片、音频等）
- 停止聊天响应
- 消息反馈（点赞/点踩）
- 获取建议问题
- 会话管理（获取列表、获取历史消息、删除会话、重命名）
- 语音转文字、文字转语音
- 获取应用信息、参数和元信息

## 基本用法

### 使用 DifyClient

```python
from pydify import DifyClient, ResponseMode

# 初始化客户端
api_key = "your_api_key_here"
client = DifyClient(api_key, "https://api.dify.ai/v1")

# 阻塞模式执行工作流
result = client.run_workflow(
    inputs={"query": "你好，请介绍一下自己"},
    response_mode=ResponseMode.BLOCKING,
    user="test_user_123"
)
print("执行结果:", result)

# 流式模式执行工作流
stream = client.run_workflow(
    inputs={"query": "给我讲个故事"},
    response_mode=ResponseMode.STREAMING,
    user="test_user_123"
)

# 处理流式响应
for line in stream:
    if line.startswith('data: '):
        data = line[6:]  # 移除 'data: ' 前缀
        try:
            event_data = json.loads(data)
            print(f"事件: {event_data.get('event', 'unknown')}")
        except json.JSONDecodeError:
            print(f"解析事件数据失败: {data}")
```

### 使用 DifyChatClient

```python
from pydify import DifyChatClient, ResponseMode, MessageRating

# 初始化聊天客户端
api_key = "your_api_key_here"
chat_client = DifyChatClient(api_key, "http://sandanapp.com/v1")

# 发送聊天消息（阻塞模式）
result = chat_client.send_chat_message(
    query="你好，请介绍一下自己",
    response_mode=ResponseMode.BLOCKING,
    user="chat_user_123"
)
print("聊天回复:", result)

# 获取会话列表
conversations = chat_client.get_conversations(
    user="chat_user_123",
    limit=10
)
print("会话列表:", conversations)

# 上传文件
file_result = chat_client.upload_file(
    file_path="example.png",
    user="chat_user_123"
)
file_id = file_result.get("id")

# 发送带图片的消息
result = chat_client.send_chat_message(
    query="这张图片是什么?",
    files=[chat_client.create_file_input(file_id, "image", "local_file")],
    user="chat_user_123"
)
```

### 异步用法

```python
import asyncio
from pydify import DifyClient, DifyChatClient, ResponseMode

async def run_async_example():
    api_key = "your_api_key_here"
    client = DifyChatClient(api_key)

    # 定义回调函数
    async def event_callback(event_data):
        print(f"收到事件: {event_data.get('event', 'unknown')}")

        if event_data.get('event') == 'message_end':
            print("聊天结束:", event_data)

    # 异步发送聊天消息
    await client.send_chat_message_async(
        query="异步测试消息",
        response_mode=ResponseMode.STREAMING,
        user="async_user_123",
        callback=event_callback
    )

    # 异步上传文件
    file_result = await client.upload_file_async(
        file_path="example.png",
        user="async_user_123"
    )
    print("文件上传结果:", file_result)

# 运行异步示例
asyncio.run(run_async_example())
```

## 详细 API 文档

### DifyChatClient API

#### 发送聊天消息

```python
# 阻塞模式
result = chat_client.send_chat_message(
    query="你好",
    inputs={"name": "张三"},  # 可选，变量输入
    response_mode=ResponseMode.BLOCKING,
    user="user_123",
    conversation_id="conv_id",  # 可选，继续已有对话
    files=[file_input],  # 可选，文件列表
    auto_generate_name=True  # 可选，自动生成对话名称
)

# 流式模式
stream = chat_client.send_chat_message(
    query="给我讲个故事",
    response_mode=ResponseMode.STREAMING,
    user="user_123"
)

for event in stream:
    print(f"事件类型: {event.get('event')}")
    if event.get('event') == 'message':
        print(f"内容: {event.get('answer')}")
    elif event.get('event') == 'message_end':
        print("对话结束")
```

#### 文件处理

```python
# 上传文件
file_result = chat_client.upload_file(
    file_path="example.png",
    user="user_123"
)
file_id = file_result.get("id")

# 上传二进制内容
with open("example.png", "rb") as f:
    file_content = f.read()

file_result = chat_client.upload_file_content(
    file_content=io.BytesIO(file_content),
    filename="example.png",
    user="user_123",
    mime_type="image/png"  # 可选
)

# 创建文件输入参数
file_input = chat_client.create_file_input(
    file_id=file_id,
    file_type="image",
    transfer_method="local_file"
)

# 创建URL输入参数
url_input = chat_client.create_url_input(
    url="https://example.com/image.jpg",
    file_type="image",
    transfer_method="remote_url"
)
```

#### 会话管理

```python
# 获取会话列表
conversations = chat_client.get_conversations(
    user="user_123",
    limit=20,
    last_id="last_conv_id",  # 可选
    sort_by="-updated_at"  # 可选
)

# 获取会话消息历史
messages = chat_client.get_conversation_messages(
    conversation_id="conv_id",
    user="user_123",
    first_id="first_message_id",  # 可选
    limit=20  # 可选
)

# 删除会话
result = chat_client.delete_conversation(
    conversation_id="conv_id",
    user="user_123"
)

# 重命名会话
result = chat_client.rename_conversation(
    conversation_id="conv_id",
    user="user_123",
    name="新会话名称",  # 可选
    auto_generate=False  # 可选
)
```

#### 消息反馈

```python
# 点赞消息
result = chat_client.send_message_feedback(
    message_id="msg_id",
    rating=MessageRating.LIKE,
    user="user_123",
    content="这条回复非常有用"  # 可选
)

# 点踩消息
result = chat_client.send_message_feedback(
    message_id="msg_id",
    rating=MessageRating.DISLIKE,
    user="user_123"
)

# 撤销反馈
result = chat_client.send_message_feedback(
    message_id="msg_id",
    rating=MessageRating.NONE,
    user="user_123"
)
```

#### 语音功能

```python
# 语音转文字
result = chat_client.audio_to_text(
    file_path="speech.mp3",
    user="user_123"
)
text = result.get("text")

# 文字转语音
audio_data = chat_client.text_to_audio(
    text="你好，世界！",
    user="user_123"
)

# 或通过消息ID转换
audio_data = chat_client.text_to_audio(
    message_id="msg_id",
    user="user_123"
)

# 保存音频
with open("output.wav", "wb") as f:
    f.write(audio_data)
```

#### 其他功能

```python
# 获取应用信息
app_info = chat_client.get_app_info()

# 获取应用参数
app_params = chat_client.get_app_parameters()

# 获取应用元信息
app_meta = chat_client.get_app_meta()

# 获取建议问题
suggestions = chat_client.get_suggested_questions(
    message_id="msg_id",
    user="user_123"
)

# 停止响应
result = chat_client.stop_chat_response(
    task_id="task_id",
    user="user_123"
)
```

## 错误处理

所有 API 错误都会抛出 `DifyApiError` 异常，包含状态码和错误消息：

```python
from pydify import DifyChatClient, DifyApiError

try:
    client = DifyChatClient("invalid_api_key")
    result = client.get_app_info()
except DifyApiError as e:
    print(f"API 错误: {e.status_code} - {e.message}")
```

## 开发与贡献

欢迎贡献代码或提出问题！请在 GitHub 上提交 Issue 或 Pull Request。

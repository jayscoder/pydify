# Pydify

Pydify 是一个用于与 Dify API 交互的 Python 客户端库。

[![PyPI version](https://badge.fury.io/py/pydify.svg)](https://badge.fury.io/py/pydify)
[![Python Versions](https://img.shields.io/pypi/pyversions/pydify.svg)](https://pypi.org/project/pydify)
[![Downloads](https://pepy.tech/badge/pydify)](https://pepy.tech/project/pydify)

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

- 💬 **Chatbot 聊天助手**：多轮对话、会话管理、消息反馈、多模态交互等
- 🔄 **Workflow 工作流应用**：执行工作流、处理流式响应、文件上传等
- 🤖 **Agent 对话型应用**：迭代式规划推理、自主工具调用，直至完成任务目标的智能助手
- 📝 **Text Generation 文本生成应用**：单轮文本生成，适合翻译、文章写作、总结等 AI 任务
- 🔧 **DifySite 管理工具**：自动化管理 Dify 平台的应用、API 密钥等

## 安装

```bash
pip install pydify
```

## 使用方法

### ChatbotClient

ChatbotClient 用于与 Dify 的 Chatbot 应用交互。Chatbot 对话应用支持会话持久化，可将之前的聊天记录作为上下文进行回答，适用于聊天/客服 AI 等场景。

#### 基本用法

```python
from pydify import ChatbotClient

# 初始化客户端
client = ChatbotClient(
    api_key="your_dify_api_key",
    base_url="https://your-dify-instance.com/v1"  # 可选，默认使用 DIFY_BASE_URL 环境变量
)

# 获取应用信息
app_info = client.get_app_info()
print(f"应用名称: {app_info['name']}")

# 获取应用参数（开场白、推荐问题等）
params = client.get_parameters()
print(f"开场白: {params.get('opening_statement', '')}")

# 发送消息（阻塞模式）
response = client.send_message(
    query="你好，请介绍一下自己",
    user="user_123",  # 用户唯一标识
    response_mode="blocking"  # 阻塞模式，等待回复完成
)
print(f"AI回答: {response['answer']}")
print(f"会话ID: {response['conversation_id']}")
```

#### 流式响应处理

```python
# 流式模式发送消息
stream = client.send_message(
    query="请写一首关于春天的诗",
    user="user_123",
    response_mode="streaming"  # 流式模式，实时获取回复内容
)

# 处理流式响应
for chunk in stream:
    event = chunk.get("event")
    if event == "message":
        print(chunk.get("answer", ""), end="", flush=True)
    elif event == "message_end":
        print("\n\n消息回复完成！")
        if "metadata" in chunk and "usage" in chunk["metadata"]:
            usage = chunk["metadata"]["usage"]
            print(f"Token使用: {usage}")
```

#### 多轮对话

```python
# 第一轮对话
response1 = client.send_message(
    query="你能帮我写一个Python函数吗？",
    user="user_123",
    response_mode="blocking"
)
conversation_id = response1["conversation_id"]
print(f"AI: {response1['answer']}")

# 第二轮对话（基于之前的上下文）
response2 = client.send_message(
    query="这个函数需要实现什么功能？",
    user="user_123",
    conversation_id=conversation_id,  # 使用第一轮返回的会话ID
    response_mode="blocking"
)
print(f"AI: {response2['answer']}")
```

#### 消息反馈（点赞/点踩）

```python
# 对消息进行点赞
client.message_feedback(
    message_id="message_id_from_response",
    user="user_123",
    rating="like",  # "like"或"dislike"
    content="非常有用的回答，谢谢！"  # 可选
)

# 撤销反馈
client.message_feedback(
    message_id="message_id_from_response",
    user="user_123",
    rating=None  # 撤销反馈
)
```

#### 会话管理

```python
# 获取会话列表
conversations = client.get_conversations(
    user="user_123",
    limit=10  # 获取最近10条会话
)
for conv in conversations["data"]:
    print(f"会话ID: {conv['id']}, 名称: {conv['name']}")

# 获取会话历史消息
messages = client.get_messages(
    conversation_id="conversation_id",
    user="user_123",
    limit=20  # 获取最近20条消息
)
for msg in messages["data"]:
    sender = "用户" if "query" in msg else "AI"
    content = msg.get("query") if "query" in msg else msg.get("answer")
    print(f"{sender}: {content}")

# 重命名会话
client.rename_conversation(
    conversation_id="conversation_id",
    user="user_123",
    name="Python学习讨论"  # 手动指定名称
)
# 或自动生成名称
client.rename_conversation(
    conversation_id="conversation_id",
    user="user_123",
    auto_generate=True  # 自动生成名称
)

# 删除会话
client.delete_conversation(
    conversation_id="conversation_id",
    user="user_123"
)
```

#### 文件与多模态功能

```python
# 上传图片文件
file_result = client.upload_file(
    file_path="image.png",
    user="user_123"
)
file_id = file_result["id"]

# 发送带图片的消息
response = client.send_message(
    query="请描述这张图片的内容",
    user="user_123",
    files=[{
        "type": "image",
        "transfer_method": "local_file",
        "upload_file_id": file_id
    }],
    response_mode="blocking"
)
print(f"AI对图片的描述: {response['answer']}")
```

#### 语音功能

```python
# 语音转文字
speech_result = client.audio_to_text(
    file_path="speech.mp3",
    user="user_123"
)
print(f"识别出的文字: {speech_result['text']}")

# 文字转语音
# 从文本生成
audio_result = client.text_to_audio(
    user="user_123",
    text="这段文字将被转换为语音"
)

# 从消息ID生成
audio_result = client.text_to_audio(
    user="user_123",
    message_id="message_id_from_response"
)
```

#### 其他功能

```python
# 获取推荐问题
suggestions = client.get_suggested_questions(
    message_id="message_id_from_response",
    user="user_123"
)
for question in suggestions["data"]:
    print(f"推荐问题: {question}")

# 停止响应（针对流式模式）
client.stop_task(
    task_id="task_id_from_stream",
    user="user_123"
)
```

### AgentClient

AgentClient 用于与 Dify 的 Agent 应用交互。Agent 是能够迭代式规划推理、自主工具调用，直至完成任务目标的智能助手。

#### 基本用法

```python
from pydify import AgentClient
from pydify.agent import AgentEvent  # 导入事件类型

# 初始化客户端
client = AgentClient(
    api_key="your_dify_api_key",
    base_url="https://your-dify-instance.com/v1"  # 可选，默认使用 DIFY_BASE_URL 环境变量
)

# 获取应用信息
app_info = client.get_app_info()
print(f"应用名称: {app_info['name']}")

# 获取应用参数
params = client.get_parameters()
print(f"开场白: {params.get('opening_statement', '')}")

# 发送消息（Agent应用只支持流式模式）
stream = client.send_message(
    query="帮我搜索最近一周的股市行情，并分析趋势",
    user="user_123"  # 用户唯一标识
)

# 简单处理流式响应
for chunk in stream:
    event = chunk.get("event")
    if event == "agent_message":
        print(chunk.get("answer", ""), end="", flush=True)
    elif event == "agent_thought":
        print(f"\n[思考] {chunk.get('thought')}")
        print(f"[工具] {chunk.get('tool')}")
        print(f"[结果] {chunk.get('observation')}")
    elif event == "message_end":
        print("\n\n回答完成")
```

#### 流式响应处理

```python
# 发送消息
stream = client.send_message(
    query="帮我分析最近的经济数据，预测下个季度的趋势",
    user="user_123"
)

# 简单的事件处理
for chunk in stream:
    event = chunk.get("event")
    if event == AgentEvent.AGENT_MESSAGE:
        print(chunk.get("answer", ""), end="", flush=True)
    elif event == AgentEvent.AGENT_THOUGHT:
        print(f"\n\n[思考] {chunk.get('thought')}")
        print(f"[工具] {chunk.get('tool')}")
        print(f"[观察] {chunk.get('observation')}\n")
    elif event == AgentEvent.MESSAGE_END:
        print("\n\n回答完成！")
```

#### 多轮对话

```python
# 第一轮对话
stream1 = client.send_message(
    query="帮我找出最适合初学者的编程语言",
    user="user_123"
)
# 处理第一轮对话的响应...
conversation_id = None
for chunk in stream1:
    if chunk.get("event") == "message_end":
        conversation_id = chunk.get("conversation_id")

# 第二轮对话（基于之前的上下文）
if conversation_id:
    stream2 = client.send_message(
        query="我想学习你推荐的第一种语言，有什么好的学习资源？",
        user="user_123",
        conversation_id=conversation_id  # 使用第一轮返回的会话ID
    )
    # 处理第二轮对话的响应...
```

#### 会话管理

```python
# 获取会话列表
conversations = client.get_conversations(
    user="user_123",
    limit=5  # 获取最近5条会话
)

# 获取会话历史消息（包含Agent思考过程）
messages = client.get_messages(
    conversation_id="conversation_id",
    user="user_123"
)

# 重命名会话
client.rename_conversation(
    conversation_id="conversation_id",
    user="user_123",
    name="编程学习助手"
)

# 删除会话
client.delete_conversation(
    conversation_id="conversation_id",
    user="user_123"
)
```

#### 停止正在进行的任务

```python
# 停止响应
client.stop_task(
    task_id="task_id_from_stream",
    user="user_123"
)
```

### TextGenerationClient

TextGenerationClient 用于与 Dify 的 Text Generation 应用交互。Text Generation 应用无会话支持，适合用于翻译、文章写作、总结等 AI 任务。

#### 基本用法

```python
from pydify import TextGenerationClient
from pydify.text_generation import TextGenerationEvent  # 导入事件类型

# 初始化客户端
client = TextGenerationClient(
    api_key="your_dify_api_key",
    base_url="https://your-dify-instance.com/v1"  # 可选，默认使用 DIFY_BASE_URL 环境变量
)

# 获取应用信息
app_info = client.get_app_info()
print(f"应用名称: {app_info['name']}")

# 获取应用参数
params = client.get_parameters()
print(f"支持的功能: {params.get('features', [])}")

# 发送请求（阻塞模式）
response = client.completion(
    query="写一篇关于人工智能的短文，不少于300字",
    user="user_123",  # 用户唯一标识
    response_mode="blocking"  # 阻塞模式，等待生成完成
)
print(f"生成ID: {response['message_id']}")
print(f"生成内容: {response['answer']}")
```

#### 流式响应处理

```python
# 发送流式请求
stream = client.completion(
    query="请写一首关于春天的诗",
    user="user_123",
    response_mode="streaming"  # 流式模式，实时获取生成内容
)

# 处理流式响应
for chunk in stream:
    event = chunk.get("event")
    if event == TextGenerationEvent.MESSAGE:
        print(chunk.get("answer", ""), end="", flush=True)
    elif event == TextGenerationEvent.MESSAGE_END:
        print("\n\n生成完成！")
        if "metadata" in chunk and "usage" in chunk["metadata"]:
            usage = chunk["metadata"]["usage"]
            print(f"Token使用: {usage}")
```

#### 使用自定义输入

```python
# 假设应用定义了一些变量，如：主题(topic)、风格(style)、字数(word_count)
inputs = {
    "topic": "人工智能",        # 主题
    "style": "科普",           # 风格
    "word_count": 500          # 字数要求
}

# 发送请求，使用自定义inputs
response = client.completion(
    query="帮我写一篇文章",
    user="user_123",
    inputs=inputs,
    response_mode="blocking"
)
```

#### 文件与多模态功能

```python
# 上传图片文件
file_result = client.upload_file(
    file_path="image.png",
    user="user_123"
)
file_id = file_result["id"]

# 发送带图片的请求
response = client.completion(
    query="描述这张图片的内容",
    user="user_123",
    files=[{
        "type": "image",
        "transfer_method": "local_file",
        "upload_file_id": file_id
    }],
    response_mode="blocking"
)
print(f"图片描述: {response['answer']}")
```

#### 停止生成

```python
# 停止正在进行的生成任务
client.stop_task(
    task_id="task_id_from_stream",
    user="user_123"
)
```

### WorkflowClient

WorkflowClient 用于与 Dify 的 Workflow 应用交互。Workflow 应用无会话支持，专注于执行预定义的工作流程。

#### 基本用法

```python
from pydify import WorkflowClient
from pydify.workflow import WorkflowEvent  # 导入事件类型

# 初始化客户端
client = WorkflowClient(
    api_key="your_dify_api_key",
    base_url="https://your-dify-instance.com/v1"  # 可选，默认使用 DIFY_BASE_URL 环境变量
)

# 获取应用信息
app_info = client.get_app_info()
print(f"应用名称: {app_info['name']}")

# 准备输入参数
inputs = {
    "prompt": "请写一首关于人工智能的诗",
}

# 执行工作流（阻塞模式）
result = client.run(
    inputs=inputs,
    user="user_123",  # 用户标识
    response_mode="blocking",
    timeout=30,  # 超时时间(秒)
)

print("工作流执行结果:")
print(result)
```

#### 流式模式执行工作流

```python
# 流式执行工作流
stream = client.run(
    inputs={"prompt": "分析当前市场趋势"},
    user="user_123",
    response_mode="streaming"
)

# 处理流式响应
for chunk in stream:
    event = chunk.get("event")

    if event == WorkflowEvent.WORKFLOW_STARTED:
        print(f"工作流开始：{chunk['data']['id']}")

    elif event == WorkflowEvent.NODE_STARTED:
        print(f"节点开始：{chunk['data']['title']}")

    elif event == WorkflowEvent.NODE_FINISHED:
        node_data = chunk['data']
        print(f"节点完成：{node_data.get('id')}")
        if 'outputs' in node_data:
            print(f"  输出：{node_data['outputs']}")

    elif event == WorkflowEvent.WORKFLOW_FINISHED:
        print(f"工作流完成：{chunk['data']['id']}")
        if 'outputs' in chunk['data']:
            print(f"最终结果：{chunk['data']['outputs']}")
```

#### 文件上传与使用

```python
# 上传文件
file_result = client.upload_file("document.pdf", "user_123")
file_id = file_result["id"]

# 使用文件执行工作流
result = client.run(
    inputs={"prompt": "总结这个文档的内容"},
    user="user_123",
    response_mode="blocking",
    files=[{
        "type": "document",
        "transfer_method": "local_file",
        "upload_file_id": file_id
    }]
)
```

#### 停止正在执行的任务与获取日志

```python
# 停止任务
client.stop_task(task_id="task_id_from_stream", user="user_123")

# 获取工作流执行日志
logs = client.get_logs(limit=10)
for log in logs["data"]:
    print(f"工作流 {log['id']} 状态: {log['workflow_run']['status']}")
```

### DifySite 管理工具

DifySite 类提供了与 Dify 平台管理 API 的直接交互能力，用于自动化管理应用、API 密钥等后台任务。与其他客户端不同，DifySite 需要使用用户账户登录凭据而非 API 密钥。

#### 初始化与登录

```python
from pydify.site import DifySite, DifyAppMode

# 初始化DifySite实例（初始化时会自动登录并获取令牌）
site = DifySite(
    base_url="http://your-dify-instance.com",  # Dify平台地址
    email="your-email@example.com",            # 登录邮箱
    password="your-password"                   # 登录密码
)
# 登录成功后，site.access_token和site.refresh_token已自动填充
```

#### 应用管理

```python
# 获取所有应用
apps = site.fetch_apps(limit=10)  # 获取前10个应用
for app in apps['data']:
    print(f"应用: {app['name']} (ID: {app['id']}, 模式: {app['mode']})")

# 获取所有应用（自动处理分页）
all_apps = site.fetch_all_apps()
print(f"共有{len(all_apps)}个应用")

# 获取特定应用详情
app_details = site.fetch_app("your-app-id")
print(f"应用名称: {app_details['name']}")
print(f"应用模式: {app_details['mode']}")

# 创建新应用
new_app = site.create_app(
    name="测试应用",
    description="通过API创建的测试应用",
    mode=DifyAppMode.CHAT  # 聊天助手应用
)
print(f"创建成功! 应用ID: {new_app['id']}")

# 删除应用
site.delete_app("your-app-id")
```

#### DSL 配置导入导出

```python
# 导出应用DSL配置
dsl = site.fetch_app_dsl("your-app-id")

# 将DSL保存到文件
with open("app_backup.yaml", "w") as f:
    f.write(dsl)

# 导入应用DSL配置（创建新应用）
with open("app_backup.yaml", "r") as f:
    dsl_content = f.read()

imported_app = site.import_app_dsl(dsl_content)
print(f"导入成功! 新应用ID: {imported_app['id']}")

# 导入应用DSL配置（更新现有应用）
site.import_app_dsl(dsl_content, app_id="existing-app-id")
```

#### API 密钥管理

```python
# 获取应用的API密钥列表
api_keys = site.fetch_app_api_keys("your-app-id")
print(f"应用共有{len(api_keys)}个API密钥")

# 创建新的API密钥
new_key = site.create_app_api_key("your-app-id")
print(f"新API密钥: {new_key['token']}")

# 删除API密钥
site.delete_app_api_key("your-app-id", "api-key-id")
```

#### 其他功能

```python
# 在浏览器中打开应用
site.jump_to_app("your-app-id", DifyAppMode.CHAT)
```

## 贡献

欢迎贡献代码、报告问题或提出建议！请查看 [CONTRIBUTING.md](CONTRIBUTING.md) 了解更多详情。

## 许可证

本项目采用 MIT 许可证。详细信息请参阅 [LICENSE](LICENSE) 文件。

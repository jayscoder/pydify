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

- 💬 **Chatbot 聊天助手**：多轮对话、会话管理、消息反馈、多模态交互等
- 🔄 **Workflow 工作流应用**：执行工作流、处理流式响应、文件上传等
- 🤖 **Agent 对话型应用**：迭代式规划推理、自主工具调用，直至完成任务目标的智能助手
- 📝 **Text Generation 文本生成应用**：单轮文本生成，适合翻译、文章写作、总结等 AI 任务
- 🧩 **Chatflow 工作流编排对话型应用**：基于工作流编排的多轮对话，支持复杂流程定义，具有记忆功能

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
def on_message(chunk):
    print(chunk["answer"], end="", flush=True)  # 实时打印文本块

def on_message_end(chunk):
    print("\n\n消息回复完成！")
    # 获取令牌使用信息
    if "metadata" in chunk and "usage" in chunk["metadata"]:
        usage = chunk["metadata"]["usage"]
        print(f"Token使用: {usage}")

# 处理流式响应
result = client.process_streaming_response(
    stream,
    handle_message=on_message,
    handle_message_end=on_message_end
)
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
client.stop_response(
    task_id="task_id_from_stream",
    user="user_123"
)

# 获取应用Meta信息
meta_info = client.get_meta()
print(f"工具图标: {meta_info.get('tool_icons', {})}")
```

更多示例请参阅 [examples/chatbot_example.py](examples/chatbot_example.py)。

### AgentClient

AgentClient 用于与 Dify 的 Agent 应用交互。Agent 是能够迭代式规划推理、自主工具调用，直至完成任务目标的智能助手。

#### 基本用法

```python
from pydify import AgentClient

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

Agent 应用有特殊的事件类型，用于处理智能体的思考过程和工具调用：

```python
# 定义处理函数
def on_agent_message(chunk):
    print(chunk.get("answer", ""), end="", flush=True)

def on_agent_thought(chunk):
    print(f"\n\n[Agent思考] {chunk.get('position')}:")
    print(f"思考: {chunk.get('thought')}")
    print(f"工具: {chunk.get('tool')}")
    print(f"输入: {chunk.get('tool_input')}")
    print(f"观察: {chunk.get('observation')}\n")

def on_message_end(chunk):
    print("\n\n消息完成！")
    if "metadata" in chunk and "usage" in chunk["metadata"]:
        usage = chunk["metadata"]["usage"]
        print(f"Token使用: {usage}")

# 流式模式发送消息
stream = client.send_message(
    query="帮我分析最近的经济数据，预测下个季度的趋势",
    user="user_123"
)

# 处理流式响应
result = client.process_streaming_response(
    stream,
    handle_agent_message=on_agent_message,
    handle_agent_thought=on_agent_thought,
    handle_message_end=on_message_end
)

print(f"Agent思考步骤数: {len(result.get('agent_thoughts', []))}")
```

#### 多轮对话

```python
# 第一轮对话
stream1 = client.send_message(
    query="帮我找出最适合初学者的编程语言",
    user="user_123"
)
result1 = client.process_streaming_response(
    stream1,
    handle_agent_message=lambda chunk: print(chunk.get("answer", ""), end="")
)
conversation_id = result1["conversation_id"]

# 第二轮对话（基于之前的上下文）
stream2 = client.send_message(
    query="我想学习你推荐的第一种语言，有什么好的学习资源？",
    user="user_123",
    conversation_id=conversation_id  # 使用第一轮返回的会话ID
)
client.process_streaming_response(
    stream2,
    handle_agent_message=lambda chunk: print(chunk.get("answer", ""), end="")
)
```

#### 会话管理

Agent 应用与 Chatbot 一样支持会话管理功能：

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
for msg in messages["data"]:
    if "agent_thoughts" in msg:
        thoughts = msg["agent_thoughts"]
        print(f"Agent思考步骤: {len(thoughts)}个")
        for thought in thoughts:
            print(f"- 思考: {thought.get('thought')}")
            print(f"  工具: {thought.get('tool')}")

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

#### 图片分析功能

```python
# 上传图片文件
file_result = client.upload_file(
    file_path="chart.png",
    user="user_123"
)
file_id = file_result["id"]

# 发送带图片的消息，让Agent分析图片
stream = client.send_message(
    query="请分析这张图表，告诉我主要趋势",
    user="user_123",
    files=[{
        "type": "image",
        "transfer_method": "local_file",
        "upload_file_id": file_id
    }]
)

# 处理Agent对图片的分析
client.process_streaming_response(
    stream,
    handle_agent_message=lambda chunk: print(chunk.get("answer", ""), end="")
)
```

#### 反馈与推荐问题

```python
# 对消息进行反馈
client.message_feedback(
    message_id="message_id_from_response",
    user="user_123",
    rating="like",  # "like"或"dislike"
    content="Agent的分析非常深入，感谢！"
)

# 获取推荐问题
suggestions = client.get_suggested_questions(
    message_id="message_id_from_response",
    user="user_123"
)
```

#### 停止正在进行的任务

Agent 处理复杂任务可能需要较长时间，可以中途停止：

```python
# 停止响应
client.stop_response(
    task_id="task_id_from_stream",
    user="user_123"
)
```

更多示例请参阅 [examples/agent_example.py](examples/agent_example.py)。

### TextGenerationClient

TextGenerationClient 用于与 Dify 的 Text Generation 应用交互。Text Generation 应用无会话支持，适合用于翻译、文章写作、总结等 AI 任务。

#### 基本用法

```python
from pydify import TextGenerationClient

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
print(f"输入表单: {params.get('user_input_form', [])}")

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
# 处理函数
def on_message(chunk):
    print(chunk.get("answer", ""), end="", flush=True)

def on_message_end(chunk):
    print("\n\n生成完成！")
    if "metadata" in chunk and "usage" in chunk["metadata"]:
        usage = chunk["metadata"]["usage"]
        print(f"Token使用情况: 输入={usage.get('prompt_tokens', 0)}, "
              f"输出={usage.get('completion_tokens', 0)}, "
              f"总计={usage.get('total_tokens', 0)}")

# 发送流式请求
stream = client.completion(
    query="请写一首关于春天的诗",
    user="user_123",
    response_mode="streaming"  # 流式模式，实时获取生成内容
)

# 处理流式响应
result = client.process_streaming_response(
    stream,
    handle_message=on_message,
    handle_message_end=on_message_end
)
```

#### 使用自定义输入

```python
# 假设应用定义了一些变量，如：主题(topic)、风格(style)、字数(word_count)
inputs = {
    "query": "帮我写一篇文章",  # 基本查询
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

#### 专业任务示例

```python
# 翻译任务
translation_result = client.completion(
    query="将文本翻译成英文",
    user="user_123",
    inputs={
        "text_to_translate": "人工智能是模拟人类智能的科学与技术",
        "target_language": "english"
    },
    response_mode="blocking"
)

# 文本摘要任务
summary_result = client.completion(
    query="请对以下文本进行摘要",
    user="user_123",
    inputs={
        "text_to_summarize": "一段很长的文本...",
        "max_length": 150
    },
    response_mode="blocking"
)
```

#### 反馈功能

```python
# 对生成结果进行反馈
client.message_feedback(
    message_id="message_id_from_response",
    user="user_123",
    rating="like",  # "like"或"dislike"
    content="生成的文章非常符合要求，感谢！"  # 可选
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

#### 文字转语音

```python
# 从文本生成语音
audio_result = client.text_to_audio(
    user="user_123",
    text="这段文字将被转换为语音"
)

# 从生成结果ID生成语音
audio_result = client.text_to_audio(
    user="user_123",
    message_id="message_id_from_response"
)
```

#### 停止生成

```python
# 停止正在进行的生成任务
client.stop_completion(
    task_id="task_id_from_stream",
    user="user_123"
)
```

更多示例请参阅 [examples/text_generation_example.py](examples/text_generation_example.py)。

### ChatflowClient

ChatflowClient 用于与 Dify 的 Chatflow 应用交互。Chatflow 是基于工作流编排的对话型应用，适用于定义复杂流程的多轮对话场景，具有记忆功能。

#### 基本用法

```python
from pydify import ChatflowClient

# 初始化客户端
client = ChatflowClient(
    api_key="your_dify_api_key",
    base_url="https://your-dify-instance.com/v1"  # 可选，默认使用 DIFY_BASE_URL 环境变量
)

# 获取应用信息
app_info = client.get_app_info()
print(f"应用名称: {app_info['name']}")

# 获取应用参数
params = client.get_parameters()
print(f"开场白: {params.get('opening_statement', '')}")

# 发送消息（阻塞模式）
response = client.send_message(
    query="你好，请介绍一下工作流编排",
    user="user_123",  # 用户唯一标识
    response_mode="blocking"  # 阻塞模式，等待回复完成
)
print(f"AI回答: {response['answer']}")
print(f"会话ID: {response['conversation_id']}")
```

#### 流式响应处理

Chatflow 应用支持工作流相关的事件处理，可以监控工作流和节点的执行过程：

```python
# 流式模式发送消息
stream = client.send_message(
    query="分析人工智能的发展趋势",
    user="user_123",
    response_mode="streaming"  # 流式模式
)

# 消息处理函数
def on_message(chunk):
    print(chunk.get("answer", ""), end="", flush=True)

def on_message_end(chunk):
    print("\n消息完成！")

# 工作流事件处理函数
def on_workflow_started(data):
    print(f"\n工作流开始: ID={data.get('id')}")

def on_node_started(data):
    print(f"节点开始: ID={data.get('node_id')}, 类型={data.get('node_type')}")

def on_node_finished(data):
    print(f"节点完成: ID={data.get('node_id')}, 状态={data.get('status')}")
    if data.get('outputs'):
        print(f"  输出: {data.get('outputs')}")

def on_workflow_finished(data):
    print(f"工作流完成: ID={data.get('id')}, 状态={data.get('status')}")
    if data.get('outputs'):
        print(f"  最终输出: {data.get('outputs')}")

# 处理流式响应
result = client.process_streaming_response(
    stream,
    handle_message=on_message,
    handle_message_end=on_message_end,
    handle_workflow_started=on_workflow_started,
    handle_node_started=on_node_started,
    handle_node_finished=on_node_finished,
    handle_workflow_finished=on_workflow_finished
)

print(f"工作流运行ID: {result.get('workflow_run_id')}")
print(f"执行的节点数量: {len(result.get('nodes_data', []))}")
```

#### 多轮对话

```python
# 第一轮对话
response1 = client.send_message(
    query="什么是工作流编排？",
    user="user_123",
    response_mode="blocking"
)
conversation_id = response1["conversation_id"]
print(f"AI: {response1['answer']}")

# 第二轮对话（基于之前的上下文）
response2 = client.send_message(
    query="能给我举个工作流编排的实际应用例子吗？",
    user="user_123",
    conversation_id=conversation_id,  # 使用第一轮返回的会话ID
    response_mode="blocking"
)
print(f"AI: {response2['answer']}")
```

#### 会话管理

Chatflow 应用与 Chatbot 一样支持会话管理功能：

```python
# 获取会话列表
conversations = client.get_conversations(
    user="user_123",
    limit=5  # 获取最近5条会话
)

# 获取会话历史消息
messages = client.get_messages(
    conversation_id="conversation_id",
    user="user_123",
    limit=10  # 获取最近10条消息
)

# 重命名会话
client.rename_conversation(
    conversation_id="conversation_id",
    user="user_123",
    name="工作流编排讨论"  # 手动指定名称
)

# 删除会话
client.delete_conversation(
    conversation_id="conversation_id",
    user="user_123"
)
```

#### 文件与多模态功能

```python
# 上传文件
file_result = client.upload_file(
    file_path="document.pdf",
    user="user_123"
)
file_id = file_result["id"]

# 发送带文件的消息
response = client.send_message(
    query="请分析这个文档",
    user="user_123",
    files=[{
        "type": "document",
        "transfer_method": "local_file",
        "upload_file_id": file_id
    }],
    response_mode="blocking"
)
```

#### 消息反馈与推荐问题

```python
# 对消息进行反馈
client.message_feedback(
    message_id="message_id_from_response",
    user="user_123",
    rating="like",  # "like"或"dislike"
    content="这个工作流分析很到位！"  # 可选
)

# 获取推荐问题
suggestions = client.get_suggested_questions(
    message_id="message_id_from_response",
    user="user_123"
)
```

#### 停止正在进行的任务

```python
# 停止响应
client.stop_response(
    task_id="task_id_from_stream",
    user="user_123"
)
```

更多示例请参阅 [examples/chatflow_example.py](examples/chatflow_example.py)。

### WorkflowClient

WorkflowClient 用于与 Dify 的 Workflow 应用交互。Workflow 应用无会话支持，适合用于翻译、文章写作、文本总结等 AI 任务。

#### 基本用法

```python
from pydify import WorkflowClient

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
    "input": "请写一首关于人工智能的诗",
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

#### 流式响应处理

```python
# 流式模式执行工作流
stream = client.run(
    inputs={"prompt": "给我列出5种编程语言及其特点"},
    user="user_123",
    response_mode="streaming"  # 流式模式，实时获取工作流执行进度
)

# 处理流式响应
def on_workflow_started(data):
    print(f"工作流开始: {data['id']}")

def on_node_finished(data):
    print(f"节点完成: {data['node_id']}, 状态: {data['status']}")

def on_workflow_finished(data):
    print(f"工作流完成: {data['id']}, 状态: {data['status']}")

# 处理流式响应
result = client.process_streaming_response(
    stream,
    handle_workflow_started=on_workflow_started,
    handle_node_finished=on_node_finished,
    handle_workflow_finished=on_workflow_finished
)
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

#### 停止正在执行的任务

```python
# 停止任务
client.stop_task(task_id="task_id_from_stream", user="user_123")
```

#### 获取工作流日志

```python
# 获取工作流执行日志
logs = client.get_logs(limit=10)
for log in logs["data"]:
    print(f"工作流 {log['id']} 状态: {log['workflow_run']['status']}")
```

更多示例请参阅 [examples/workflow_example.py](examples/workflow_example.py)。

## 贡献

欢迎贡献代码、报告问题或提出建议！请查看 [CONTRIBUTING.md](CONTRIBUTING.md) 了解更多详情。

## 许可证

本项目采用 MIT 许可证。详细信息请参阅 [LICENSE](LICENSE) 文件。

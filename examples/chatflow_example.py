"""
Pydify ChatflowClient 使用示例

本示例展示了如何使用 ChatflowClient 类与 Dify Chatflow 应用进行交互。
Chatflow 是基于工作流编排的对话型应用，适用于定义复杂流程的多轮对话场景。
"""
import os
import sys
import base64
from pprint import pprint

# load_env
from dotenv import load_dotenv
load_dotenv()

# 将父目录添加到 sys.path，使示例可以直接运行
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from pydify import ChatflowClient

# 从环境变量或直接设置 API 密钥
API_KEY = os.environ.get("DIFY_API_KEY_CHATFLOW", "your_api_key_here")
BASE_URL = os.environ.get("DIFY_BASE_URL", "http://your-dify-instance.com/v1")
USER_ID = "user_123"  # 用户唯一标识

# 初始化客户端
client = ChatflowClient(api_key=API_KEY, base_url=BASE_URL)

def example_get_app_info():
    """获取应用信息示例"""
    print("\n==== 获取应用信息 ====")
    info = client.get_app_info()
    pprint(info)
    return info

def example_get_parameters():
    """获取应用参数示例"""
    print("\n==== 获取应用参数 ====")
    params = client.get_parameters()
    print("开场白: ", params.get("opening_statement", ""))
    print("推荐问题: ", params.get("suggested_questions", []))
    print("支持的功能:")
    
    features = []
    if params.get("speech_to_text", {}).get("enabled", False):
        features.append("语音转文本")
    if params.get("file_upload", {}).get("image", {}).get("enabled", False):
        features.append("图片上传")
    
    print(", ".join(features) if features else "无特殊功能")
    return params

def example_send_message_blocking():
    """以阻塞模式发送消息示例"""
    print("\n==== 以阻塞模式发送消息 ====")
    
    # 发送消息（阻塞模式）
    response = client.send_message(
        query="你好，请介绍一下自己",
        user=USER_ID,
        response_mode="blocking"
    )
    
    print("消息ID: ", response.get("message_id", ""))
    print("会话ID: ", response.get("conversation_id", ""))
    print("AI回答: ", response.get("answer", ""))
    
    # 返回会话ID，可用于后续对话
    return response.get("conversation_id")

def example_send_message_streaming():
    """以流式模式发送消息示例"""
    print("\n==== 以流式模式发送消息 ====")
    
    # 消息处理函数
    def on_message(chunk):
        print(f"{chunk.get('answer', '')}", end="", flush=True)
    
    def on_message_end(chunk):
        print("\n消息完成！")
        if "metadata" in chunk and "usage" in chunk["metadata"]:
            usage = chunk["metadata"]["usage"]
            print(f"Token使用情况: 输入={usage.get('prompt_tokens', 0)}, "
                  f"输出={usage.get('completion_tokens', 0)}, "
                  f"总计={usage.get('total_tokens', 0)}")
    
    def on_workflow_started(data):
        print(f"\n工作流开始: ID={data.get('id')}, 序列号={data.get('sequence_number')}")
    
    def on_node_started(data):
        print(f"节点开始: ID={data.get('node_id')}, 类型={data.get('node_type')}, 标题={data.get('title')}")
    
    def on_node_finished(data):
        print(f"节点完成: ID={data.get('node_id')}, 状态={data.get('status')}, 耗时={data.get('elapsed_time', 0)}秒")
        if data.get('outputs'):
            print(f"  输出: {data.get('outputs')}")
    
    def on_workflow_finished(data):
        print(f"工作流完成: ID={data.get('id')}, 状态={data.get('status')}, 总耗时={data.get('elapsed_time', 0)}秒")
        if data.get('outputs'):
            print(f"  最终输出: {data.get('outputs')}")
    
    def on_error(chunk):
        print(f"\n错误: {chunk.get('message', '未知错误')}")
    
    # 发送消息（流式模式）
    stream = client.send_message(
        query="分析一下人工智能的未来发展趋势",
        user=USER_ID,
        response_mode="streaming"
    )
    
    # 处理流式响应
    result = client.process_streaming_response(
        stream,
        handle_message=on_message,
        handle_message_end=on_message_end,
        handle_workflow_started=on_workflow_started,
        handle_node_started=on_node_started,
        handle_node_finished=on_node_finished,
        handle_workflow_finished=on_workflow_finished,
        handle_error=on_error
    )
    
    print("\n\n处理结果摘要:")
    print(f"消息ID: {result.get('message_id')}")
    print(f"会话ID: {result.get('conversation_id')}")
    print(f"工作流运行ID: {result.get('workflow_run_id')}")
    print(f"节点数量: {len(result.get('nodes_data', []))}")
    
    # 返回会话ID，可用于后续对话
    return result.get("conversation_id")

def example_continuation_conversation():
    """多轮对话示例"""
    print("\n==== 多轮对话示例 ====")
    
    # 第一轮对话
    response1 = client.send_message(
        query="你好，我想了解工作流编排的概念",
        user=USER_ID,
        response_mode="blocking"
    )
    
    conversation_id = response1.get("conversation_id")
    print(f"第一轮对话 - AI: {response1.get('answer', '')}")
    
    # 第二轮对话（在同一会话中）
    response2 = client.send_message(
        query="能给我举个工作流编排的实际应用例子吗？",
        user=USER_ID,
        conversation_id=conversation_id,  # 使用第一轮返回的会话ID
        response_mode="blocking"
    )
    
    print(f"第二轮对话 - AI: {response2.get('answer', '')}")
    
    return conversation_id

def example_get_conversations():
    """获取会话列表示例"""
    print("\n==== 获取会话列表 ====")
    
    result = client.get_conversations(
        user=USER_ID,
        limit=5  # 获取最近5条会话
    )
    
    print(f"共有 {len(result.get('data', []))} 条会话:")
    for i, conversation in enumerate(result.get("data", []), 1):
        print(f"{i}. ID: {conversation.get('id')} - "
              f"名称: {conversation.get('name')} - "
              f"创建时间: {conversation.get('created_at')}")
    
    # 返回第一个会话的ID，如果有的话
    conversations = result.get("data", [])
    return conversations[0].get("id") if conversations else None

def example_get_messages():
    """获取会话历史消息示例"""
    print("\n==== 获取会话历史消息 ====")
    
    # 先获取会话列表
    conversation_id = example_get_conversations()
    
    if not conversation_id:
        print("没有可用的会话，跳过此示例")
        return
    
    # 获取该会话的历史消息
    result = client.get_messages(
        conversation_id=conversation_id,
        user=USER_ID,
        limit=10  # 获取最近10条消息
    )
    
    print(f"会话 {conversation_id} 的消息记录:")
    for i, message in enumerate(result.get("data", []), 1):
        sender = "用户" if "query" in message else "AI"
        content = message.get("query") if "query" in message else message.get("answer")
        print(f"{i}. {sender}: {content[:50]}{'...' if len(content) > 50 else ''}")
    
    # 返回第一条消息的ID，如果有的话
    messages = result.get("data", [])
    return messages[0].get("id") if messages else None

def example_message_feedback():
    """消息反馈示例"""
    print("\n==== 消息反馈示例 ====")
    
    # 先创建一个会话获取消息ID
    response = client.send_message(
        query="解释一下什么是工作流编排对话型应用",
        user=USER_ID,
        response_mode="blocking"
    )
    
    message_id = response.get("message_id")
    if not message_id:
        print("消息发送失败，跳过此示例")
        return
    
    # 对消息进行点赞
    like_result = client.message_feedback(
        message_id=message_id,
        user=USER_ID,
        rating="like",
        content="这个解释非常清晰！"
    )
    
    print(f"点赞反馈结果: {like_result}")
    
    # 撤销点赞
    clear_result = client.message_feedback(
        message_id=message_id,
        user=USER_ID,
        rating=None
    )
    
    print(f"撤销反馈结果: {clear_result}")
    
    return message_id

def example_get_suggested_questions():
    """获取推荐问题示例"""
    print("\n==== 获取推荐问题示例 ====")
    
    # 先发送一条消息
    response = client.send_message(
        query="什么是工作流编排？",
        user=USER_ID,
        response_mode="blocking"
    )
    
    message_id = response.get("message_id")
    if not message_id:
        print("消息发送失败，跳过此示例")
        return
    
    # 获取推荐的下一轮问题
    result = client.get_suggested_questions(
        message_id=message_id,
        user=USER_ID
    )
    
    questions = result.get("data", [])
    if questions:
        print("推荐的后续问题:")
        for i, question in enumerate(questions, 1):
            print(f"{i}. {question}")
    else:
        print("没有推荐问题")
    
    return questions

def example_rename_conversation():
    """重命名会话示例"""
    print("\n==== 重命名会话示例 ====")
    
    # 创建一个新会话
    response = client.send_message(
        query="请概述一下工作流编排的主要优势",
        user=USER_ID,
        response_mode="blocking"
    )
    
    conversation_id = response.get("conversation_id")
    if not conversation_id:
        print("会话创建失败，跳过此示例")
        return
    
    # 手动重命名会话
    result = client.rename_conversation(
        conversation_id=conversation_id,
        user=USER_ID,
        name="工作流编排优势讨论"
    )
    
    print(f"重命名结果: 新名称 = {result.get('name')}")
    
    # 自动生成会话名称
    auto_result = client.rename_conversation(
        conversation_id=conversation_id,
        user=USER_ID,
        auto_generate=True
    )
    
    print(f"自动重命名结果: 新名称 = {auto_result.get('name')}")
    
    return conversation_id

def example_delete_conversation():
    """删除会话示例"""
    print("\n==== 删除会话示例 ====")
    
    # 创建一个新会话
    response = client.send_message(
        query="这个会话将被删除",
        user=USER_ID,
        response_mode="blocking"
    )
    
    conversation_id = response.get("conversation_id")
    if not conversation_id:
        print("会话创建失败，跳过此示例")
        return
    
    print(f"创建的会话ID: {conversation_id}")
    
    # 删除会话
    result = client.delete_conversation(
        conversation_id=conversation_id,
        user=USER_ID
    )
    
    print(f"删除结果: {result}")
    return result

def example_upload_file():
    """上传文件示例"""
    print("\n==== 上传文件示例 ====")
    
    # 创建一个临时图片文件
    try:
        import tempfile
        from PIL import Image, ImageDraw
        
        # 创建一个简单的图片
        img = Image.new('RGB', (300, 200), color = (73, 109, 137))
        d = ImageDraw.Draw(img)
        d.text((100, 100), "Dify Test Image", fill=(255, 255, 0))
        
        # 保存到临时文件
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            img_path = f.name
            img.save(img_path)
        
        print(f"创建测试图片: {img_path}")
        
        # 上传图片
        result = client.upload_file(
            file_path=img_path,
            user=USER_ID
        )
        
        print("文件上传成功:")
        print(f"文件ID: {result.get('id')}")
        print(f"文件名: {result.get('name')}")
        print(f"大小: {result.get('size')} 字节")
        
        # 清理临时文件
        os.unlink(img_path)
        
        # 返回上传的文件ID
        return result.get('id')
    
    except ImportError:
        print("需要安装PIL库才能运行此示例: pip install pillow")
        return None
    except Exception as e:
        print(f"创建或上传文件时出错: {e}")
        return None

def example_send_message_with_image():
    """发送带图片的消息示例"""
    print("\n==== 发送带图片的消息示例 ====")
    
    # 先上传图片
    file_id = example_upload_file()
    if not file_id:
        print("图片上传失败，跳过此示例")
        return
    
    # 准备文件信息
    files = [{
        "type": "image",
        "transfer_method": "local_file",
        "upload_file_id": file_id
    }]
    
    # 发送带图片的消息
    response = client.send_message(
        query="请描述这张图片",
        user=USER_ID,
        files=files,
        response_mode="blocking"
    )
    
    print(f"AI对图片的描述: {response.get('answer', '')}")
    return response

def example_audio_to_text():
    """语音转文字示例"""
    print("\n==== 语音转文字示例 ====")
    
    try:
        import tempfile
        from gtts import gTTS
        
        # 创建一个临时语音文件
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as f:
            audio_path = f.name
        
        # 使用gTTS生成语音
        tts = gTTS("请问工作流编排对话型应用有哪些优势？", lang='zh-cn')
        tts.save(audio_path)
        
        print(f"创建测试语音: {audio_path}")
        
        # 语音转文字
        result = client.audio_to_text(
            file_path=audio_path,
            user=USER_ID
        )
        
        print(f"语音转文字结果: {result.get('text', '')}")
        
        # 清理临时文件
        os.unlink(audio_path)
        
        return result
        
    except ImportError:
        print("需要安装gTTS库才能运行此示例: pip install gtts")
        return None
    except Exception as e:
        print(f"创建或处理语音文件时出错: {e}")
        return None

def example_text_to_audio():
    """文字转语音示例"""
    print("\n==== 文字转语音示例 ====")
    
    # 直接文本转语音
    result_from_text = client.text_to_audio(
        user=USER_ID,
        text="工作流编排对话型应用是基于工作流编排，适用于定义复杂流程的多轮对话场景，具有记忆功能。"
    )
    
    print("文本转语音请求发送成功")
    
    # 从消息ID转语音
    response = client.send_message(
        query="工作流编排有哪些主要组件？",
        user=USER_ID,
        response_mode="blocking"
    )
    
    message_id = response.get("message_id")
    if message_id:
        result_from_message = client.text_to_audio(
            user=USER_ID,
            message_id=message_id
        )
        print("从消息ID生成语音请求发送成功")
    
    return result_from_text

def example_stop_response():
    """停止响应示例"""
    print("\n==== 停止响应示例 ====")
    print("注意: 此示例需要有一个正在运行的长任务才能演示")
    
    # 启动一个需要较长时间的流式响应
    task_id = None
    
    try:
        # 定义事件处理函数获取任务ID
        def get_task_id(chunk):
            nonlocal task_id
            if "task_id" in chunk:
                task_id = chunk["task_id"]
                print(f"获取到任务ID: {task_id}")
                # 故意抛出异常，中断流式处理
                raise Exception("获取到任务ID，中断流处理")
        
        # 执行一个长任务
        stream = client.send_message(
            query="请详细分析工作流编排在企业数字化转型中的应用场景和案例，要求内容全面深入",
            user=USER_ID,
            response_mode="streaming"
        )
        
        # 只处理第一个响应块以获取任务ID
        for chunk in stream:
            get_task_id(chunk)
            break
        
    except Exception as e:
        if "获取到任务ID" not in str(e):
            print(f"错误: {e}")
            return
    
    if task_id:
        # 停止任务
        print(f"尝试停止任务: {task_id}")
        result = client.stop_response(task_id, USER_ID)
        print("停止任务结果:", result)
        return result
    else:
        print("无法获取任务ID，跳过停止任务")
        return None

if __name__ == "__main__":
    print("===== Pydify ChatflowClient 示例 =====")
    
    try:
        # 运行基本示例
        example_get_app_info()
        example_get_parameters()
        
        # 发送消息示例
        example_send_message_blocking()
        example_send_message_streaming()
        
        # 会话管理示例
        example_continuation_conversation()
        example_get_conversations()
        example_get_messages()
        example_rename_conversation()
        
        # 消息交互示例
        example_message_feedback()
        example_get_suggested_questions()
        
        # 文件和多模态示例
        # example_upload_file()  # 需要PIL库
        # example_send_message_with_image()  # 需要PIL库
        
        # 语音功能示例
        # example_audio_to_text()  # 需要gtts库
        # example_text_to_audio()
        
        # 其他功能示例
        # example_delete_conversation()  # 会删除会话，慎用
        # example_stop_response()  # 需要长任务
        
    except Exception as e:
        print(f"示例运行过程中发生错误: {e}")
        import traceback
        traceback.print_exc() 
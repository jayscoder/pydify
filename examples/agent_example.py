"""
Pydify AgentClient 使用示例

本示例展示了如何使用 AgentClient 类与 Dify Agent 应用进行交互。
Agent 是能够迭代式规划推理、自主工具调用，直至完成任务目标的智能助手。
"""

import base64
import os
import sys
from pprint import pprint

# load_env
from dotenv import load_dotenv

load_dotenv()

# 将父目录添加到 sys.path，使示例可以直接运行
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from pydify import AgentClient
from pydify.common import DifyAPIError

# 从环境变量或直接设置 API 密钥
API_KEY = os.environ.get("DIFY_API_KEY_AGENT", "your_api_key_here")
BASE_URL = os.environ.get("DIFY_BASE_URL", "http://your_base_url_here")
USER_ID = "user_123"  # 用户唯一标识

# 配置API请求参数
REQUEST_TIMEOUT = 30  # API请求超时时间(秒)
MAX_RETRIES = 3  # 最大重试次数
RETRY_DELAY = 2  # 重试延迟时间(秒)

# 初始化客户端
client = AgentClient(
    api_key=API_KEY,
    base_url=BASE_URL,
)


# 自定义请求参数的函数
def get_request_kwargs():
    """返回一个包含请求参数的字典，可用于所有API请求"""
    return {
        "timeout": REQUEST_TIMEOUT,
        "max_retries": MAX_RETRIES,
        "retry_delay": RETRY_DELAY,
    }


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


def example_send_message_streaming():
    """以流式模式发送消息示例"""
    print("\n==== Agent对话示例 ====")

    # 定义处理函数
    def on_agent_message(chunk):
        print(f"{chunk.get('answer', '')}", end="", flush=True)

    def on_agent_thought(chunk):
        print(f"\n\n[Agent思考] {chunk.get('position')}:")
        print(f"思考: {chunk.get('thought')}")
        print(f"工具: {chunk.get('tool')}")
        print(f"输入: {chunk.get('tool_input')}")
        print(f"观察: {chunk.get('observation')}\n")

    def on_message_file(chunk):
        print(
            f"\n收到文件: ID={chunk.get('id')}, 类型={chunk.get('type')}, URL={chunk.get('url')}"
        )

    def on_message_end(chunk):
        print("\n\n消息完成！")
        if "metadata" in chunk and "usage" in chunk["metadata"]:
            usage = chunk["metadata"]["usage"]
            print(
                f"Token使用情况: 输入={usage.get('prompt_tokens', 0)}, "
                f"输出={usage.get('completion_tokens', 0)}, "
                f"总计={usage.get('total_tokens', 0)}"
            )

    def on_error(chunk):
        print(f"\n错误: {chunk.get('message', '未知错误')}")

    # 请求参数，包括加入重试和超时设置
    request_kwargs = get_request_kwargs()

    try:
        # 发送消息（流式模式，Agent只支持流式模式）
        print("发送查询: '帮我搜索最近一周的股市行情，并分析趋势'")
        stream = client.send_message(
            query="帮我搜索最近一周的股市行情，并分析趋势",
            user=USER_ID,
            inputs={},  # 添加空的inputs参数
            **request_kwargs,  # 传递请求参数
        )

        # 处理流式响应
        result = client.process_streaming_response(
            stream,
            handle_agent_message=on_agent_message,
            handle_agent_thought=on_agent_thought,
            handle_message_file=on_message_file,
            handle_message_end=on_message_end,
            handle_error=on_error,
        )

        print("\n\n处理结果摘要:")
        print(f"消息ID: {result.get('message_id')}")
        print(f"会话ID: {result.get('conversation_id')}")
        print(f"Agent思考步骤数: {len(result.get('agent_thoughts', []))}")

        # 返回会话ID，可用于后续对话
        return result.get("conversation_id")

    except DifyAPIError as e:
        print(f"API错误: {str(e)}")
        print(f"状态码: {e.status_code}")
        print(f"错误数据: {e.error_data}")
        return None
    except Exception as e:
        print(f"发生异常: {str(e)}")
        import traceback

        traceback.print_exc()
        return None


def example_continuation_conversation():
    """多轮对话示例"""
    print("\n==== 多轮对话示例 ====")

    # 获取会话ID
    conversation_id = example_send_message_streaming()

    if not conversation_id:
        print("第一轮对话失败，跳过多轮对话示例")
        return

    # 继续对话函数
    def on_agent_message(chunk):
        print(f"{chunk.get('answer', '')}", end="", flush=True)

    def on_agent_thought(chunk):
        print(f"\n\n[Agent思考] {chunk.get('position')}:")
        print(f"思考: {chunk.get('thought')}")
        print(f"工具: {chunk.get('tool')}")
        print(f"输入: {chunk.get('tool_input')}")
        print(f"观察: {chunk.get('observation')}\n")

    def on_message_end(chunk):
        print("\n\n第二轮对话完成！")

    # 第二轮对话（在同一会话中）
    print("\n发送第二轮对话...")
    stream2 = client.send_message(
        query="基于上述分析，你认为下周适合买入哪些类型的股票？",
        user=USER_ID,
        conversation_id=conversation_id,  # 使用第一轮返回的会话ID
    )

    # 处理流式响应
    client.process_streaming_response(
        stream2,
        handle_agent_message=on_agent_message,
        handle_agent_thought=on_agent_thought,
        handle_message_end=on_message_end,
    )

    return conversation_id


def example_get_conversations():
    """获取会话列表示例"""
    print("\n==== 获取会话列表 ====")

    result = client.get_conversations(user=USER_ID, limit=5)  # 获取最近5条会话

    print(f"共有 {len(result.get('data', []))} 条会话:")
    for i, conversation in enumerate(result.get("data", []), 1):
        print(
            f"{i}. ID: {conversation.get('id')} - "
            f"名称: {conversation.get('name')} - "
            f"创建时间: {conversation.get('created_at')}"
        )

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
        conversation_id=conversation_id, user=USER_ID, limit=10  # 获取最近10条消息
    )

    print(f"会话 {conversation_id} 的消息记录:")
    for i, message in enumerate(result.get("data", []), 1):
        sender = "用户" if "query" in message else "AI"
        content = message.get("query") if "query" in message else message.get("answer")
        print(f"{i}. {sender}: {content[:50]}{'...' if len(content) > 50 else ''}")

        # 如果有Agent思考内容，显示摘要
        if "agent_thoughts" in message and message["agent_thoughts"]:
            thoughts = message["agent_thoughts"]
            print(f"   - Agent思考步骤: {len(thoughts)}个")
            for j, thought in enumerate(thoughts[:2], 1):  # 只显示前两个思考步骤
                print(f"     步骤{j}: {thought.get('thought', '')[:50]}...")
            if len(thoughts) > 2:
                print(f"     ...还有{len(thoughts) - 2}个步骤未显示")

    # 返回第一条消息的ID，如果有的话
    messages = result.get("data", [])
    return messages[0].get("id") if messages else None


def example_message_feedback():
    """消息反馈示例"""
    print("\n==== 消息反馈示例 ====")

    # 获取消息ID
    message_id = example_get_messages()

    if not message_id:
        print("没有可用的消息，跳过此示例")
        return

    print(f"为消息ID {message_id} 提供反馈")

    # 对消息进行点赞
    like_result = client.message_feedback(
        message_id=message_id,
        user=USER_ID,
        rating="like",
        content="这个分析非常全面，感谢AI的帮助！",
    )

    print(f"点赞反馈结果: {like_result}")

    # 撤销点赞
    clear_result = client.message_feedback(
        message_id=message_id, user=USER_ID, rating=None
    )

    print(f"撤销反馈结果: {clear_result}")

    return message_id


def example_get_suggested_questions():
    """获取推荐问题示例"""
    print("\n==== 获取推荐问题示例 ====")

    # 获取消息ID
    message_id = example_get_messages()

    if not message_id:
        print("没有可用的消息，跳过此示例")
        return

    print(f"使用消息ID: {message_id} 获取推荐问题")

    # 请求参数，包括加入重试和超时设置
    request_kwargs = get_request_kwargs()

    try:
        # 获取推荐的下一轮问题
        result = client.get_suggested_questions(
            message_id=message_id, user=USER_ID, **request_kwargs  # 传递请求参数
        )

        questions = result.get("data", [])
        if questions:
            print("推荐的后续问题:")
            for i, question in enumerate(questions, 1):
                print(f"{i}. {question}")
        else:
            print("没有推荐问题")

        return questions

    except DifyAPIError as e:
        print(f"API错误: {str(e)}")
        print(f"状态码: {e.status_code}")
        print(f"错误数据: {e.error_data}")
        return []
    except Exception as e:
        print(f"发生异常: {str(e)}")
        import traceback

        traceback.print_exc()
        return []


def example_rename_conversation():
    """重命名会话示例"""
    print("\n==== 重命名会话示例 ====")

    # 获取会话ID
    conversation_id = example_get_conversations()

    if not conversation_id:
        print("没有可用的会话，跳过此示例")
        return

    # 手动重命名会话
    result = client.rename_conversation(
        conversation_id=conversation_id, user=USER_ID, name="智能分析股市趋势"
    )

    print(f"重命名结果: 新名称 = {result.get('name')}")

    # 自动生成会话名称
    auto_result = client.rename_conversation(
        conversation_id=conversation_id, user=USER_ID, auto_generate=True
    )

    print(f"自动重命名结果: 新名称 = {auto_result.get('name')}")

    return conversation_id


def example_delete_conversation():
    """删除会话示例"""
    print("\n==== 删除会话示例 ====")

    # 创建一个新会话（通过流式发送消息）
    def on_message_end(chunk):
        print("测试消息发送完成")

    stream = client.send_message(query="这是一个测试消息，该会话将被删除", user=USER_ID)

    result = client.process_streaming_response(
        stream, handle_message_end=on_message_end
    )

    conversation_id = result.get("conversation_id")
    if not conversation_id:
        print("会话创建失败，跳过此示例")
        return

    print(f"创建的会话ID: {conversation_id}")

    # 删除会话
    result = client.delete_conversation(conversation_id=conversation_id, user=USER_ID)

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
        img = Image.new("RGB", (300, 200), color=(73, 109, 137))
        d = ImageDraw.Draw(img)
        d.text((100, 100), "Dify Test Image", fill=(255, 255, 0))

        # 保存到临时文件
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            img_path = f.name
            img.save(img_path)

        print(f"创建测试图片: {img_path}")

        # 上传图片
        result = client.upload_file(file_path=img_path, user=USER_ID)

        print("文件上传成功:")
        print(f"文件ID: {result.get('id')}")
        print(f"文件名: {result.get('name')}")
        print(f"大小: {result.get('size')} 字节")

        # 清理临时文件
        os.unlink(img_path)

        # 返回上传的文件ID
        return result.get("id")

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
    files = [
        {"type": "image", "transfer_method": "local_file", "upload_file_id": file_id}
    ]

    # 定义处理函数
    def on_agent_message(chunk):
        print(f"{chunk.get('answer', '')}", end="", flush=True)

    def on_agent_thought(chunk):
        print(f"\n\n[Agent思考] {chunk.get('position')}:")
        print(f"思考: {chunk.get('thought')}")
        if chunk.get("tool"):
            print(f"工具: {chunk.get('tool')}")
            print(f"输入: {chunk.get('tool_input')}")
        print(f"观察: {chunk.get('observation')}\n")

    def on_message_end(chunk):
        print("\n\n消息完成！")

    # 发送带图片的消息
    print("发送带图片的消息: '请分析这张图片'")
    stream = client.send_message(
        query="请分析这张图片，告诉我上面写了什么内容", user=USER_ID, files=files
    )

    # 处理流式响应
    result = client.process_streaming_response(
        stream,
        handle_agent_message=on_agent_message,
        handle_agent_thought=on_agent_thought,
        handle_message_end=on_message_end,
    )

    return result


def example_audio_to_text():
    """语音转文字示例"""
    print("\n==== 语音转文字示例 ====")

    try:
        import tempfile

        from gtts import gTTS

        # 创建一个临时语音文件
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            audio_path = f.name

        # 使用gTTS生成语音
        tts = gTTS("分析股市趋势并给出投资建议", lang="zh-cn")
        tts.save(audio_path)

        print(f"创建测试语音: {audio_path}")

        # 语音转文字
        result = client.audio_to_text(file_path=audio_path, user=USER_ID)

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
        text="Agent对话型应用能够迭代式的规划推理、自主工具调用，直至完成任务目标。",
    )

    print("文本转语音请求发送成功")

    # 从消息ID转语音
    message_id = example_get_messages()
    if message_id:
        result_from_message = client.text_to_audio(user=USER_ID, message_id=message_id)
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
            query="请详细撰写一份关于人工智能在金融市场中的应用研究报告，包括市场预测、风险管理、自动交易等方面",
            user=USER_ID,
        )

        # 只处理第一个响应块以获取任务ID
        for chunk in stream:
            if (
                chunk.get("event") in ["message", "agent_message"]
                and "task_id" in chunk
            ):
                task_id = chunk["task_id"]
                print(f"获取到任务ID: {task_id}")
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
    print("===== Pydify AgentClient 示例 =====")

    try:
        # 运行基本示例
        example_get_app_info()
        example_get_parameters()

        # 发送消息示例
        example_send_message_streaming()

        # 多轮对话示例
        # example_continuation_conversation()

        # 会话管理示例
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

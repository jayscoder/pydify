"""
Pydify TextGenerationClient 使用示例

本示例展示了如何使用 TextGenerationClient 类与 Dify Text Generation 应用进行交互。
Text Generation 应用无会话支持，适合用于翻译、文章写作、总结等AI任务。
"""

import os
import sys
from pprint import pprint

# load_env
from dotenv import load_dotenv

load_dotenv()

# 将父目录添加到 sys.path，使示例可以直接运行
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from examples.utils import (
    create_test_image,
    get_standard_handlers,
    print_header,
    print_json,
    print_result_summary,
    print_section,
    run_example,
    save_audio_data,
)
from pydify import TextGenerationClient

# 从环境变量或直接设置 API 密钥
API_KEY = os.environ.get("DIFY_API_KEY_TEXT_GENERATION", "your_api_key_here")
BASE_URL = os.environ.get("DIFY_BASE_URL", "http://your-dify-instance.com/v1")
USER_ID = "user_123"  # 用户唯一标识

# 配置API请求参数
REQUEST_TIMEOUT = 30  # API请求超时时间(秒)
MAX_RETRIES = 3  # 最大重试次数
RETRY_DELAY = 2  # 重试延迟时间(秒)

# 初始化客户端
client = TextGenerationClient(api_key=API_KEY, base_url=BASE_URL)


# 自定义请求参数的函数
def get_request_kwargs():
    """返回一个包含请求参数的字典，可用于所有API请求"""
    return {
        "timeout": REQUEST_TIMEOUT,
        "max_retries": MAX_RETRIES,
        "retry_delay": RETRY_DELAY,
    }


# 获取标准事件处理函数
handlers = get_standard_handlers("text_generation")


def example_get_app_info():
    """获取应用信息示例"""
    info = client.get_app_info()
    print_json(info)
    return info


def example_get_parameters():
    """获取应用参数示例"""
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

    # 检查输入表单控件
    print("\n用户输入表单控件:")
    for control in params.get("user_input_form", []):
        for control_type, config in control.items():
            print(
                f"- {control_type}: {config.get('label')} (变量名: {config.get('variable')})"
            )

    return params


def example_completion_blocking():
    """以阻塞模式发送消息示例"""

    # 获取请求参数
    request_kwargs = get_request_kwargs()

    try:
        response = client.completion(
            query="随机告诉我1个成语",
            user=USER_ID,
            response_mode="blocking",
            **request_kwargs,  # 传递请求参数
        )

        print("消息ID: ", response.get("message_id", ""))
        print("AI回答: ", response.get("answer", ""))

        # 检查是否有使用量信息
        if "metadata" in response and "usage" in response["metadata"]:
            usage = response["metadata"]["usage"]
            print(
                f"\nToken使用情况: 输入={usage.get('prompt_tokens', 0)}, "
                f"输出={usage.get('completion_tokens', 0)}, "
                f"总计={usage.get('total_tokens', 0)}"
            )

        return response.get("message_id")

    except Exception as e:
        print(f"发送消息时出错: {str(e)}")
        import traceback

        traceback.print_exc()
        return None


def example_completion_streaming():
    """以流式模式发送消息示例"""
    print("\n请求生成文本: '请写一首关于春天的诗'")

    # 获取请求参数
    request_kwargs = get_request_kwargs()

    try:
        # 发送消息（流式模式）
        stream = client.completion(
            query="请写一首关于春天的诗",
            user=USER_ID,
            response_mode="streaming",
            **request_kwargs,  # 传递请求参数
        )

        # 处理流式响应
        result = client.process_streaming_response(stream, **handlers)
        print_result_summary(result)

        return result.get("message_id")

    except Exception as e:
        print(f"发送流式消息时出错: {str(e)}")
        import traceback

        traceback.print_exc()
        return None


def example_completion_with_custom_inputs():
    """使用自定义输入参数的示例"""
    # 假设应用定义了一些变量，如：主题(topic)、风格(style)、字数(word_count)
    inputs = {
        "query": "帮我写一篇文章",  # 基本查询
        "topic": "人工智能",  # 主题
        "style": "科普",  # 风格
        "word_count": 500,  # 字数要求
    }

    print(f"\n生成文章，使用自定义参数: {inputs}")

    # 获取请求参数
    request_kwargs = get_request_kwargs()

    try:
        # 发送消息，使用自定义inputs
        stream = client.completion(
            query="帮我写一篇文章",  # 这个会被添加到inputs中的query字段
            user=USER_ID,
            inputs=inputs,
            response_mode="streaming",
            **request_kwargs,  # 传递请求参数
        )

        # 处理流式响应
        result = client.process_streaming_response(
            stream,
            handle_message=handlers["handle_message"],
            handle_message_end=handlers["handle_message_end"],
        )

        return result.get("message_id")

    except Exception as e:
        print(f"发送自定义输入消息时出错: {str(e)}")
        import traceback

        traceback.print_exc()
        return None


def example_message_feedback():
    """消息反馈示例"""
    # 先生成一条消息
    message_id = example_completion_blocking()

    if not message_id:
        print("消息生成失败，跳过反馈示例")
        return

    print(f"\n为消息ID {message_id} 提供反馈")

    # 获取请求参数
    request_kwargs = get_request_kwargs()

    try:
        # 对消息进行点赞
        like_result = client.message_feedback(
            message_id=message_id,
            user=USER_ID,
            rating="like",
            content="这个文章写得很好，内容充实且有深度！",
            **request_kwargs,  # 传递请求参数
        )

        print(f"点赞反馈结果: {like_result}")

        # 撤销点赞
        clear_result = client.message_feedback(
            message_id=message_id,
            user=USER_ID,
            rating=None,
            **request_kwargs,  # 传递请求参数
        )

        print(f"撤销反馈结果: {clear_result}")

        return message_id

    except Exception as e:
        print(f"发送反馈时出错: {str(e)}")
        import traceback

        traceback.print_exc()
        return None


def example_upload_file():
    """上传文件示例"""
    try:
        # 创建测试图片
        img_path = create_test_image("Dify Text Generation Test")

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

    except ImportError as e:
        print(f"创建或上传文件时出错: {e}")
        return None
    except Exception as e:
        print(f"创建或上传文件时出错: {e}")
        return None


def example_completion_with_image():
    """带图片的文本生成示例"""
    # 先上传图片
    file_id = example_upload_file()
    if not file_id:
        print("图片上传失败，跳过此示例")
        return

    # 准备文件信息
    files = [
        {"type": "image", "transfer_method": "local_file", "upload_file_id": file_id}
    ]

    # 获取请求参数
    request_kwargs = get_request_kwargs()

    try:
        # 发送带图片的消息
        print("\n发送带图片的请求: '描述这张图片'")
        stream = client.completion(
            query="描述这张图片的内容，包括颜色、文字等元素",
            user=USER_ID,
            files=files,
            response_mode="streaming",
            **request_kwargs,  # 传递请求参数
        )

        # 处理流式响应
        result = client.process_streaming_response(
            stream,
            handle_message=handlers["handle_message"],
            handle_message_end=handlers["handle_message_end"],
        )

        return result.get("message_id")

    except Exception as e:
        print(f"发送带图片的消息时出错: {str(e)}")
        import traceback

        traceback.print_exc()
        return None


def example_text_to_audio():
    """文字转语音示例"""
    # 先生成一条消息
    message_id = example_completion_blocking()

    # 获取请求参数
    request_kwargs = get_request_kwargs()

    try:
        # 从消息ID生成语音
        if message_id:
            print(f"\n从消息ID生成语音: {message_id}")
            result_from_message = client.text_to_audio(
                user=USER_ID, message_id=message_id, **request_kwargs  # 传递请求参数
            )
            print("从消息ID生成语音请求成功")

        # 直接从文本生成语音
        text = "文本生成应用适合用于翻译、文章写作和内容总结等任务。"
        print(f"\n从文本生成语音: '{text}'")
        result_from_text = client.text_to_audio(
            user=USER_ID, text=text, **request_kwargs  # 传递请求参数
        )
        print("从文本生成语音请求成功")

        # 通常，响应会包含一个base64编码的音频数据字符串
        if "audio_url" in result_from_text:
            print(f"音频URL: {result_from_text['audio_url']}")

        return result_from_text

    except Exception as e:
        print(f"文字转语音时出错: {str(e)}")
        import traceback

        traceback.print_exc()
        return None


def example_stop_completion():
    """停止响应示例"""
    print("注意: 此示例需要有一个正在运行的长任务才能演示")

    # 启动一个需要较长时间的流式响应
    task_id = None

    try:
        # 执行一个长任务
        print("\n开始一个长任务: '写一篇长篇科幻小说，5000字以上'")
        stream = client.completion(
            query="写一篇长篇科幻小说，描述人类在2100年后星际移民的细节，要求5000字以上，包含具体的情节和人物刻画",
            user=USER_ID,
            response_mode="streaming",
        )

        # 只处理前几个响应块以获取任务ID
        for chunk in stream:
            if chunk.get("event") == "message" and "task_id" in chunk:
                task_id = chunk["task_id"]
                print(f"获取到任务ID: {task_id}")
                print(f"开始生成: {chunk.get('answer', '')}")
                # 获取到任务ID后立即停止
                break

    except Exception as e:
        print(f"错误: {e}")
        return

    if task_id:
        # 停止任务
        print(f"\n尝试停止任务: {task_id}")
        result = client.stop_completion(task_id, USER_ID)
        print("停止任务结果:", result)
        return result
    else:
        print("无法获取任务ID，跳过停止任务")
        return None


def example_completion_translation():
    """翻译示例"""
    # 准备翻译输入
    inputs = {
        "query": "请翻译以下文本",
        "text": "Artificial intelligence (AI) is transforming healthcare through early disease detection, personalized treatment plans, and streamlined administrative processes.",
        "target_language": "中文",
    }

    print(f"\n翻译文本: '{inputs['text']}' 到 {inputs['target_language']}")

    # 获取请求参数
    request_kwargs = get_request_kwargs()

    try:
        # 发送翻译请求
        stream = client.completion(
            query="请翻译以下文本",
            user=USER_ID,
            inputs=inputs,
            response_mode="streaming",
            **request_kwargs,  # 传递请求参数
        )

        # 处理流式响应
        result = client.process_streaming_response(
            stream,
            handle_message=handlers["handle_message"],
            handle_message_end=handlers["handle_message_end"],
        )

        return result.get("message_id")

    except Exception as e:
        print(f"发送翻译请求时出错: {str(e)}")
        import traceback

        traceback.print_exc()
        return None


def example_completion_summarization():
    """摘要示例"""
    # 准备摘要输入
    inputs = {
        "query": "请对以下文本进行摘要",
        "text": """
        人工智能(AI)正在迅速改变医疗保健领域。通过机器学习算法，AI系统可以分析大量医疗数据，帮助医生更早地发现疾病迹象。
        例如，AI算法已经能够识别早期癌症标志，有时比传统诊断方法更准确。个性化医疗是另一个关键应用领域，
        AI可以分析患者的遗传信息、生活方式数据和医疗历史，帮助制定针对个体的治疗计划。
        在医院管理方面，AI也在简化行政流程，减少文书工作，让医护人员能够将更多时间用于患者护理。
        虽然还有数据隐私和算法透明度等挑战需要解决，但AI在医疗领域的应用前景非常广阔，
        有望提高诊断准确性，降低成本，并使医疗服务变得更加个性化和高效。
        """,
    }

    print("\n摘要文本示例")

    # 获取请求参数
    request_kwargs = get_request_kwargs()

    try:
        # 发送摘要请求
        stream = client.completion(
            query="请对以下文本进行摘要",
            user=USER_ID,
            inputs=inputs,
            response_mode="streaming",
            **request_kwargs,  # 传递请求参数
        )

        # 处理流式响应
        result = client.process_streaming_response(
            stream,
            handle_message=handlers["handle_message"],
            handle_message_end=handlers["handle_message_end"],
        )

        return result.get("message_id")

    except Exception as e:
        print(f"发送摘要请求时出错: {str(e)}")
        import traceback

        traceback.print_exc()
        return None


if __name__ == "__main__":
    print_header("Pydify TextGenerationClient 示例")

    try:
        # 运行基本示例
        run_example(example_get_app_info)
        run_example(example_get_parameters)

        # 文本生成示例
        run_example(example_completion_blocking)
        run_example(example_completion_streaming)

        # 特定任务示例
        run_example(example_completion_with_custom_inputs)
        run_example(example_completion_translation)
        run_example(example_completion_summarization)

        # 交互功能示例
        run_example(example_message_feedback)

        # 文件和多模态示例
        # run_example(example_upload_file)  # 依赖PIL库
        # run_example(example_completion_with_image)  # 依赖PIL库

        # 语音功能示例
        # run_example(example_text_to_audio)  # 可能需要base64解码支持

        # 其他功能示例
        # run_example(example_stop_completion)  # 会发送长请求并中断

    except Exception as e:
        print(f"示例运行过程中发生错误: {e}")
        import traceback

        traceback.print_exc()

"""
Pydify TextGenerationClient 使用示例

本示例展示了如何使用 TextGenerationClient 类与 Dify Text Generation 应用进行交互。
Text Generation 应用无会话支持，适合用于翻译、文章写作、总结等AI任务。
"""
import os
import sys
import base64
from pprint import pprint

# 将父目录添加到 sys.path，使示例可以直接运行
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from pydify import TextGenerationClient

# 从环境变量或直接设置 API 密钥
API_KEY = os.environ.get("DIFY_API_KEY", "your_api_key_here")
BASE_URL = os.environ.get("DIFY_BASE_URL", "http://your-dify-instance.com/v1")
USER_ID = "user_123"  # 用户唯一标识

# 初始化客户端
client = TextGenerationClient(api_key=API_KEY, base_url=BASE_URL)

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
    
    # 检查输入表单控件
    print("\n用户输入表单控件:")
    for control in params.get("user_input_form", []):
        for control_type, config in control.items():
            print(f"- {control_type}: {config.get('label')} (变量名: {config.get('variable')})")
    
    return params

def example_completion_blocking():
    """以阻塞模式发送消息示例"""
    print("\n==== 文本生成示例（阻塞模式）====")
    
    # 发送消息（阻塞模式）
    response = client.completion(
        query="写一篇关于人工智能在医疗领域应用的短文，不少于300字",
        user=USER_ID,
        response_mode="blocking"
    )
    
    print("消息ID: ", response.get("message_id", ""))
    print("AI回答: ", response.get("answer", ""))
    
    # 检查是否有使用量信息
    if "metadata" in response and "usage" in response["metadata"]:
        usage = response["metadata"]["usage"]
        print(f"\nToken使用情况: 输入={usage.get('prompt_tokens', 0)}, "
              f"输出={usage.get('completion_tokens', 0)}, "
              f"总计={usage.get('total_tokens', 0)}")
    
    return response.get("message_id")

def example_completion_streaming():
    """以流式模式发送消息示例"""
    print("\n==== 文本生成示例（流式模式）====")
    
    # 消息处理函数
    def on_message(chunk):
        print(f"{chunk.get('answer', '')}", end="", flush=True)
    
    def on_message_end(chunk):
        print("\n\n生成完成！")
        if "metadata" in chunk and "usage" in chunk["metadata"]:
            usage = chunk["metadata"]["usage"]
            print(f"Token使用情况: 输入={usage.get('prompt_tokens', 0)}, "
                  f"输出={usage.get('completion_tokens', 0)}, "
                  f"总计={usage.get('total_tokens', 0)}")
    
    def on_error(chunk):
        print(f"\n错误: {chunk.get('message', '未知错误')}")
    
    print("\n请求生成文本: '请写一首关于春天的诗'")
    
    # 发送消息（流式模式）
    stream = client.completion(
        query="请写一首关于春天的诗",
        user=USER_ID,
        response_mode="streaming"
    )
    
    # 处理流式响应
    result = client.process_streaming_response(
        stream,
        handle_message=on_message,
        handle_message_end=on_message_end,
        handle_error=on_error
    )
    
    print("\n\n处理结果摘要:")
    print(f"消息ID: {result.get('message_id')}")
    print(f"任务ID: {result.get('task_id')}")
    
    return result.get("message_id")

def example_completion_with_custom_inputs():
    """使用自定义输入参数的示例"""
    print("\n==== 使用自定义输入参数生成文本 ====")
    
    # 假设应用定义了一些变量，如：主题(topic)、风格(style)、字数(word_count)
    inputs = {
        "query": "帮我写一篇文章",  # 基本查询
        "topic": "人工智能",        # 主题
        "style": "科普",           # 风格
        "word_count": 500          # 字数要求
    }
    
    # 消息处理函数
    def on_message(chunk):
        print(f"{chunk.get('answer', '')}", end="", flush=True)
    
    def on_message_end(chunk):
        print("\n\n生成完成！")
    
    print(f"\n生成文章，使用自定义参数: {inputs}")
    
    # 发送消息，使用自定义inputs
    stream = client.completion(
        query="帮我写一篇文章",  # 这个会被添加到inputs中的query字段
        user=USER_ID,
        inputs=inputs,
        response_mode="streaming"
    )
    
    # 处理流式响应
    result = client.process_streaming_response(
        stream,
        handle_message=on_message,
        handle_message_end=on_message_end
    )
    
    return result.get("message_id")

def example_message_feedback():
    """消息反馈示例"""
    print("\n==== 消息反馈示例 ====")
    
    # 先生成一条消息
    message_id = example_completion_blocking()
    
    if not message_id:
        print("消息生成失败，跳过反馈示例")
        return
    
    print(f"\n为消息ID {message_id} 提供反馈")
    
    # 对消息进行点赞
    like_result = client.message_feedback(
        message_id=message_id,
        user=USER_ID,
        rating="like",
        content="这个文章写得很好，内容充实且有深度！"
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

def example_completion_with_image():
    """带图片的文本生成示例"""
    print("\n==== 带图片的文本生成示例 ====")
    
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
    
    # 消息处理函数
    def on_message(chunk):
        print(f"{chunk.get('answer', '')}", end="", flush=True)
    
    def on_message_end(chunk):
        print("\n\n生成完成！")
    
    # 发送带图片的消息
    print("\n发送带图片的请求: '描述这张图片'")
    stream = client.completion(
        query="描述这张图片的内容，包括颜色、文字等元素",
        user=USER_ID,
        files=files,
        response_mode="streaming"
    )
    
    # 处理流式响应
    result = client.process_streaming_response(
        stream,
        handle_message=on_message,
        handle_message_end=on_message_end
    )
    
    return result.get("message_id")

def example_text_to_audio():
    """文字转语音示例"""
    print("\n==== 文字转语音示例 ====")
    
    # 先生成一条消息
    message_id = example_completion_blocking()
    
    # 从消息ID生成语音
    if message_id:
        print(f"\n从消息ID生成语音: {message_id}")
        result_from_message = client.text_to_audio(
            user=USER_ID,
            message_id=message_id
        )
        print("从消息ID生成语音请求成功")
    
    # 直接从文本生成语音
    text = "文本生成应用适合用于翻译、文章写作和内容总结等任务。"
    print(f"\n从文本生成语音: '{text}'")
    result_from_text = client.text_to_audio(
        user=USER_ID,
        text=text
    )
    print("从文本生成语音请求成功")
    
    # 通常，响应会包含一个base64编码的音频数据字符串
    if "audio_url" in result_from_text:
        print(f"音频URL: {result_from_text['audio_url']}")
    elif "audio" in result_from_text:
        # 这里只打印前50个字符，因为base64字符串可能很长
        print(f"音频数据(base64, 前50字符): {result_from_text.get('audio', '')[:50]}...")
    
    return result_from_text

def example_stop_completion():
    """停止响应示例"""
    print("\n==== 停止响应示例 ====")
    print("注意: 此示例需要有一个正在运行的长任务才能演示")
    
    # 启动一个需要较长时间的流式响应
    task_id = None
    
    try:
        # 执行一个长任务
        print("\n开始一个长任务: '写一篇长篇科幻小说，5000字以上'")
        stream = client.completion(
            query="写一篇长篇科幻小说，描述人类在2100年后星际移民的细节，要求5000字以上，包含具体的情节和人物刻画",
            user=USER_ID,
            response_mode="streaming"
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
    print("\n==== 文本翻译示例 ====")
    
    # 消息处理函数
    def on_message(chunk):
        print(f"{chunk.get('answer', '')}", end="", flush=True)
    
    def on_message_end(chunk):
        print("\n\n翻译完成！")
    
    # 假设应用有专门的翻译输入字段
    inputs = {
        "query": "将以下文本翻译成英文",
        "text_to_translate": "人工智能是研究、开发用于模拟、延伸和扩展人的智能的理论、方法、技术及应用系统的一门新的技术科学。",
        "target_language": "english"
    }
    
    print(f"\n请求翻译: '{inputs['text_to_translate']}'")
    
    # 发送翻译请求
    stream = client.completion(
        query="将以下文本翻译成英文",
        user=USER_ID,
        inputs=inputs,
        response_mode="streaming"
    )
    
    # 处理流式响应
    result = client.process_streaming_response(
        stream,
        handle_message=on_message,
        handle_message_end=on_message_end
    )
    
    return result.get("message_id")

def example_completion_summarization():
    """文本摘要示例"""
    print("\n==== 文本摘要示例 ====")
    
    # 准备一段长文本
    long_text = """
    人工智能(AI)正在以前所未有的速度发展。从自动驾驶汽车到智能助手，从推荐系统到医疗诊断，AI已经渗透到我们生活的方方面面。近年来，特别是大型语言模型(LLM)的出现，更是将AI的能力提升到了新的高度。大型语言模型如ChatGPT、Claude和Gemini能够理解和生成人类语言，回答问题，撰写各种风格的文章，甚至可以编写计码和解释复杂概念。
    
    大型语言模型主要基于Transformer架构，通过自注意力机制来处理序列数据。这些模型在海量文本数据上进行预训练，学习词语的语义和上下文关系，然后通过微调来适应特定任务。尽管这些模型非常强大，但它们也存在一些局限性，如依赖于训练数据的质量和数量，可能存在偏见，难以进行长期规划，以及缺乏真正的理解能力。
    
    随着AI技术的不断发展，我们可以期待看到更加智能和高效的系统出现。未来的AI系统可能会更好地整合多种模态的信息，具有更强的推理能力和常识理解，能够自主学习和适应新环境，并且更加安全、公平和透明。同时，AI的发展也带来了一系列伦理和社会问题，如隐私保护、工作替代、偏见歧视等，这需要我们在技术发展的同时，也关注其对社会的影响，制定相应的政策和规范，确保AI的发展能够真正造福人类。
    """
    
    # 消息处理函数
    def on_message(chunk):
        print(f"{chunk.get('answer', '')}", end="", flush=True)
    
    def on_message_end(chunk):
        print("\n\n摘要生成完成！")
    
    # 准备输入参数
    inputs = {
        "query": "请对以下文本进行摘要",
        "text_to_summarize": long_text,
        "max_length": 150  # 指定摘要最大长度
    }
    
    print("\n请求生成摘要...")
    
    # 发送摘要请求
    stream = client.completion(
        query="请对以下文本进行摘要",
        user=USER_ID,
        inputs=inputs,
        response_mode="streaming"
    )
    
    # 处理流式响应
    result = client.process_streaming_response(
        stream,
        handle_message=on_message,
        handle_message_end=on_message_end
    )
    
    return result.get("message_id")

if __name__ == "__main__":
    print("===== Pydify TextGenerationClient 示例 =====")
    
    try:
        # 运行基本示例
        example_get_app_info()
        example_get_parameters()
        
        # 文本生成示例
        example_completion_blocking()
        example_completion_streaming()
        
        # 特定任务示例
        example_completion_with_custom_inputs()
        example_completion_translation()
        example_completion_summarization()
        
        # 交互功能示例
        example_message_feedback()
        
        # 文件和多模态示例
        # example_upload_file()  # 需要PIL库
        # example_completion_with_image()  # 需要PIL库
        
        # 语音功能示例
        # example_text_to_audio()
        
        # 其他功能示例
        # example_stop_completion()  # 会发送长请求并中断
        
    except Exception as e:
        print(f"示例运行过程中发生错误: {e}")
        import traceback
        traceback.print_exc() 
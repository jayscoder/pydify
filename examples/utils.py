"""
Pydify 示例辅助工具

此模块提供示例程序中常用的辅助功能，如打印格式化输出、创建测试图片、
常见事件处理函数等，避免在各个示例文件中重复类似的代码。
"""

import os
import sys
import tempfile
from typing import Any, Callable, Dict, List, Optional


def print_header(title: str, width: int = 80):
    """
    打印格式化的标题头

    Args:
        title: 标题内容
        width: 标题宽度
    """
    print("\n" + "=" * width)
    print(f" {title} ".center(width, "="))
    print("=" * width)


def print_section(title: str):
    """
    打印小节标题

    Args:
        title: 标题内容
    """
    print(f"\n==== {title} ====")


def print_json(data: Dict[str, Any], indent: int = 2):
    """
    格式化打印JSON数据

    Args:
        data: 要打印的字典数据
        indent: 缩进空格数
    """
    import json

    print(json.dumps(data, ensure_ascii=False, indent=indent))


def print_result_summary(result: Dict[str, Any]):
    """
    打印API调用结果摘要

    Args:
        result: API响应结果
    """
    print("\n结果摘要:")

    if "conversation_id" in result:
        print(f"会话ID: {result['conversation_id']}")

    if "message_id" in result:
        print(f"消息ID: {result['message_id']}")

    if "task_id" in result:
        print(f"任务ID: {result['task_id']}")

    if "metadata" in result and "usage" in result["metadata"]:
        usage = result["metadata"]["usage"]
        print(
            f"Token使用情况: 输入={usage.get('prompt_tokens', 0)}, "
            f"输出={usage.get('completion_tokens', 0)}, "
            f"总计={usage.get('total_tokens', 0)}"
        )

    if "error" in result:
        print(f"错误: {result['error']['message']}")


def create_test_image(text: str = "Dify Test Image") -> str:
    """
    创建测试图片文件

    Args:
        text: 要写入图片的文字

    Returns:
        str: 临时图片文件路径

    Raises:
        ImportError: 当PIL库未安装时
    """
    try:
        from PIL import Image, ImageDraw, ImageFont

        # 创建一个简单的图片
        img = Image.new("RGB", (500, 300), color=(73, 109, 137))
        d = ImageDraw.Draw(img)

        # 尝试加载字体，如果失败则使用默认字体
        try:
            font = ImageFont.truetype("Arial", 24)
        except IOError:
            font = ImageFont.load_default()

        # 添加文字
        d.text((150, 150), text, fill=(255, 255, 0), font=font)

        # 保存到临时文件
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            img_path = f.name
            img.save(img_path)

        print(f"创建测试图片: {img_path}")
        return img_path

    except ImportError:
        print("需要安装PIL库才能创建测试图片: pip install pillow")
        raise


def create_test_audio() -> str:
    """
    创建测试音频文件

    Returns:
        str: 临时音频文件路径

    Raises:
        ImportError: 当所需库未安装时
    """
    try:
        import numpy as np
        from scipy.io import wavfile

        # 创建简单的正弦波音频
        sample_rate = 44100  # 采样率
        duration = 3  # 持续时间(秒)
        frequency = 440  # 频率(赫兹)

        # 生成时间序列
        t = np.linspace(0, duration, int(sample_rate * duration), False)

        # 生成正弦波
        audio_data = np.sin(2 * np.pi * frequency * t) * 32767
        audio_data = audio_data.astype(np.int16)

        # 保存到临时文件
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            audio_path = f.name
            wavfile.write(audio_path, sample_rate, audio_data)

        print(f"创建测试音频: {audio_path}")
        return audio_path

    except ImportError:
        print("需要安装NumPy和SciPy库才能创建测试音频: pip install numpy scipy")
        raise


def save_audio_data(audio_data: str, output_path: Optional[str] = None) -> str:
    """
    保存Base64编码的音频数据到文件

    Args:
        audio_data: Base64编码的音频数据
        output_path: 输出文件路径，如果未提供则创建临时文件

    Returns:
        str: 音频文件路径
    """
    import base64

    if not output_path:
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            output_path = f.name

    # 解码Base64数据并写入文件
    with open(output_path, "wb") as f:
        f.write(base64.b64decode(audio_data))

    print(f"音频已保存到: {output_path}")
    return output_path


# ===== 通用事件处理函数 =====


def default_message_handler(chunk: Dict[str, Any]):
    """
    默认消息块处理函数，打印消息内容

    Args:
        chunk: 消息数据块
    """
    if "answer" in chunk:
        print(chunk["answer"], end="", flush=True)


def default_message_end_handler(chunk: Dict[str, Any]):
    """
    默认消息结束处理函数，打印结束信息和使用统计

    Args:
        chunk: 消息结束数据块
    """
    print("\n\n消息结束")

    if "metadata" in chunk and "usage" in chunk["metadata"]:
        usage = chunk["metadata"]["usage"]
        print(
            f"Token使用: 输入={usage.get('prompt_tokens', 0)}, "
            f"输出={usage.get('completion_tokens', 0)}, "
            f"总计={usage.get('total_tokens', 0)}"
        )


def default_error_handler(chunk: Dict[str, Any]):
    """
    默认错误处理函数，打印错误信息

    Args:
        chunk: 错误数据块
    """
    print(f"\n错误: {chunk.get('message', '未知错误')}")


def default_agent_thought_handler(chunk: Dict[str, Any]):
    """
    默认Agent思考处理函数，打印思考过程

    Args:
        chunk: Agent思考数据块
    """
    print(f"\n\n[思考] {chunk.get('position')}:")
    print(f"思考: {chunk.get('thought')}")

    if "tool" in chunk:
        print(f"工具: {chunk.get('tool')}")

    if "tool_input" in chunk:
        print(f"输入: {chunk.get('tool_input')}")

    if "observation" in chunk:
        print(f"观察: {chunk.get('observation')}")


def default_workflow_started_handler(chunk: Dict[str, Any]):
    """
    默认工作流开始处理函数

    Args:
        chunk: 工作流开始数据块
    """
    print(f"\n工作流开始: ID={chunk.get('id')}")


def default_node_started_handler(chunk: Dict[str, Any]):
    """
    默认节点开始处理函数

    Args:
        chunk: 节点开始数据块
    """
    print(f"节点开始: ID={chunk.get('node_id')}, 类型={chunk.get('node_type')}")


def default_node_finished_handler(chunk: Dict[str, Any]):
    """
    默认节点完成处理函数

    Args:
        chunk: 节点完成数据块
    """
    print(f"节点完成: ID={chunk.get('node_id')}, 状态={chunk.get('status')}")

    if chunk.get("outputs"):
        print(f"  输出: {chunk.get('outputs')}")


def default_workflow_finished_handler(chunk: Dict[str, Any]):
    """
    默认工作流完成处理函数

    Args:
        chunk: 工作流完成数据块
    """
    print(f"工作流完成: ID={chunk.get('id')}, 状态={chunk.get('status')}")

    if chunk.get("outputs"):
        print(f"  最终输出: {chunk.get('outputs')}")


def get_standard_handlers(client_type: str = "chatbot") -> Dict[str, Callable]:
    """
    获取标准事件处理函数集合

    Args:
        client_type: 客户端类型，可选值: 'chatbot', 'agent', 'text_generation', 'chatflow', 'workflow'

    Returns:
        Dict[str, Callable]: 处理函数映射
    """
    handlers = {
        "handle_message": default_message_handler,
        "handle_message_end": default_message_end_handler,
        "handle_error": default_error_handler,
    }

    if client_type == "agent":
        handlers["handle_agent_thought"] = default_agent_thought_handler

    if client_type in ("chatflow", "workflow"):
        handlers.update(
            {
                "handle_workflow_started": default_workflow_started_handler,
                "handle_node_started": default_node_started_handler,
                "handle_node_finished": default_node_finished_handler,
                "handle_workflow_finished": default_workflow_finished_handler,
            }
        )

    return handlers


# ===== 简单示例运行器 =====


def run_example(example_fn: Callable, *args, **kwargs):
    """
    运行单个示例函数并捕获异常

    Args:
        example_fn: 示例函数
        args: 位置参数
        kwargs: 关键字参数

    Returns:
        Any: 示例函数的返回值
    """
    try:
        print_section(f"运行 {example_fn.__name__}")
        if example_fn.__doc__:
            print(f"{example_fn.__doc__.strip()}\n")

        return example_fn(*args, **kwargs)

    except Exception as e:
        print(f"\n示例运行过程中发生错误: {e}")
        import traceback

        traceback.print_exc()
        return None

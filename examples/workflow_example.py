"""
Pydify WorkflowClient 使用示例

本示例展示了如何使用 WorkflowClient 类与 Dify Workflow 应用进行交互。

注意: 此示例需要Dify平台的Workflow模式应用API密钥才能正常工作。
如果遇到"input is required in input form"或类似错误，可能是因为:
1. 使用了非Workflow模式的应用API密钥
2. API版本不兼容 - 本代码库可能需要与特定版本的Dify API配合使用
3. API参数格式发生了变化

解决方法:
1. 确保使用正确的Workflow模式应用密钥
2. 查看Dify官方API文档了解最新的API参数格式
3. 如有必要，修改pydify/workflow.py中的run方法以匹配您的API版本需求
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

from pydify import WorkflowClient
from pydify.common import DifyAPIError

# 从环境变量或直接设置 API 密钥
API_KEY = os.environ.get("DIFY_API_KEY_WORKFLOW", "your_api_key")  # 使用样例API密钥
BASE_URL = os.environ.get("DIFY_BASE_URL", "your_base_url")  # 使用自定义API服务器地址
USER_ID = "user_123"  # 用户唯一标识

# 配置API请求参数
REQUEST_TIMEOUT = 30  # API请求超时时间(秒)
MAX_RETRIES = 3  # 最大重试次数
RETRY_DELAY = 2  # 重试延迟时间(秒)

# 初始化客户端
client = WorkflowClient(api_key=API_KEY, base_url=BASE_URL)


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

    # 获取请求参数
    request_kwargs = get_request_kwargs()

    try:
        info = client.get_app_info(**request_kwargs)
        pprint(info)
        return info
    except Exception as e:
        print(f"获取应用信息时出错: {str(e)}")
        import traceback

        traceback.print_exc()
        return None


def example_get_app_parameters():
    """获取应用参数示例"""
    print("\n==== 获取应用参数 ====")
    request_kwargs = get_request_kwargs()
    params = client.get_parameters(**request_kwargs)
    pprint(params)
    return params


def example_run_workflow_blocking():
    """以阻塞模式运行工作流示例"""
    print("\n==== 以阻塞模式运行工作流 ====")

    # 准备输入参数
    inputs = {
        "input": "请写一首关于人工智能的诗",
    }

    # 获取请求参数
    request_kwargs = get_request_kwargs()

    try:
        # 执行工作流（阻塞模式）
        result = client.run(
            inputs=inputs,
            user=USER_ID,
            response_mode="blocking",
            **request_kwargs,  # 传递请求参数
        )

        print("工作流执行结果:")
        pprint(result)
        return result
    except DifyAPIError as e:
        if "not_workflow_app" in str(e) or "app mode" in str(e).lower():
            print(f"错误: 当前API密钥不是Workflow模式应用，无法执行工作流")
        else:
            print(f"执行工作流时出错: {str(e)}")
            import traceback

            traceback.print_exc()
        return None


def example_run_workflow_streaming():
    """以流式模式运行工作流示例"""
    print("\n==== 以流式模式运行工作流 ====")

    # 准备输入参数
    inputs = {
        "input": "列出5个使用Python进行数据分析的库，并简要说明其用途",
    }

    # 定义事件处理函数
    def on_workflow_started(data):
        print(f"工作流开始: ID={data.get('id')}")

    def on_node_started(data):
        print(f"节点开始: ID={data.get('node_id')}, 类型={data.get('node_type')}")

    def on_node_finished(data):
        print(f"节点完成: ID={data.get('node_id')}, 状态={data.get('status')}")
        if data.get("outputs"):
            print(f"节点输出: {data.get('outputs')}")

    def on_workflow_finished(data):
        print(f"工作流完成: ID={data.get('id')}, 状态={data.get('status')}")
        if data.get("outputs"):
            print(f"最终输出: {data.get('outputs')}")

    # 获取请求参数
    request_kwargs = get_request_kwargs()

    try:
        # 执行工作流（流式模式）
        stream = client.run(
            inputs=inputs,
            user=USER_ID,
            response_mode="streaming",
            **request_kwargs,  # 传递请求参数
        )

        # 处理流式响应
        result = client.process_streaming_response(
            stream,
            handle_workflow_started=on_workflow_started,
            handle_node_started=on_node_started,
            handle_node_finished=on_node_finished,
            handle_workflow_finished=on_workflow_finished,
        )

        print("工作流执行完成，最终结果:")
        pprint(result)
        return result
    except DifyAPIError as e:
        if "not_workflow_app" in str(e) or "app mode" in str(e).lower():
            print(f"错误: 当前API密钥不是Workflow模式应用，无法执行工作流")
        else:
            print(f"执行流式工作流时出错: {str(e)}")
            import traceback

            traceback.print_exc()
        return None


def example_upload_file():
    """上传文件示例"""
    print("\n==== 上传文件 ====")

    # 确保文件存在
    file_path = "example.txt"
    if not os.path.exists(file_path):
        with open(file_path, "w") as f:
            f.write("这是一个测试文件，用于演示 Dify API 的文件上传功能。")

    # 上传文件
    try:
        result = client.upload_file(file_path, USER_ID)
        print("文件上传成功:")
        pprint(result)

        # 返回上传的文件ID，可用于后续调用
        return result.get("id")
    except Exception as e:
        print(f"文件上传失败: {e}")
        return None


def example_workflow_with_file():
    """使用文件运行工作流示例"""
    print("\n==== 使用文件运行工作流 ====")

    # 先上传文件
    file_id = example_upload_file()
    if not file_id:
        print("由于文件上传失败，跳过此示例")
        return

    # 准备输入参数和文件
    inputs = {
        "prompt": "分析这个文件并总结其内容",
    }

    files = [
        {"type": "document", "transfer_method": "local_file", "upload_file_id": file_id}
    ]

    # 执行工作流（阻塞模式）
    result = client.run(
        inputs=inputs, user=USER_ID, response_mode="blocking", files=files
    )

    print("工作流执行结果:")
    pprint(result)
    return result


def example_get_logs():
    """获取工作流日志示例"""
    print("\n==== 获取工作流日志 ====")

    # 获取请求参数
    request_kwargs = get_request_kwargs()

    try:
        logs = client.get_logs(limit=5, **request_kwargs)
        print(f"最近5条日志:")
        pprint(logs)
        return logs
    except DifyAPIError as e:
        if "not_workflow_app" in str(e) or "app mode" in str(e).lower():
            print(f"错误: 当前API密钥不是Workflow模式应用，无法获取工作流日志")
        else:
            print(f"获取工作流日志时出错: {str(e)}")
            import traceback

            traceback.print_exc()
        return None


def example_stop_task():
    """停止工作流任务示例"""
    print("\n==== 停止工作流任务 ====")
    print("注意: 此示例需要有一个正在运行的长任务才能演示")

    # 启动一个工作流任务
    inputs = {
        "prompt": "写一篇5000字的小说，描述未来世界中人工智能的发展",
    }

    # 获取请求参数
    request_kwargs = get_request_kwargs()

    # 执行工作流（流式模式）
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

        # 执行工作流并立即尝试停止
        stream = client.run(
            inputs=inputs,
            user=USER_ID,
            response_mode="streaming",
            **request_kwargs,  # 传递请求参数
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
        try:
            result = client.stop_task(task_id, USER_ID, **request_kwargs)
            print("停止任务结果:")
            pprint(result)
            return result
        except Exception as e:
            print(f"停止任务时出错: {str(e)}")
            import traceback

            traceback.print_exc()
            return None
    else:
        print("无法获取任务ID，跳过停止任务")
        return None


def validate_workflow_app():
    """验证当前API密钥是否对应Workflow模式的应用"""
    print("\n==== 验证应用类型 ====")
    try:
        # 获取请求参数
        request_kwargs = get_request_kwargs()

        # 尝试获取应用信息，检查API连接
        info = client.get_app_info(**request_kwargs)
        app_name = info.get("name", "未知")
        print(f"应用名称: {app_name}")

        # 提示用户验证API密钥和URL信息
        print(f"API Base URL: {BASE_URL}")
        print(f"API Key 前缀: {API_KEY[:6]}...")
        print(
            f"API Key 来源: {'环境变量' if os.environ.get('DIFY_API_KEY_WORKFLOW') else '代码中硬编码'}"
        )

        print("\n提示: 如果您尝试运行工作流时遇到参数格式错误，可能是由于:")
        print("1. API密钥不是Workflow模式应用的密钥")
        print("2. API版本与当前代码库不兼容")
        print("3. API参数格式要求已更改")

        # 简单提示用户确认
        response = input("\n确认继续运行示例? (y/n): ")
        if response.lower() != "y":
            print("退出示例")
            return False

        return True
    except Exception as e:
        print(f"✗ 验证失败: {str(e)}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("===== Pydify WorkflowClient 示例 =====")
    print(f"当前API地址: {BASE_URL}")
    print(
        f"当前API密钥: {API_KEY[:8]}...{API_KEY[-4:]}"
        if len(API_KEY) > 12
        else "当前API密钥未设置或格式不正确"
    )

    # 检查API密钥是否设置了有效值
    if API_KEY == "your_api_key":
        print("\n⚠️ 警告: 您使用的是默认API密钥。请设置正确的API密钥。")
        print("可以通过以下方式设置API密钥:")
        print("1. 在.env文件中设置 DIFY_API_KEY_WORKFLOW=你的密钥")
        print("2. 直接修改脚本中的API_KEY变量")
        sys.exit(1)

    if BASE_URL == "your_base_url":
        print("\n⚠️ 警告: 您使用的是默认API基础URL。请设置正确的API地址。")
        print("可以通过以下方式设置API地址:")
        print("1. 在.env文件中设置 DIFY_BASE_URL=你的API地址")
        print("2. 直接修改脚本中的BASE_URL变量")
        sys.exit(1)

    try:
        # 运行基本示例
        example_get_app_info()
        example_get_app_parameters()
        # 如果是Workflow应用，或者用户选择继续运行，则执行以下示例
        example_run_workflow_blocking()
        example_run_workflow_streaming()
        example_get_logs()

        # 运行文件相关示例和停止任务示例默认不启用
        # if is_workflow_app:
        #    example_workflow_with_file()
        #    example_stop_task()

    except KeyboardInterrupt:
        print("\n用户中断，退出示例运行")
    except Exception as e:
        print(f"示例运行过程中发生错误: {e}")
        import traceback

        traceback.print_exc()

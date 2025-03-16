"""
Pydify WorkflowClient 使用示例

本示例展示了如何使用 WorkflowClient 类与 Dify Workflow 应用进行交互。
"""
import os
import sys
import base64
from pprint import pprint

# 将父目录添加到 sys.path，使示例可以直接运行
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from pydify import WorkflowClient

# 从环境变量或直接设置 API 密钥
API_KEY = os.environ.get("DIFY_API_KEY", "your_api_key_here")
BASE_URL = os.environ.get("DIFY_BASE_URL", "http://your-dify-instance.com/v1")
USER_ID = "user_123"  # 用户唯一标识

# 初始化客户端
client = WorkflowClient(api_key=API_KEY, base_url=BASE_URL)

def example_get_app_info():
    """获取应用信息示例"""
    print("\n==== 获取应用信息 ====")
    info = client.get_app_info()
    pprint(info)
    return info

def example_run_workflow_blocking():
    """以阻塞模式运行工作流示例"""
    print("\n==== 以阻塞模式运行工作流 ====")
    # 准备输入参数
    inputs = {
        "prompt": "请写一首关于人工智能的诗",
    }
    
    # 执行工作流（阻塞模式）
    result = client.run(
        inputs=inputs,
        user=USER_ID,
        response_mode="blocking"
    )
    
    print("工作流执行结果:")
    pprint(result)
    return result

def example_run_workflow_streaming():
    """以流式模式运行工作流示例"""
    print("\n==== 以流式模式运行工作流 ====")
    
    # 准备输入参数
    inputs = {
        "prompt": "列出5个使用Python进行数据分析的库，并简要说明其用途",
    }
    
    # 定义事件处理函数
    def on_workflow_started(data):
        print(f"工作流开始: ID={data.get('id')}")
    
    def on_node_started(data):
        print(f"节点开始: ID={data.get('node_id')}, 类型={data.get('node_type')}")
    
    def on_node_finished(data):
        print(f"节点完成: ID={data.get('node_id')}, 状态={data.get('status')}")
        if data.get('outputs'):
            print(f"节点输出: {data.get('outputs')}")
    
    def on_workflow_finished(data):
        print(f"工作流完成: ID={data.get('id')}, 状态={data.get('status')}")
        if data.get('outputs'):
            print(f"最终输出: {data.get('outputs')}")
    
    # 执行工作流（流式模式）
    stream = client.run(
        inputs=inputs,
        user=USER_ID,
        response_mode="streaming"
    )
    
    # 处理流式响应
    result = client.process_streaming_response(
        stream,
        handle_workflow_started=on_workflow_started,
        handle_node_started=on_node_started,
        handle_node_finished=on_node_finished,
        handle_workflow_finished=on_workflow_finished
    )
    
    print("工作流执行完成，最终结果:")
    pprint(result)
    return result

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
    
    files = [{
        "type": "document",
        "transfer_method": "local_file",
        "upload_file_id": file_id
    }]
    
    # 执行工作流（阻塞模式）
    result = client.run(
        inputs=inputs,
        user=USER_ID,
        response_mode="blocking",
        files=files
    )
    
    print("工作流执行结果:")
    pprint(result)
    return result

def example_get_logs():
    """获取工作流日志示例"""
    print("\n==== 获取工作流日志 ====")
    logs = client.get_logs(limit=5)
    print(f"最近5条日志:")
    pprint(logs)
    return logs

def example_stop_task():
    """停止工作流任务示例"""
    print("\n==== 停止工作流任务 ====")
    print("注意: 此示例需要有一个正在运行的长任务才能演示")
    
    # 启动一个工作流任务
    inputs = {
        "prompt": "写一篇5000字的小说，描述未来世界中人工智能的发展",
    }
    
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
        result = client.stop_task(task_id, USER_ID)
        print("停止任务结果:")
        pprint(result)
        return result
    else:
        print("无法获取任务ID，跳过停止任务")
        return None

if __name__ == "__main__":
    print("===== Pydify WorkflowClient 示例 =====")
    
    try:
        # 运行基本示例
        example_get_app_info()
        example_run_workflow_blocking()
        example_run_workflow_streaming()
        
        # 运行文件相关示例
        # 注意：文件上传需要实际的Dify服务器支持
        # example_workflow_with_file()
        
        # 运行日志示例
        example_get_logs()
        
        # 运行停止任务示例
        # 注意：此示例需要长时间运行的任务才能正常演示
        # example_stop_task()
        
    except Exception as e:
        print(f"示例运行过程中发生错误: {e}")
        import traceback
        traceback.print_exc() 
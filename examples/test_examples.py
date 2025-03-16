import importlib
import json
import os
import sys
import traceback

import requests
from requests.exceptions import RequestException

API_KEYS = {
    # 'chatbot': 'app-mDB080ZuQUDyS82Rq0NtY7oS',
    # 'workflow': 'app-LXUWuMxaBjVvocdTetbudqCt',
    # 'chatflow': 'app-1paAYV2MD2HTglzCdiBDeCXD',
    "agent": "app-JH2PWol59GDhOfLpB1Qwvts3",
    # 'text_generation': 'app-OdRBvIBtBvyDntkEl9TI5YnS'
}

# 设置API基础URL
DIFY_BASE_URL = "http://sandanapp.com:8080/v1"

# 将父目录添加到 sys.path，使示例可以直接运行
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# 引入模块
from utils import print_header

from pydify.common import DifyBaseClient


# 首先测试API连接是否正常
def test_api_connection():
    """测试API连接是否正常工作"""
    print_header("测试API连接")

    # 使用第一个可用的API密钥
    api_key = next(iter(API_KEYS.values()))

    # 创建临时客户端
    client = DifyBaseClient(api_key=api_key, base_url=DIFY_BASE_URL)

    try:
        # 修补DifyBaseClient中的get方法，添加安全处理
        original_get = DifyBaseClient.get

        def safe_get(self, endpoint, **kwargs):
            """添加错误处理的安全get方法"""
            try:
                response = self._request("GET", endpoint, **kwargs)
                if not response.text.strip():
                    print(f"警告: API返回空响应 ({endpoint})")
                    return {}
                return response.json()
            except json.JSONDecodeError:
                print(f"警告: 无法解析API响应为JSON ({endpoint})")
                print(f"响应内容: {response.text[:100]}")
                return {}
            except Exception as e:
                print(f"API请求异常 ({endpoint}): {str(e)}")
                return {}

        # 应用补丁
        DifyBaseClient.get = safe_get

        # 测试API连接
        response = requests.get(
            url=f"{DIFY_BASE_URL}/ping", headers={"Authorization": f"Bearer {api_key}"}
        )

        if response.status_code == 200:
            print("✓ API连接正常")
            try:
                print(f"响应: {response.json()}")
            except json.JSONDecodeError:
                print(f"响应: {response.text[:100]}")
        else:
            print(f"✗ API连接失败: {response.status_code}")
            print(f"响应: {response.text[:100]}")

    except RequestException as e:
        print(f"✗ 无法连接到API: {str(e)}")

    return True  # 即使连接失败也继续测试


def run_examples():
    """运行所有示例"""
    # 测试API连接
    test_api_connection()

    for app_name, app_id in API_KEYS.items():
        print_header(f"测试 {app_name} 应用")
        print(f"API Key: {app_id}")

        # 设置环境变量
        os.environ["DIFY_API_KEY"] = app_id
        os.environ["DIFY_BASE_URL"] = DIFY_BASE_URL

        # 导入示例模块
        try:
            module_name = f"{app_name}_example"
            module = importlib.import_module(module_name)

            # 运行示例函数
            try:
                if hasattr(module, "example_get_app_info"):
                    print("\n运行 example_get_app_info:")
                    result = module.example_get_app_info()
                    if result:
                        print(f"结果: {result}")

                if hasattr(module, "example_get_parameters"):
                    print("\n运行 example_get_parameters:")
                    result = module.example_get_parameters()
                    if result:
                        print(f"结果: {result}")

            except Exception as e:
                print(f"\n示例运行过程中发生错误: {str(e)}")
                traceback.print_exc()

        except ImportError as e:
            print(f"无法导入模块 {module_name}: {str(e)}")


if __name__ == "__main__":
    run_examples()

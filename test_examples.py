import os
import sys
import importlib
import traceback
import requests
import json
from requests.exceptions import RequestException

API_KEYS = {
    # 'chatbot': 'app-mDB080ZuQUDyS82Rq0NtY7oS',
    # 'workflow': 'app-LXUWuMxaBjVvocdTetbudqCt',
    # 'chatflow': 'app-1paAYV2MD2HTglzCdiBDeCXD',
    'agent': 'app-JH2PWol59GDhOfLpB1Qwvts3',
    # 'text_generation': 'app-OdRBvIBtBvyDntkEl9TI5YnS'
}

# 设置API基础URL - 尝试不同的URL格式之一
DIFY_BASE_URLS = [
    "https://api.dify.ai/v1",          # 标准生产环境
    "http://sandanapp.com/v1",         # 原始URL格式
    "http://sandanapp.com/api/v1",     # 可能的API路径
    "http://sandanapp.com",            # 仅域名
]

# 将父目录添加到 sys.path，使示例可以直接运行
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 引入模块
from utils import print_header

# 首先测试API连接是否正常
def test_api_connection():
    """测试API连接是否正常工作"""
    print_header("测试API连接")
    
    # 使用第一个可用的API密钥
    api_key = next(iter(API_KEYS.values()))
    print(f"测试API密钥: {api_key}")
    
    # 尝试所有配置的基础URL
    print("\n尝试多个API基础URL:")
    
    working_url = None
    
    for base_url in DIFY_BASE_URLS:
        print(f"\n测试基础URL: {base_url}")
        
        # 尝试几个不同的端点
        endpoints = [
            "/ping",  # 简单的ping
            "",       # 仅基础URL
            "/apps",  # 应用列表
        ]
        
        for endpoint in endpoints:
            test_url = f"{base_url}{endpoint}"
            print(f"  尝试连接: {test_url}")
            
            try:
                response = requests.get(
                    url=test_url,
                    headers={"Authorization": f"Bearer {api_key}"},
                    timeout=5
                )
                
                print(f"  状态码: {response.status_code}")
                
                # 检查响应内容类型
                content_type = response.headers.get('Content-Type', '')
                print(f"  内容类型: {content_type}")
                
                # 如果是JSON内容类型或者状态码为2xx
                if 'application/json' in content_type or (200 <= response.status_code < 300):
                    try:
                        json_data = response.json()
                        # 找到了有效的URL!
                        print(f"  ✓ 成功解析JSON响应: {json.dumps(json_data, ensure_ascii=False)[:100]}")
                        working_url = base_url
                        break
                    except json.JSONDecodeError:
                        # 尝试检查是否是HTML响应
                        if '<html' in response.text.lower():
                            print("  ✗ 收到HTML响应而非JSON")
                        else:
                            print(f"  ✗ 非JSON响应: {response.text[:100]}")
                else:
                    print(f"  ✗ 响应内容类型不是JSON或状态码不是2xx")
                    
            except RequestException as e:
                print(f"  ✗ 请求异常: {str(e)}")
        
        # 如果找到工作的URL，跳出外层循环
        if working_url:
            break
    
    if working_url:
        print(f"\n找到工作的API基础URL: {working_url}")
        return working_url
    else:
        print("\n⚠️ 所有API连接测试失败。请检查API密钥和连接。")
        # 使用第一个URL作为默认值
        return DIFY_BASE_URLS[0]

def run_examples():
    """运行所有示例"""
    # 测试API连接并获取工作的URL
    working_url = test_api_connection()
    
    # 设置全局环境变量
    os.environ["DIFY_BASE_URL"] = working_url
    
    for app_name, app_id in API_KEYS.items():
        print_header(f"测试 {app_name} 应用")
        print(f"API Key: {app_id}")
        print(f"基础 URL: {working_url}")
        
        # 设置本次测试的环境变量
        os.environ["DIFY_API_KEY"] = app_id
        
        # 导入示例模块
        try:
            module_name = f"{app_name}_example"
            print(f"导入模块: {module_name}")
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
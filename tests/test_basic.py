"""基本的软件包导入测试。"""

def test_import():
    """测试包基本导入。"""
    import pydify
    
    # 确保可以导入所有客户端类
    from pydify import ChatbotClient
    from pydify import TextGenerationClient
    from pydify import AgentClient
    from pydify import WorkflowClient
    from pydify import ChatflowClient
    
    assert hasattr(pydify, "__version__") 
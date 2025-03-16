"""基本的软件包导入测试。"""


def test_import():
    """测试包基本导入。"""
    import pydify

    # 确保可以导入所有客户端类
    from pydify import (
        AgentClient,
        ChatbotClient,
        ChatflowClient,
        TextGenerationClient,
        WorkflowClient,
    )

    assert hasattr(pydify, "__version__")

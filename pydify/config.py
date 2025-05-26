VERSION = "2.4.0"


# Dify应用模式的枚举类，用于创建应用时指定应用类型
class DifyAppMode:
    """
    Dify应用模式的枚举类，定义了Dify支持的所有应用类型
    """

    CHAT = "chat"  # 聊天助手chatbot
    AGENT_CHAT = "agent-chat"  # Agent - 代理模式
    COMPLETION = "completion"  # 文本生成应用
    ADVANCED_CHAT = "advanced-chat"  # Chatflow - 高级聊天流
    WORKFLOW = "workflow"  # 工作流应用


DEFAULT_ICON = {"content": "🤖", "background": "#FFEAD5"}


class DifyToolParameterFormType:
    """
    Dify工具参数表单类型枚举类，定义了Dify支持的所有工具参数表单类型
    """

    FORM = "form"  # 表单类型
    LLM = "llm"  # LLM类型

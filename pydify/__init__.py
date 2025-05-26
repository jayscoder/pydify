"""
Pydify - Dify API的Python客户端库

这个库提供了与Dify API交互的简单方式，支持所有主要功能，
包括对话、文本生成、工作流、文件上传等。
"""

from .agent import AgentClient, AgentEvent
from .chatbot import ChatbotClient, ChatbotEvent
from .chatflow import ChatflowClient, ChatflowEvent
from .common import DifyBaseClient, DifyType
from .config import *
from .text_generation import TextGenerationClient, TextGenerationEvent
from .workflow import WorkflowClient, WorkflowEvent


def create_client(type: str, base_url: str, api_key: str) -> DifyBaseClient:
    if type == DifyType.Workflow:
        return WorkflowClient(base_url=base_url, api_key=api_key)
    elif type == DifyType.Chatbot:
        return ChatbotClient(base_url=base_url, api_key=api_key)
    elif type == "chatflow":
        return ChatflowClient(base_url=base_url, api_key=api_key)
    elif type == "agent":
        return AgentClient(base_url=base_url, api_key=api_key)
    elif type == "text_generation" or type == "text":
        return TextGenerationClient(base_url=base_url, api_key=api_key)
    else:
        raise ValueError(f"Invalid client type: {type}")


__version__ = VERSION
__all__ = [
    "WorkflowClient",
    "ChatbotClient",
    "ChatflowClient",
    "AgentClient",
    "TextGenerationClient",
    "create_client",
    "DifyType",
    "ChatbotEvent",
    "WorkflowEvent",
]

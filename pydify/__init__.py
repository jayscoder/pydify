"""
Pydify - Dify API的Python客户端库

这个库提供了与Dify API交互的简单方式，支持所有主要功能，
包括对话、文本生成、工作流、文件上传等。
"""

from .agent import AgentClient
from .chatbot import ChatbotClient
from .chatflow import ChatflowClient
from .text_generation import TextGenerationClient
from .workflow import WorkflowClient

__version__ = "0.1.4"
__all__ = [
    "WorkflowClient",
    "ChatbotClient",
    "ChatflowClient",
    "AgentClient",
    "TextGenerationClient",
]

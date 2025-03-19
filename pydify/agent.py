"""
Pydify - Dify Agent应用客户端

此模块提供与Dify Agent应用API交互的客户端。
Agent对话型应用能够迭代式的规划推理、自主工具调用，直至完成任务目标的智能助手。
"""

import json
import mimetypes
import os
from typing import Any, BinaryIO, Dict, Generator, List, Optional, Tuple, Union

from .common import DifyBaseClient, DifyType


class AgentClient(DifyBaseClient):
    """Dify Agent应用客户端类。

    提供与Dify Agent应用API交互的方法，包括发送消息、获取历史消息、管理会话、
    上传文件、语音转文字、文字转语音等功能。Agent应用支持迭代式规划推理和自主工具调用。
    """

    type = DifyType.Agent

    def send_message(
        self,
        query: str,
        user: str,
        response_mode: str = "streaming",
        inputs: Dict[str, Any] = None,
        conversation_id: str = None,
        files: List[Dict[str, Any]] = None,
        auto_generate_name: bool = True,
        **kwargs,  # 添加kwargs参数，用于接收额外的请求参数
    ) -> Generator[Dict[str, Any], None, None]:
        """
        发送对话消息，创建会话消息。在Agent模式下，只支持streaming流式模式。

        Args:
            query (str): 用户输入/提问内容
            user (str): 用户标识，用于定义终端用户的身份
            response_mode (str, optional): 响应模式，只支持'streaming'。默认为'streaming'
            inputs (Dict[str, Any], optional): App定义的各变量值。默认为None
            conversation_id (str, optional): 会话ID，基于之前的聊天记录继续对话时需提供。默认为None
            files (List[Dict[str, Any]], optional): 要包含在消息中的文件列表，每个文件为一个字典。默认为None
            auto_generate_name (bool, optional): 是否自动生成会话标题。默认为True
            **kwargs: 传递给底层API请求的额外参数，如timeout, max_retries等

        Returns:
            Generator[Dict[str, Any], None, None]: 返回字典生成器

        Raises:
            ValueError: 当提供了无效的参数时
            DifyAPIError: 当API请求失败时
        """
        if response_mode != "streaming":
            raise ValueError("Agent mode only supports streaming response mode")

        payload = {
            "query": query,
            "user": user,
            "response_mode": "streaming",
            "auto_generate_name": auto_generate_name,
            "inputs": inputs or {},  # 确保inputs参数总是存在，如果未提供则使用空字典
        }

        if conversation_id:
            payload["conversation_id"] = conversation_id

        if files:
            payload["files"] = files

        endpoint = "chat-messages"

        return self.post_stream(endpoint, json_data=payload, **kwargs)  # 传递额外参数

    def stop_response(self, task_id: str, user: str) -> Dict[str, Any]:
        """
        停止正在进行的响应流。此方法仅在流式模式下有效。

        Args:
            task_id (str): 任务唯一标识,可从流式响应的数据块中获取
            user (str): 用户唯一标识,需要与发送消息时的user参数保持一致

        Returns:
            Dict[str, Any]: 停止响应的结果,格式如下:
            {
                "result": "success"  # 表示成功停止响应
            }

        Raises:
            requests.HTTPError: API请求失败时抛出此异常,包含具体的错误信息
            DifyAPIError: Dify服务端返回错误时抛出此异常
        """
        endpoint = f"chat-messages/{task_id}/stop"
        payload = {"user": user}
        return self.post(endpoint, json_data=payload)

    def get_meta(self) -> Dict[str, Any]:
        """
        获取应用Meta信息，用于获取工具icon等。

        Returns:
            Dict[str, Any]: 应用Meta信息

        Raises:
            requests.HTTPError: 当API请求失败时
        """
        return self.get("meta")

    def process_streaming_response(
        self,
        stream_generator: Generator[Dict[str, Any], None, None],
        handle_message=None,
        handle_agent_message=None,
        handle_agent_thought=None,
        handle_message_file=None,
        handle_message_end=None,
        handle_tts_message=None,
        handle_tts_message_end=None,
        handle_message_replace=None,
        handle_error=None,
        handle_ping=None,
        break_on_error=True,
    ) -> Dict[str, Any]:
        """
        处理流式响应，调用相应事件处理器。

        Args:
            stream_generator: 流式响应生成器
            handle_message: LLM返回文本块事件处理函数
            handle_agent_message: Agent模式下返回文本块事件处理函数
            handle_agent_thought: Agent模式下思考步骤事件处理函数
            handle_message_file: 文件事件处理函数
            handle_message_end: 消息结束事件处理函数
            handle_tts_message: TTS音频流事件处理函数
            handle_tts_message_end: TTS音频流结束事件处理函数
            handle_message_replace: 消息内容替换事件处理函数
            handle_error: 错误事件处理函数
            handle_ping: ping事件处理函数
            break_on_error: 当遇到错误时是否中断处理，默认为True

        Returns:
            Dict[str, Any]: 处理结果，包含消息ID、会话ID等信息

        示例:
            ```python
            def on_agent_message(chunk):
                # 打印Agent返回的文本块
                print(f"{chunk['answer']}")

            def on_agent_thought(chunk):
                print(f"Agent思考: {chunk['thought']}")
                print(f"使用工具: {chunk['tool']}")
                print(f"工具输入: {chunk['tool_input']}")
                print(f"观察结果: {chunk['observation']}")

            def on_message_end(chunk):
                print(f"消息结束: ID={chunk['message_id']}")

            client = AgentClient(api_key)
            stream = client.send_message(
                query="帮我分析最近的股市走势",
                user="user123"
            )
            result = client.process_streaming_response(
                stream,
                handle_agent_message=on_agent_message,
                handle_agent_thought=on_agent_thought,
                handle_message_end=on_message_end
            )
            ```
        """
        result = {"agent_thoughts": []}
        answer_chunks = []

        for chunk in stream_generator:
            event = chunk.get("event")

            if event == "message" and handle_message:
                handle_message(chunk)
                # 累积回答内容
                if "answer" in chunk:
                    answer_chunks.append(chunk["answer"])
                # 保存消息和会话ID
                if "message_id" in chunk and not result.get("message_id"):
                    result["message_id"] = chunk["message_id"]
                if "conversation_id" in chunk and not result.get("conversation_id"):
                    result["conversation_id"] = chunk["conversation_id"]
                if "task_id" in chunk and not result.get("task_id"):
                    result["task_id"] = chunk["task_id"]

            elif event == "agent_message" and handle_agent_message:
                handle_agent_message(chunk)
                # 累积回答内容
                if "answer" in chunk:
                    answer_chunks.append(chunk["answer"])
                # 保存消息和会话ID
                if "message_id" in chunk and not result.get("message_id"):
                    result["message_id"] = chunk["message_id"]
                if "conversation_id" in chunk and not result.get("conversation_id"):
                    result["conversation_id"] = chunk["conversation_id"]
                if "task_id" in chunk and not result.get("task_id"):
                    result["task_id"] = chunk["task_id"]

            elif event == "agent_thought" and handle_agent_thought:
                if handle_agent_thought:
                    handle_agent_thought(chunk)
                # 保存Agent思考内容
                thought_data = {
                    "id": chunk.get("id"),
                    "position": chunk.get("position"),
                    "thought": chunk.get("thought"),
                    "observation": chunk.get("observation"),
                    "tool": chunk.get("tool"),
                    "tool_input": chunk.get("tool_input"),
                    "message_files": chunk.get("message_files", []),
                    "created_at": chunk.get("created_at"),
                }
                result["agent_thoughts"].append(thought_data)

            elif event == "message_file" and handle_message_file:
                handle_message_file(chunk)
                # 保存文件信息
                if not result.get("files"):
                    result["files"] = []
                result["files"].append(
                    {
                        "id": chunk.get("id"),
                        "type": chunk.get("type"),
                        "belongs_to": chunk.get("belongs_to"),
                        "url": chunk.get("url"),
                    }
                )

            elif event == "message_end" and handle_message_end:
                if handle_message_end:
                    handle_message_end(chunk)
                # 保存元数据
                if "metadata" in chunk:
                    result["metadata"] = chunk["metadata"]
                if "message_id" in chunk and not result.get("message_id"):
                    result["message_id"] = chunk["message_id"]
                if "conversation_id" in chunk and not result.get("conversation_id"):
                    result["conversation_id"] = chunk["conversation_id"]

            elif event == "tts_message" and handle_tts_message:
                handle_tts_message(chunk)

            elif event == "tts_message_end" and handle_tts_message_end:
                handle_tts_message_end(chunk)

            elif event == "message_replace" and handle_message_replace:
                handle_message_replace(chunk)
                # 替换回答内容
                if "answer" in chunk:
                    answer_chunks = [chunk["answer"]]

            elif event == "error" and handle_error:
                handle_error(chunk)
                if break_on_error:
                    # 添加错误信息到结果中
                    result["error"] = {
                        "status": chunk.get("status"),
                        "code": chunk.get("code"),
                        "message": chunk.get("message"),
                    }
                    break

            elif event == "ping" and handle_ping:
                handle_ping(chunk)

        # 合并所有回答块
        if answer_chunks:
            result["answer"] = "".join(answer_chunks)

        return result

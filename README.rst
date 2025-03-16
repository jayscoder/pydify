======
Pydify
======

Pydify是一个Python SDK，用于与Dify API进行交互。它提供了一组简单易用的客户端类，让您能够轻松地使用Dify的各种功能。

===========
功能特点
===========

* **多种应用类型支持**：支持Chatbot、Agent、Text Generation、Workflow和Chatflow应用类型
* **流式响应处理**：支持处理流式（streaming）返回的消息
* **文件上传**：支持上传图像等文件进行多模态理解
* **会话管理**：提供会话历史记录管理功能
* **文本到音频转换**：支持将文本转换为音频

====
安装
====

.. code-block:: bash

    pip install pydify

==========
快速开始
==========

以下是一个基本的聊天机器人示例：

.. code-block:: python

    from pydify import ChatbotClient
    
    # 初始化客户端
    client = ChatbotClient(
        api_key="your_api_key",
        app_id="your_app_id"
    )
    
    # 发送消息
    response = client.send_message("Hello, how are you?")
    print(response)
    
    # 流式响应处理
    def handle_message(message):
        print(f"接收到消息: {message}")
    
    def handle_end():
        print("消息结束")
    
    client.send_message(
        "Tell me a story",
        streaming=True,
        message_handler=handle_message,
        message_end_handler=handle_end
    )

更多示例请查看项目的examples目录。

=======
许可证
=======

MIT

==========
更多信息
==========

完整文档请参考项目的README.md文件或访问GitHub仓库。 
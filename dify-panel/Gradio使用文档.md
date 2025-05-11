# Gradio 使用手册

## 目录

1. [简介](#简介)
2. [快速开始](#快速开始)
3. [核心概念](#核心概念)
4. [组件详解](#组件详解)
5. [布局管理](#布局管理)
6. [高级特性](#高级特性)
7. [部署与分享](#部署与分享)
8. [最佳实践](#最佳实践)

## 简介

### 什么是 Gradio？

Gradio 是一个开源的 Python 库，用于快速构建机器学习模型、API 或任何 Python 函数的交互式 Web 界面。它的主要目标是让开发者能够轻松地将他们的模型和数据科学工作流程分享给他人，而无需复杂的 Web 开发知识。

### 主要特点

- 简单易用：几行代码即可创建功能完整的 Web 界面
- 丰富的组件：提供 30+ 预构建组件，支持文本、图像、音频等多种数据类型
- 灵活的布局：支持水平、垂直排列、选项卡、折叠面板等多种布局方式
- 易于分享：一键生成可分享的链接，方便远程访问
- 可扩展性：支持自定义组件和主题
- 多平台支持：可在 Jupyter Notebook、Google Colab 中运行，也可作为独立网页

## 快速开始

### 安装

```bash
pip install --upgrade gradio
```

### 第一个应用

```python
import gradio as gr

def greet(name):
    return f"Hello, {name}!"

# 创建界面
demo = gr.Interface(
    fn=greet,                # 要包装的函数
    inputs="textbox",        # 输入组件
    outputs="textbox",       # 输出组件
    title="问候应用",        # 应用标题
    description="输入你的名字，获取问候语"  # 应用描述
)

# 启动应用
demo.launch()
```

### 运行方式

1. 保存为 `app.py`
2. 运行命令：
   ```bash
   python app.py
   ```
   或使用热重载模式：
   ```bash
   gradio app.py
   ```

## 核心概念

### Interface 类

Interface 是 Gradio 的主要高级类，用于快速创建简单的应用界面。

#### 基本用法

```python
import gradio as gr

def process_image(image):
    # 处理图像的函数
    return processed_image

demo = gr.Interface(
    fn=process_image,
    inputs=gr.Image(),
    outputs=gr.Image(),
    examples=[["example1.jpg"], ["example2.jpg"]]
)
```

#### 主要参数

- `fn`: 要包装的 Python 函数
- `inputs`: 输入组件
- `outputs`: 输出组件
- `title`: 应用标题
- `description`: 应用描述
- `examples`: 示例输入
- `theme`: 界面主题

### Blocks 类

Blocks 提供了更灵活的界面构建方式，适合创建复杂的应用。

#### 基本用法

```python
import gradio as gr

with gr.Blocks() as demo:
    gr.Markdown("# 图像处理应用")

    with gr.Row():
        input_image = gr.Image()
        output_image = gr.Image()

    with gr.Row():
        process_btn = gr.Button("处理图像")
        clear_btn = gr.Button("清除")

    process_btn.click(
        fn=process_image,
        inputs=input_image,
        outputs=output_image
    )

    clear_btn.click(
        fn=lambda: None,
        inputs=[],
        outputs=[input_image, output_image]
    )
```

## 组件详解

### 基础组件

#### 文本框 (Textbox)

```python
textbox = gr.Textbox(
    label="输入文本",
    placeholder="请输入...",
    lines=3,
    max_lines=5
)
```

#### 图像 (Image)

```python
image = gr.Image(
    label="上传图片",
    type="pil",
    height=300,
    width=300
)
```

#### 音频 (Audio)

```python
audio = gr.Audio(
    label="录制音频",
    type="numpy",
    format="wav"
)
```

#### 按钮 (Button)

```python
button = gr.Button(
    value="点击我",
    variant="primary",
    size="lg"
)
```

### 布局组件

#### 行 (Row)

```python
with gr.Row():
    gr.Textbox(label="输入1")
    gr.Textbox(label="输入2")
```

#### 列 (Column)

```python
with gr.Column():
    gr.Textbox(label="输入1")
    gr.Textbox(label="输入2")
```

#### 选项卡 (Tab)

```python
with gr.Tab("选项卡1"):
    gr.Textbox(label="选项卡1内容")
with gr.Tab("选项卡2"):
    gr.Textbox(label="选项卡2内容")
```

## 高级特性

### 状态管理

```python
with gr.Blocks() as demo:
    counter = gr.State(0)

    def increment(counter):
        return counter + 1

    button = gr.Button("增加")
    number = gr.Number()

    button.click(
        fn=increment,
        inputs=counter,
        outputs=[counter, number]
    )
```

### 主题定制

```python
demo = gr.Interface(
    fn=process_image,
    inputs=gr.Image(),
    outputs=gr.Image(),
    theme=gr.themes.Soft()
)
```

### 自定义 CSS

```python
demo = gr.Interface(
    fn=process_image,
    inputs=gr.Image(),
    outputs=gr.Image(),
    css="""
    .gradio-container {
        background-color: #f0f0f0;
    }
    """
)
```

## 部署与分享

### 本地部署

```python
demo.launch(
    server_name="0.0.0.0",
    server_port=7860,
    share=True
)
```

### Hugging Face Spaces 部署

1. 创建 `requirements.txt`
2. 创建 `app.py`
3. 上传到 Hugging Face Spaces

## 最佳实践

### 性能优化

1. 使用缓存装饰器

```python
@gr.cache()
def process_image(image):
    # 处理图像
    return result
```

2. 设置并发限制

```python
demo.queue(concurrency_count=3)
```

### 错误处理

```python
def process_with_error_handling(input_data):
    try:
        result = process(input_data)
        return result
    except Exception as e:
        return f"错误: {str(e)}"
```

### 安全性

```python
demo.launch(
    auth=("username", "password"),
    auth_message="请输入用户名和密码"
)
```

## 常见问题

### 1. 如何处理大文件上传？

- 使用 `gr.File()` 组件
- 设置适当的文件大小限制
- 考虑使用流式处理

### 2. 如何实现实时更新？

- 使用 `gr.Textbox(interactive=True)`
- 设置 `every` 参数实现定期更新

### 3. 如何保存用户输入？

- 使用 `gr.State()`
- 实现数据持久化
- 使用数据库存储

## 示例应用

### 图像分类应用

```python
import gradio as gr
import torch
from torchvision import transforms

def classify_image(image):
    # 图像预处理
    transform = transforms.Compose([
        transforms.Resize(256),
        transforms.CenterCrop(224),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    ])

    # 模型预测
    image_tensor = transform(image).unsqueeze(0)
    with torch.no_grad():
        output = model(image_tensor)

    # 返回预测结果
    return f"预测类别: {output.argmax().item()}"

demo = gr.Interface(
    fn=classify_image,
    inputs=gr.Image(type="pil"),
    outputs=gr.Textbox(),
    examples=[["example1.jpg"], ["example2.jpg"]]
)
```

### 聊天机器人应用

```python
import gradio as gr

def respond(message, chat_history):
    bot_message = f"你说: {message}"
    chat_history.append((message, bot_message))
    return "", chat_history

demo = gr.ChatInterface(
    fn=respond,
    chatbot=gr.Chatbot(),
    textbox=gr.Textbox(placeholder="在这里输入消息..."),
    title="简单聊天机器人",
    description="这是一个简单的聊天机器人示例"
)
```

## 更新日志

### 版本 3.0.0

- 新增 Blocks API
- 改进组件系统
- 添加主题支持

### 版本 2.0.0

- 添加事件系统
- 改进布局管理
- 新增多个组件

## 参考资源

- [官方文档](https://gradio.app/docs)
- [GitHub 仓库](https://github.com/gradio-app/gradio)
- [示例库](https://gradio.app/gallery)
- [社区论坛](https://discuss.huggingface.co/c/gradio)

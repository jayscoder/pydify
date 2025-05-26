# Dify DSL 可视化工具

这个项目是基于 Streamlit 的 Dify 工作流 DSL 可视化工具，用于帮助用户理解和分析 Dify 中的工作流程图结构。

## 功能特性

- **DSL 图形可视化**：将 Dify 的 DSL JSON 结构转换为直观的可视化图表
- **交互式节点**：支持节点拖拽和点击查看详情
- **节点类型区分**：不同类型的节点使用不同颜色直观展示
- **统计分析**：提供工作流节点和边的统计信息
- **支持多种输入方式**：文件上传或直接粘贴 DSL 内容

## 安装与使用

### 安装依赖

```bash
pip install streamlit streamlit-agraph
```

### 启动应用

```bash
cd dify-panel
streamlit run app.py
```

或者直接运行可视化页面:

```bash
cd dify-panel
streamlit run pages/dsl_visualization.py
```

## 使用方法

1. 启动应用后，选择"上传 JSON 文件"或"粘贴 DSL 文本"输入 DSL 数据
2. 点击"加载示例数据"可快速查看示例效果
3. 查看生成的可视化图表，可拖动节点调整位置
4. 点击节点可查看节点详细信息

## 节点类型说明

- **开始节点(绿色)**：工作流的起始点
- **结束节点(红色)**：工作流的终止点
- **LLM 节点(蓝色)**：大语言模型处理节点
- **代码节点(橙色)**：执行代码逻辑的节点
- **模板转换节点(紫色)**：处理内容模板转换的节点
- **条件分支节点(黄色)**：根据条件控制流程走向的节点
- **工具节点(棕色)**：调用外部工具或服务的节点

## 项目结构

```
dify-panel/
├── app.py                  # 主应用入口
├── utils/
│   ├── dsl_components.py   # DSL图形渲染组件
│   └── ...
├── pages/
│   └── dsl_visualization.py # DSL可视化页面
└── examples/
    └── example_dsl.json    # 示例DSL数据
```

## 技术栈

- **Streamlit**：构建 Web 界面
- **streamlit-agraph**：处理图形可视化
- **Python**：核心逻辑实现

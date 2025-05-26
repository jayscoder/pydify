# StreamlitAGraph 使用文档

`streamlit-agraph`是一个用于 Streamlit 的交互式图形可视化组件，基于[react-graph-vis](https://github.com/crubier/react-graph-vis)实现。该组件让你能够在 Streamlit 应用中创建交互式的网络图表，适合展示各种关系数据。

## 安装

```bash
pip install streamlit-agraph
```

## 基本组件

### Node（节点）

节点是图中的基本元素，可以用来表示各种实体。

```python
from streamlit_agraph import Node

# 基本节点
node = Node(id="node1", label="节点1")

# 设置节点形状和大小
node = Node(id="node2", label="节点2", shape="dot", size=25)

# 使用图片作为节点
node = Node(
    id="node3",
    label="节点3",
    shape="circularImage",
    image="https://example.com/image.png"
)

# 设置节点颜色
node = Node(id="node4", label="节点4", color="#F7A7A6")

# 添加链接功能（双击可打开链接）
node = Node(id="node5", label="节点5", link="https://example.com")

# 设置节点分组（用于层次结构和颜色分组）
node = Node(id="node6", label="节点6", group="group1")
```

节点支持的形状包括：

- `dot`（默认）：圆形
- `circularImage`：圆形图片
- `diamond`：菱形
- `square`：正方形
- `triangle`：三角形
- `triangleDown`：倒三角形
- `hexagon`：六边形
- `star`：星形
- `image`：图片
- `icon`：图标

### Edge（边）

边用于连接节点，表示节点之间的关系。

```python
from streamlit_agraph import Edge

# 基本边
edge = Edge(source="node1", target="node2")

# 添加标签
edge = Edge(source="node1", target="node2", label="关系")

# 设置颜色
edge = Edge(source="node1", target="node2", color="#F48B94")

# 设置曲线类型
edge = Edge(source="node1", target="node2", type="CURVE_SMOOTH")
```

边支持的类型包括：

- `STRAIGHT`：直线
- `CURVE_SMOOTH`：平滑曲线
- `CURVE_FULL`：完整曲线

### Config（配置）

Config 用于配置图的显示样式和行为。

```python
from streamlit_agraph import Config

# 基本配置
config = Config(
    width=750,      # 图的宽度（像素）
    height=750,     # 图的高度（像素）
    directed=True,  # 是否为有向图
    physics=True,   # 是否启用物理引擎
    hierarchical=False  # 是否启用层次布局
)

# 高级配置
config = Config(
    width=750,
    height=750,
    directed=True,
    physics=True,
    hierarchical=False,
    nodeHighlightBehavior=True,  # 节点高亮行为
    highlightColor="#F7A7A6",    # 高亮颜色
    collapsible=True,            # 是否可折叠
    node={'labelProperty': 'label'},  # 节点标签属性
    link={'labelProperty': 'label', 'renderLabel': True}  # 边标签属性
)
```

## 基本用法

### 创建简单图表

```python
import streamlit as st
from streamlit_agraph import agraph, Node, Edge, Config

# 创建节点
nodes = []
nodes.append(Node(id="node1", label="节点1", size=25))
nodes.append(Node(id="node2", label="节点2", size=25))
nodes.append(Node(id="node3", label="节点3", size=25))

# 创建边
edges = []
edges.append(Edge(source="node1", target="node2", label="连接到"))
edges.append(Edge(source="node2", target="node3", label="连接到"))

# 配置
config = Config(
    width=750,
    height=500,
    directed=True,
    physics=True,
    hierarchical=False
)

# 渲染图表
return_value = agraph(nodes=nodes, edges=edges, config=config)

# 获取用户交互返回值（被点击的节点ID）
st.write(return_value)
```

### 使用图片节点

```python
import streamlit as st
from streamlit_agraph import agraph, Node, Edge, Config

nodes = []
edges = []

# 创建带图片的节点
nodes.append(
    Node(
        id="Spiderman",
        label="蜘蛛侠",
        size=25,
        shape="circularImage",
        image="http://marvel-force-chart.surge.sh/marvel_force_chart_img/top_spiderman.png"
    )
)
nodes.append(
    Node(
        id="Captain_Marvel",
        label="惊奇队长",
        size=25,
        shape="circularImage",
        image="http://marvel-force-chart.surge.sh/marvel_force_chart_img/top_captainmarvel.png"
    )
)

# 创建边
edges.append(
    Edge(
        source="Captain_Marvel",
        label="朋友关系",
        target="Spiderman"
    )
)

# 配置
config = Config(
    width=750,
    height=500,
    directed=True,
    physics=True,
    hierarchical=False
)

# 渲染图表
return_value = agraph(nodes=nodes, edges=edges, config=config)
```

## 高级功能

### 使用 ConfigBuilder 构建配置

ConfigBuilder 提供了一个方便的方式通过 Streamlit 侧边栏来调整图表配置。

```python
import streamlit as st
from streamlit_agraph import agraph, Node, Edge, Config, ConfigBuilder

# 创建节点和边
nodes = []
edges = []
# 添加节点和边...

# 使用ConfigBuilder
config_builder = ConfigBuilder(nodes)
config = config_builder.build()

# 使用构建的配置渲染图表
return_value = agraph(nodes=nodes, edges=edges, config=config)
```

ConfigBuilder 会在 Streamlit 侧边栏中添加以下配置选项：

- 基本配置：宽度、高度、是否有向
- 物理引擎配置：是否启用物理引擎、求解器选择、最小/最大速度等
- 层次结构配置：是否启用层次布局、层间距、节点间距等
- 分组配置：为不同分组设置颜色

### 保存和加载配置

```python
# 保存配置到文件
config.save("config.json")

# 从文件加载配置
config = Config(from_json="config.json")
```

### 分层布局

创建层次结构图表：

```python
import streamlit as st
from streamlit_agraph import agraph, Node, Edge, Config

# 创建节点和边
nodes = []
edges = []

# 添加根节点
nodes.append(Node(id="root", label="根节点", size=25))

# 添加第一层节点
for i in range(3):
    node_id = f"node_{i}"
    nodes.append(Node(id=node_id, label=f"节点 {i}", size=20))
    edges.append(Edge(source=node_id, target="root"))

    # 添加第二层节点
    for j in range(2):
        child_id = f"child_{i}_{j}"
        nodes.append(Node(id=child_id, label=f"子节点 {i}_{j}", size=15))
        edges.append(Edge(source=child_id, target=node_id))

# 配置分层布局
config = Config(
    width=750,
    height=500,
    directed=True,
    physics=False,  # 关闭物理引擎以保持层次结构稳定
    hierarchical=True,
    # 层次结构配置
    levelSeparation=150,  # 层级间距
    nodeSpacing=100,      # 同层节点间距
    treeSpacing=200,      # 树之间的间距
    direction="UD",       # 方向：UD (上到下), DU (下到上), LR (左到右), RL (右到左)
    sortMethod="hubsize"  # 排序方法：hubsize, directed
)

# 渲染图表
return_value = agraph(nodes=nodes, edges=edges, config=config)
```

### 与 NetworkX 集成

`streamlit-agraph`可以与 NetworkX 库集成，将 NetworkX 的图转换为可视化组件。

```python
import networkx as nx
import streamlit as st
from streamlit_agraph import agraph, Node, Edge, Config

# 创建NetworkX图
G = nx.karate_club_graph()

# 转换为Node和Edge列表
nodes = [Node(id=i, label=str(i), size=20) for i in G.nodes]
edges = [Edge(source=i, target=j) for i, j in G.edges]

# 配置
config = Config(
    width=750,
    height=500,
    directed=False,
    physics=True,
    hierarchical=False
)

# 渲染图表
return_value = agraph(nodes=nodes, edges=edges, config=config)
```

### 使用 TripleStore

TripleStore 可用于处理 RDF 数据和创建语义网络可视化。

```python
from rdflib import Graph
from streamlit_agraph import TripleStore, agraph, Config

# 加载RDF图
graph = Graph()
graph.parse("http://www.w3.org/People/Berners-Lee/card")

# 创建TripleStore
store = TripleStore()

# 添加三元组
for subj, pred, obj in graph:
    store.add_triple(subj, pred, obj, "")

# 配置
config = Config(
    width=1000,
    height=800,
    directed=True,
    physics=True,
    hierarchical=False
)

# 渲染图表
agraph(list(store.getNodes()), list(store.getEdges()), config=config)
```

### 使用 GraphAlgos

GraphAlgos 类提供了一些基本的图算法功能。

```python
import streamlit as st
from streamlit_agraph import GraphAlgos, TripleStore, Node, Edge, agraph, Config

# 创建TripleStore或直接创建节点和边
store = TripleStore()
# 添加节点和边...

# 创建GraphAlgos对象
algos = GraphAlgos(store)

# 计算图密度
density = algos.density()
st.write(f"图密度: {density}")

# 计算最短路径
path = algos.shortest_path("node1", "node5")
st.write(f"最短路径: {path}")
```

## 实际应用示例

### 卡拉泰俱乐部社交网络

```python
import networkx as nx
import streamlit as st
from streamlit_agraph import agraph, Node, Edge, Config

# 生成Zachary卡拉泰俱乐部图
G = nx.karate_club_graph()

# 创建节点和边
nodes = [Node(id=i, label=str(i), size=20) for i in range(len(G.nodes))]
edges = [Edge(source=i, target=j, type="CURVE_SMOOTH") for (i, j) in G.edges]

# 配置
config = Config(
    width=700,
    height=700,
    directed=True,
    nodeHighlightBehavior=True,
    highlightColor="#F7A7A6",
    collapsible=True,
    node={'labelProperty': 'label'},
    link={'labelProperty': 'label', 'renderLabel': True}
)

# 渲染图表
return_value = agraph(nodes=nodes, edges=edges, config=config)
```

### 自我中心网络

```python
import networkx as nx
import streamlit as st
from streamlit_agraph import agraph, Node, Edge, Config

# 创建Barabasi-Albert图模型
n = 2000  # 节点数
m = 2     # 每个新节点连接的边数
G = nx.generators.barabasi_albert_graph(n, m)

# 找到度最大的节点
most_connected_node = sorted(G.degree, key=lambda x: x[1], reverse=True)[0]

# 创建自我中心网络
hub_ego = nx.ego_graph(G, most_connected_node[0])

# 创建节点和边
nodes = [Node(id=i, label=str(i), size=20) for i in hub_ego.nodes]
edges = [Edge(source=i, target=j, type="CURVE_SMOOTH") for (i, j) in G.edges
        if i in hub_ego.nodes and j in hub_ego.nodes]

# 配置
config = Config(
    width=700,
    height=700,
    directed=True,
    nodeHighlightBehavior=False,
    highlightColor="#F7A7A6",
    collapsible=False,
    node={'labelProperty': 'label'}
)

# 渲染图表
return_value = agraph(nodes=nodes, edges=edges, config=config)
```

### 决策树可视化

```python
import json
import pygraphviz as pgv
import streamlit as st
from sklearn import tree
from sklearn.datasets import load_iris
from streamlit_agraph import Config, Edge, Node, agraph

# 加载鸢尾花数据集
with st.spinner("加载鸢尾花数据集"):
    iris = load_iris()

# 训练决策树分类器
with st.spinner("训练决策树分类器"):
    clf = tree.DecisionTreeClassifier()
    clf = clf.fit(iris.data, iris.target)

# 导出为DOT格式
dot_data = tree.export_graphviz(clf,
                               out_file=None,
                               feature_names=iris.feature_names)

# 解析DOT数据
G = pgv.AGraph().from_string(dot_data)

# 创建节点和边
nodes = []
edges = []
for node in G.nodes():
    nodes.append(Node(id=node,
                     label=node.attr['label'].split('\\n')[0],
                     symbolType='square'))
for edge in G.edges():
    edges.append(
        Edge(source=edge[0],
             target=edge[1],
             type="STRAIGHT")
    )

# 侧边栏配置选项
layout = st.sidebar.selectbox('布局',['dot', 'neato', 'circo', 'fdp', 'sfdp'])
rankdir = st.sidebar.selectbox("方向", ['BT', 'TB', 'LR', 'RL'])
ranksep = st.sidebar.slider("层间距", min_value=0, max_value=10)
nodesep = st.sidebar.slider("节点间距", min_value=0, max_value=10)

# 配置
config = Config(
    width=2000,
    height=1000,
    graphviz_layout=layout,
    graphviz_config={"rankdir": rankdir, "ranksep": ranksep, "nodesep": nodesep},
    directed=True,
    nodeHighlightBehavior=True,
    highlightColor="#F7A7A6",
    collapsible=True,
    node={'labelProperty':'label'},
    link={'labelProperty': 'label', 'renderLabel': True},
    maxZoom=2,
    minZoom=0.1,
    staticGraphWithDragAndDrop=False,
    staticGraph=False,
    initialZoom=1
)

# 渲染图表
return_value = agraph(nodes=nodes, edges=edges, config=config)
```

## 配置参考

### 基本配置选项

| 参数                  | 类型  | 默认值    | 描述             |
| --------------------- | ----- | --------- | ---------------- |
| width                 | int   | 750       | 图宽度(像素)     |
| height                | int   | 750       | 图高度(像素)     |
| directed              | bool  | True      | 是否为有向图     |
| physics               | bool  | True      | 是否启用物理引擎 |
| hierarchical          | bool  | False     | 是否启用层次布局 |
| nodeHighlightBehavior | bool  | False     | 节点高亮行为     |
| highlightColor        | str   | "#F7A7A6" | 高亮颜色         |
| collapsible           | bool  | False     | 是否可折叠       |
| maxZoom               | float | 2.0       | 最大缩放级别     |
| minZoom               | float | 0.1       | 最小缩放级别     |
| initialZoom           | float | 1.0       | 初始缩放级别     |

### 物理引擎配置

| 参数          | 类型  | 默认值      | 描述                                                                                |
| ------------- | ----- | ----------- | ----------------------------------------------------------------------------------- |
| solver        | str   | "barnesHut" | 物理求解器（"barnesHut", "forceAtlas2Based", "hierarchicalRepulsion", "repulsion"） |
| minVelocity   | float | 1.0         | 最小速度                                                                            |
| maxVelocity   | float | 100.0       | 最大速度                                                                            |
| timestep      | float | 0.5         | 时间步长                                                                            |
| stabilization | bool  | True        | 是否启用稳定化                                                                      |
| fit           | bool  | True        | 是否自适应视图                                                                      |

### 层次布局配置

| 参数                 | 类型 | 默认值    | 描述                              |
| -------------------- | ---- | --------- | --------------------------------- |
| levelSeparation      | int  | 150       | 层级间距                          |
| nodeSpacing          | int  | 100       | 同层节点间距                      |
| treeSpacing          | int  | 200       | 树之间的间距                      |
| blockShifting        | bool | True      | 块偏移                            |
| edgeMinimization     | bool | True      | 边长最小化                        |
| parentCentralization | bool | True      | 父节点居中                        |
| direction            | str  | "UD"      | 方向（"UD", "DU", "LR", "RL"）    |
| sortMethod           | str  | "hubsize" | 排序方法（"hubsize", "directed"） |
| shakeTowards         | str  | "roots"   | 震动方向（"roots", "leaves"）     |

## 节点和边的所有属性

### 节点属性

| 属性  | 类型 | 默认值 | 描述                                                      |
| ----- | ---- | ------ | --------------------------------------------------------- |
| id    | str  | 必填   | 节点唯一标识符                                            |
| label | str  | None   | 节点显示标签                                              |
| title | str  | id 值  | 鼠标悬停显示的标题                                        |
| color | str  | None   | 节点颜色(十六进制)                                        |
| shape | str  | "dot"  | 节点形状                                                  |
| size  | int  | 25     | 节点大小                                                  |
| image | str  | None   | 节点图片 URL（当 shape 为"image"或"circularImage"时使用） |
| group | str  | None   | 节点分组                                                  |
| link  | str  | None   | 双击节点打开的链接                                        |

### 边属性

| 属性   | 类型 | 默认值    | 描述                                               |
| ------ | ---- | --------- | -------------------------------------------------- |
| source | str  | 必填      | 源节点 ID                                          |
| target | str  | 必填      | 目标节点 ID                                        |
| label  | str  | None      | 边标签                                             |
| color  | str  | "#F7A7A6" | 边颜色                                             |
| type   | str  | None      | 边类型（"STRAIGHT", "CURVE_SMOOTH", "CURVE_FULL"） |
| arrows | dict | None      | 箭头配置（例如：{"to": True, "from": False}）      |

# Streamlit 使用文档

Streamlit 是一个用于快速创建数据应用程序的 Python 库。以下是完整的 Streamlit 使用文档，包含所有主要功能和用法示例。

## 目录

1. [文本元素](#文本元素)
2. [数据展示](#数据展示)
   - [st.dataframe](#stdataframe)
   - [st.data_editor](#stdata_editor)
   - [st.table](#sttable)
   - [st.metric](#stmetric)
   - [st.json](#stjson)
3. [图表](#图表)
4. [输入组件](#输入组件)
5. [布局与容器](#布局与容器)
6. [媒体元素](#媒体元素)
7. [状态控制](#状态控制)
8. [页面配置](#页面配置)
9. [实用功能](#实用功能)
   - [st.stop](#ststop)
   - [st.form](#stform)
   - [st.dialog](#stdialog)
   - [st.form_submit_button](#stform_submit_button)
   - [st.rerun](#strerun)
   - [st.get_query_params](#stget_query_params)
   - [st.set_query_params](#stset_query_params)
10. [连接功能](#连接功能)
11. [性能优化](#性能优化)
12. [缓存](#缓存)
13. [会话状态](#会话状态)
14. [用户上下文](#用户上下文)
15. [主题](#主题)
16. [配置选项](#配置选项)
17. [开发者工具](#开发者工具)

## 文本元素

### st.title

显示一个大标题。

```python
st.title("这是标题")
```

### st.header

显示一个中等大小的标题。

```python
st.header("这是节标题")
```

### st.subheader

显示一个小标题。

```python
st.subheader("这是子标题")
```

### st.write

最通用的显示方法，可以显示文本、数据、图表等。

```python
st.write("Hello, *World!* :sunglasses:")
st.write(1234)
st.write(pd.DataFrame({'A': [1, 2, 3], 'B': [4, 5, 6]}))
```

### st.markdown

显示 Markdown 格式的文本。

```python
st.markdown("# 这是Markdown标题")
st.markdown("**加粗文本** 和 *斜体文本*")
```

### st.caption

显示小字体文本，适合用作标题或图表的说明。

```python
st.caption("这是一个说明文字")
```

### st.code

显示代码块。

```python
st.code("""
def hello():
    print("Hello, Streamlit!")
""", language='python')
```

### st.text

显示固定宽度格式的文本。

```python
st.text("这是固定宽度的文本")
```

### st.latex

显示 LaTeX 公式。

```python
st.latex(r"\frac{1}{1+e^{-x}}")
```

## 数据展示

### st.dataframe

显示交互式 DataFrame。

```python
df = pd.DataFrame(np.random.randn(50, 20), columns=("col %d" % i for i in range(20)))
st.dataframe(df)  # 可交互的表格
```

#### st.dataframe 的 UI 功能

st.dataframe 底层使用 glide-data-grid 提供了丰富的功能：

- **列排序**：点击列标题，或从列标题菜单中选择"升序排列"或"降序排列"。
- **列宽调整**：拖拽列标题边界，或从列标题菜单中选择"自动调整大小"。
- **隐藏列**：从列标题菜单中选择"隐藏列"。
- **重新排序和固定列**：拖拽列标题以重新排序，或从列标题菜单中选择"固定列"将其固定在左侧。
- **格式化数字、日期和时间**：从列标题菜单的"格式"选项中选择特定格式。
- **DataFrame 大小调整**：拖拽右下角可调整整个 DataFrame 的大小。
- **全屏视图**：点击工具栏中的全屏图标可放大查看。
- **搜索**：点击工具栏中的搜索图标，或使用快捷键（⌘+F 或 Ctrl+F）。
- **下载**：点击工具栏中的下载图标可将数据下载为 CSV 文件。
- **复制到剪贴板**：选择一个或多个单元格，使用快捷键（⌘+C 或 Ctrl+C）复制，然后粘贴到电子表格软件中。

除了 Pandas DataFrame，st.dataframe 还支持其他常见 Python 类型，如列表、字典或 NumPy 数组。它还支持 Snowpark 和 PySpark DataFrame，这对处理大型数据集非常有用。

```python
import streamlit as st
import pandas as pd

df = pd.DataFrame(
    [
        {"command": "st.selectbox", "rating": 4, "is_widget": True},
        {"command": "st.balloons", "rating": 5, "is_widget": False},
        {"command": "st.time_input", "rating": 3, "is_widget": True},
    ]
)

st.dataframe(df, use_container_width=True)
```

### st.data_editor

显示可编辑的 DataFrame。

```python
edited_df = st.data_editor(df)  # 可编辑的表格
```

st.data_editor 与 st.dataframe 类似，但允许用户通过点击单元格来编辑数据。编辑后的数据会返回到 Python 端。

```python
df = pd.DataFrame(
    [
        {"command": "st.selectbox", "rating": 4, "is_widget": True},
        {"command": "st.balloons", "rating": 5, "is_widget": False},
        {"command": "st.time_input", "rating": 3, "is_widget": True},
    ]
)

edited_df = st.data_editor(df)  # 可编辑的 DataFrame

favorite_command = edited_df.loc[edited_df["rating"].idxmax()]["command"]
st.markdown(f"你最喜欢的命令是 **{favorite_command}** 🎈")
```

#### st.data_editor 的功能

st.data_editor 支持以下功能：

##### 添加和删除行

通过设置 `num_rows="dynamic"` 参数，允许用户根据需要添加和删除行：

```python
edited_df = st.data_editor(df, num_rows="dynamic")
```

- 添加行：点击工具栏中的加号图标，或点击表格底部的阴影单元格。
- 删除行：使用左侧的复选框选择一行或多行，然后点击删除图标或按键盘上的删除键。

##### 复制和粘贴支持

数据编辑器支持从 Google Sheets、Excel、Notion 等工具中粘贴表格数据，也支持在 st.data_editor 实例之间复制粘贴数据。

> **注意**：粘贴的每个单元格数据将根据列类型进行评估。例如，将非数字文本数据粘贴到数字列中将被忽略。
>
> **提示**：如果您使用 iframe 嵌入应用，需要允许 iframe 访问剪贴板。例如：
>
> ```html
> <iframe
>   allow="clipboard-write;clipboard-read;"
>   ...
>   src="https://your-app-url"
> ></iframe>
> ```

##### 访问编辑数据

有时，了解哪些单元格被更改比获取整个编辑后的 DataFrame 更方便。Streamlit 通过会话状态（Session State）使这变得简单：

```python
st.data_editor(df, key="my_key", num_rows="dynamic")  # 设置 key
st.write("Session State 中的值：")
st.write(st.session_state["my_key"])  # 显示 Session State 中的值
```

当你设置 `key` 参数时，Streamlit 会将对 DataFrame 的任何更改存储在 Session State 中。这在处理大型 DataFrame 时特别有用，因为你只需要知道哪些单元格发生了变化，而不需要访问整个编辑后的 DataFrame。

Session State 中的数据编辑器状态是一个 JSON 对象，包含三个属性：

- **edited_rows**：包含所有编辑的字典。键是基于零的行索引，值是映射列名到编辑的字典（例如 `{0: {"col1": ..., "col2": ...}}`）。
- **added_rows**：新添加行的列表。每个值都是一个与上面格式相同的字典（例如 `[{"col1": ..., "col2": ...}]`）。
- **deleted_rows**：从表格中删除的行号列表（例如 `[0, 2]`）。

> **警告**：当从 st.experimental_data_editor 迁移到 st.data_editor（1.23.0 版本）时，数据编辑器在 st.session_state 中的表示方式发生了变化。edited_cells 字典现在称为 edited_rows，使用不同的格式（`{0: {"column name": "edited value"}}` 而不是 `{"0:1": "edited value"}`）。

##### 批量编辑

数据编辑器支持批量编辑单元格。类似于 Excel，你可以拖拽手柄跨越多个单元格进行批量编辑，甚至可以使用电子表格软件中常用的键盘快捷键。

##### 编辑常见数据结构

st.data_editor 不仅适用于 Pandas DataFrame，还可以编辑列表、元组、集合、字典、NumPy 数组或 Snowpark 和 PySpark DataFrame。大多数数据类型将以原始格式返回，但某些类型（如 Snowpark 和 PySpark）会转换为 Pandas DataFrame。

例如，你可以让用户向列表添加项目：

```python
edited_list = st.data_editor(["红色", "绿色", "蓝色"], num_rows="dynamic")
st.write("你输入的所有颜色：")
st.write(edited_list)
```

或者 NumPy 数组：

```python
import numpy as np

st.data_editor(np.array([
    ["st.text_area", "widget", 4.92],
    ["st.markdown", "element", 47.22]
]))
```

或者记录列表：

```python
st.data_editor([
    {"name": "st.text_area", "type": "widget"},
    {"name": "st.markdown", "type": "element"},
])
```

甚至是字典等更多类型：

```python
st.data_editor({
    "st.text_area": "widget",
    "st.markdown": "element"
})
```

##### 自动输入验证

数据编辑器包含自动输入验证功能，有助于防止编辑单元格时出错。例如，如果你有一个包含数值数据的列，输入字段将自动限制用户只能输入数值数据。

#### 配置列

你可以通过列配置 API 配置 st.dataframe 和 st.data_editor 中列的显示和编辑行为。通过 API，你可以在 DataFrame 和数据编辑器列中添加图像、图表和可点击的 URL。此外，你还可以使单独的列可编辑，将列设置为分类列并指定它们可以采用的选项，隐藏 DataFrame 的索引等。

列配置包括以下列类型：文本、数字、复选框、选择框、日期、时间、日期时间、列表、链接、图像、折线图、条形图和进度条。还有一个通用的 Column 选项。

##### 格式化值

列配置中的 format 参数可用于文本、日期、时间和日期时间列。图表类列也可以格式化。折线图和条形图列有 y_min 和 y_max 参数来设置垂直边界。对于进度条列，你可以使用 min_value 和 max_value 声明水平边界。

##### 验证输入

指定列配置时，你不仅可以声明列的数据类型，还可以声明值限制。所有列配置元素都允许你使用关键字参数 `required=True` 将列设为必填。

对于文本和链接列，你可以使用 max_chars 指定最大字符数，或使用 validate 通过正则表达式验证条目。数字列（包括数字、日期、时间和日期时间）有 min_value 和 max_value 参数。选择框列具有可配置的选项列表。

数字列的默认数据类型是 float。如果向 min_value、max_value、step 或 default 传递 int 类型的值，将把该列的类型设置为 int。

##### 配置空 DataFrame

你可以使用 st.data_editor 从用户那里收集表格输入。从空 DataFrame 开始时，默认列类型为文本。使用列配置指定要从用户收集的数据类型：

```python
import streamlit as st
import pandas as pd

df = pd.DataFrame(columns=['name','age','color'])
colors = ['红色', '橙色', '黄色', '绿色', '蓝色', '靛蓝色', '紫色']
config = {
    'name' : st.column_config.TextColumn('全名（必填）', width='large', required=True),
    'age' : st.column_config.NumberColumn('年龄（年）', min_value=0, max_value=122),
    'color' : st.column_config.SelectboxColumn('最喜欢的颜色', options=colors)
}

result = st.data_editor(df, column_config=config, num_rows='dynamic')

if st.button('获取结果'):
    st.write(result)
```

##### 其他格式化选项

除了列配置外，st.dataframe 和 st.data_editor 还有一些其他参数来自定义 DataFrame 的显示：

- **hide_index**：设置为 True 可隐藏 DataFrame 的索引。
- **column_order**：传递列标签列表来指定显示顺序。
- **disabled**：传递列标签列表以禁止编辑它们。这样可以避免单独禁用它们。

#### 处理大型数据集

st.dataframe 和 st.data_editor 借助 glide-data-grid 库和 HTML canvas 的高性能实现，理论上可以处理包含数百万行的表格。但是，应用实际可以处理的最大数据量将取决于几个因素：

- **WebSocket 消息的最大大小**：Streamlit 的 WebSocket 消息可通过 server.maxMessageSize 配置选项配置。
- **服务器内存**：应用可以处理的数据量也取决于服务器上可用的内存量。
- **用户浏览器内存**：由于所有数据都需要传输到用户的浏览器进行渲染，用户设备上可用的内存量也会影响应用的性能。
- **网络连接速度**：慢速网络连接也会显著降低处理大型数据集的应用速度。

当处理超过 150,000 行的大型数据集时，Streamlit 会应用额外的优化并禁用列排序。

#### 限制

- Streamlit 在内部将所有列名转换为字符串，因此 st.data_editor 将返回一个所有列名都是字符串的 DataFrame。
- DataFrame 工具栏目前不可配置。
- 虽然 Streamlit 的数据编辑功能提供了很多功能，但编辑仅针对有限的列类型启用（TextColumn、NumberColumn、LinkColumn、CheckboxColumn、SelectboxColumn、DateColumn、TimeColumn 和 DatetimeColumn）。
- 几乎所有可编辑的数据类型都支持索引编辑。但是，pandas.CategoricalIndex 和 pandas.MultiIndex 不支持编辑。
- 当 num_rows="dynamic" 时，st.data_editor 不支持排序。
- 为了优化大型数据集（超过 150,000 行）的性能，排序功能会被停用。

### st.table

显示静态表格。

```python
st.table(df.iloc[0:10])  # 静态表格
```

### st.metric

显示指标卡。

```python
st.metric(label="温度", value="70 °F", delta="1.2 °F")
```

### st.json

显示 JSON 数据。

```python
st.json({
    'foo': 'bar',
    'baz': 'boz',
    'stuff': [
        'stuff 1',
        'stuff 2',
        'stuff 3',
        'stuff 5',
    ],
})
```

## 图表

### st.line_chart

显示折线图。

```python
chart_data = pd.DataFrame(np.random.randn(20, 3), columns=['a', 'b', 'c'])
st.line_chart(chart_data)
```

### st.area_chart

显示面积图。

```python
st.area_chart(chart_data)
```

### st.bar_chart

显示柱状图。

```python
st.bar_chart(chart_data)
```

### st.pyplot

显示 matplotlib 图表。

```python
import matplotlib.pyplot as plt

arr = np.random.normal(1, 1, size=100)
fig, ax = plt.subplots()
ax.hist(arr, bins=20)

st.pyplot(fig)
```

### st.altair_chart

显示 Altair 图表。

```python
import altair as alt

c = alt.Chart(chart_data).mark_circle().encode(
    x='a', y='b', size='c', color='c', tooltip=['a', 'b', 'c']
)
st.altair_chart(c, use_container_width=True)
```

### st.vega_lite_chart

显示 Vega-Lite 图表。

```python
st.vega_lite_chart(chart_data, {
    'mark': {'type': 'circle', 'tooltip': True},
    'encoding': {
        'x': {'field': 'a', 'type': 'quantitative'},
        'y': {'field': 'b', 'type': 'quantitative'},
        'size': {'field': 'c', 'type': 'quantitative'},
        'color': {'field': 'c', 'type': 'quantitative'},
    },
})
```

### st.plotly_chart

显示 Plotly 图表。

```python
import plotly.express as px

fig = px.scatter(x=[0, 1, 2, 3, 4], y=[0, 1, 4, 9, 16])
st.plotly_chart(fig)
```

### st.bokeh_chart

显示 Bokeh 图表。

```python
from bokeh.plotting import figure

p = figure(
    title='简单示例',
    x_axis_label='X',
    y_axis_label='Y'
)
p.line([1, 2, 3, 4, 5], [6, 7, 2, 4, 5], line_width=2)

st.bokeh_chart(p)
```

### st.pydeck_chart

显示 PyDeck 图表。

```python
import pydeck as pdk

chart_data = pd.DataFrame(
   np.random.randn(1000, 2) / [50, 50] + [37.76, -122.4],
   columns=['lat', 'lon'])

st.pydeck_chart(pdk.Deck(
    map_style=None,
    initial_view_state=pdk.ViewState(
        latitude=37.76,
        longitude=-122.4,
        zoom=11,
        pitch=50,
    ),
    layers=[
        pdk.Layer(
            'HexagonLayer',
            data=chart_data,
            get_position='[lon, lat]',
            radius=200,
            elevation_scale=4,
            elevation_range=[0, 1000],
            pickable=True,
            extruded=True,
        ),
        pdk.Layer(
            'ScatterplotLayer',
            data=chart_data,
            get_position='[lon, lat]',
            get_color='[200, 30, 0, 160]',
            get_radius=200,
        ),
    ],
))
```

### st.graphviz_chart

显示 Graphviz 图表。

```python
import graphviz as gv

graph = gv.Digraph()
graph.edge('run', 'intr')
graph.edge('intr', 'runbl')
graph.edge('runbl', 'run')
graph.edge('run', 'kernel')
graph.edge('kernel', 'zombie')
graph.edge('kernel', 'sleep')
graph.edge('kernel', 'runmem')
graph.edge('sleep', 'swap')
graph.edge('swap', 'runswap')
graph.edge('runswap', 'new')
graph.edge('runswap', 'runmem')
graph.edge('new', 'runmem')
graph.edge('sleep', 'runmem')

st.graphviz_chart(graph)
```

## 输入组件

### st.button

显示一个按钮。

```python
if st.button('点击我'):
    st.write('按钮被点击了!')
else:
    st.write('按钮未被点击')
```

### st.download_button

显示下载按钮。

```python
data = pd.DataFrame({'a': [1, 2, 3], 'b': [4, 5, 6]})
csv = data.to_csv(index=False).encode('utf-8')

st.download_button(
    label="下载CSV",
    data=csv,
    file_name='data.csv',
    mime='text/csv',
)
```

### st.link_button

显示链接按钮。

```python
st.link_button("访问Streamlit官网", "https://streamlit.io")
```

### st.checkbox

显示复选框。

```python
agree = st.checkbox('我同意')
if agree:
    st.write('太好了!')
```

### st.toggle

显示切换开关。

```python
on = st.toggle('激活功能')
if on:
    st.write('功能已激活!')
```

### st.radio

显示单选按钮。

```python
genre = st.radio(
    "你最喜欢的电影类型",
    ('喜剧', '动作', '爱情'))
if genre == '喜剧':
    st.write('你选择了喜剧.')
else:
    st.write("你的选择不是喜剧.")
```

### st.selectbox

显示下拉选择框。

```python
option = st.selectbox(
    '你希望如何联系?',
    ('Email', '手机', '短信'))
st.write('你选择了:', option)
```

### st.multiselect

显示多选框。

```python
options = st.multiselect(
    '你喜欢的颜色',
    ['绿色', '黄色', '红色', '蓝色'],
    ['黄色', '红色'])
st.write('你选择了:', options)
```

### st.slider

显示滑块。

```python
age = st.slider('你的年龄', 0, 130, 25)
st.write("我的年龄是", age)
```

### st.select_slider

显示选择滑块。

```python
color = st.select_slider(
    '选择颜色',
    options=['红', '橙', '黄', '绿', '蓝', '靛', '紫'])
st.write('你选择的颜色是', color)
```

### st.text_input

显示文本输入框。

```python
title = st.text_input('电影标题', '阿凡达')
st.write('当前电影标题是', title)
```

### st.number_input

显示数字输入框。

```python
number = st.number_input('输入一个数字')
st.write('当前数字是 ', number)
```

### st.text_area

显示多行文本输入框。

```python
txt = st.text_area('输入多行文本')
st.write('你输入了: ', txt)
```

### st.date_input

显示日期选择器。

```python
d = st.date_input("选择日期")
st.write('你选择的日期是:', d)
```

### st.time_input

显示时间选择器。

```python
t = st.time_input('设置闹钟')
st.write('闹钟设置为:', t)
```

### st.file_uploader

显示文件上传组件。

```python
uploaded_file = st.file_uploader("选择一个文件")
if uploaded_file is not None:
    bytes_data = uploaded_file.getvalue()
    st.write(bytes_data)
```

### st.camera_input

显示相机输入。

```python
picture = st.camera_input("拍照")
if picture:
    st.image(picture)
```

### st.color_picker

显示颜色选择器。

```python
color = st.color_picker('选择颜色', '#00f900')
st.write('当前颜色是', color)
```

## 布局与容器

### st.columns

创建列布局。

```python
col1, col2, col3 = st.columns(3)
with col1:
    st.header("第一列")
    st.write("这是第一列的内容")
with col2:
    st.header("第二列")
    st.write("这是第二列的内容")
with col3:
    st.header("第三列")
    st.write("这是第三列的内容")
```

### st.tabs

创建标签页。

```python
tab1, tab2, tab3 = st.tabs(["猫", "狗", "猫头鹰"])
with tab1:
    st.header("猫")
    st.image("https://static.streamlit.io/examples/cat.jpg")
with tab2:
    st.header("狗")
    st.image("https://static.streamlit.io/examples/dog.jpg")
with tab3:
    st.header("猫头鹰")
    st.image("https://static.streamlit.io/examples/owl.jpg")
```

### st.expander

创建可折叠的内容区域。

```python
with st.expander("点击查看详情"):
    st.write("""
        这是被折叠的内容。点击标题可以展开或折叠。
        可以在这里放置大量内容而不会占用太多空间。
    """)
```

### st.container

创建一个容器。

```python
with st.container():
    st.write("这是容器内的内容")
    st.bar_chart(np.random.randn(50, 3))
```

### st.empty

创建一个空容器，可以动态更新内容。

```python
placeholder = st.empty()
# 替换内容
placeholder.text("Hello")
# 再次替换
placeholder.line_chart({"data": [1, 5, 2, 6]})
```

## 媒体元素

### st.image

显示图片。

```python
st.image("https://static.streamlit.io/examples/cat.jpg", caption="猫")
```

### st.audio

显示音频播放器。

```python
st.audio("https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3")
```

### st.video

显示视频播放器。

```python
st.video("https://www.youtube.com/watch?v=9bZkp7q19f0")
```

## 状态控制

### st.progress

显示进度条。

```python
import time

progress_text = "操作进行中，请稍候..."
my_bar = st.progress(0, text=progress_text)

for percent_complete in range(100):
    time.sleep(0.1)
    my_bar.progress(percent_complete + 1, text=progress_text)
time.sleep(1)
my_bar.empty()
```

### st.spinner

显示加载指示器。

```python
with st.spinner('处理中...'):
    time.sleep(5)
st.success('完成!')
```

### st.balloons

显示气球动画。

```python
st.balloons()
```

### st.snow

显示下雪动画。

```python
st.snow()
```

### st.toast

显示临时通知。

```python
st.toast('你的编辑已保存!', icon='😍')
```

### st.error

显示错误消息。

```python
st.error('这是一个错误')
```

### st.warning

显示警告消息。

```python
st.warning('这是一个警告')
```

### st.info

显示信息消息。

```python
st.info('这是一个信息')
```

### st.success

显示成功消息。

```python
st.success('这是一个成功消息')
```

### st.exception

显示异常信息。

```python
e = RuntimeError('这是一个异常')
st.exception(e)
```

## 页面配置

### st.set_page_config

设置页面配置（必须在其他 Streamlit 命令之前调用）。

```python
st.set_page_config(
    page_title="我的应用",
    page_icon=":rocket:",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://www.extremelycoolapp.com/help',
        'Report a bug': "https://www.extremelycoolapp.com/bug",
        'About': "# 这是一个非常棒的应用!"
    }
)
```

### st.sidebar

在侧边栏添加元素。

```python
# 在侧边栏添加选择框
add_selectbox = st.sidebar.selectbox(
    "你希望如何联系?",
    ("Email", "手机", "短信")
)

# 在侧边栏添加滑块
add_slider = st.sidebar.slider(
    "选择一个数值范围",
    0.0, 100.0, (25.0, 75.0)
)
```

## 实用功能

### st.stop

停止执行脚本。

```python
name = st.text_input('姓名')
if not name:
    st.warning('请输入姓名')
    st.stop()
st.success('谢谢输入')
```

### st.form

创建表单，允许用户批量提交多个输入而不会在每次输入时重新运行脚本。

```python
with st.form("my_form"):
    st.write("表单内部")
    slider_val = st.slider("表单滑块")
    checkbox_val = st.checkbox("表单复选框")

    # 每个表单必须有提交按钮
    submitted = st.form_submit_button("提交")
    if submitted:
        st.write("滑块值", slider_val, "复选框状态", checkbox_val)
```

#### 表单的用户交互

当小部件不在表单中时，每当用户更改其值时，该小部件都会触发脚本重新运行。对于带有键入输入的小部件（`st.number_input`、`st.text_input`、`st.text_area`），当用户点击或从小部件中切换出去时，新值会触发重新运行。用户也可以通过在小部件中按 Enter 键来提交更改。

相反，如果小部件在表单内部，当用户点击或从该小部件中切换出去时，脚本不会重新运行。对于表单内的小部件，只有当表单被提交时脚本才会重新运行，并且表单内的所有小部件将把它们的更新值发送到 Python 后端。

用户可以通过以下方式提交表单：

- 如果光标在接受键入输入的小部件中，可以使用键盘上的 Enter 键
- 在`st.number_input`和`st.text_input`中，用户按 Enter 键提交表单
- 在`st.text_area`中，用户按 Ctrl+Enter/⌘+Enter 提交表单
- 点击`st.form_submit_button`按钮

#### 表单示例

在以下示例中，用户可以设置多个参数来更新地图。当用户更改参数时，脚本不会重新运行，地图也不会更新。当用户通过标有"更新地图"的按钮提交表单时，脚本会重新运行并更新地图。

```python
import streamlit as st
import numpy as np
import pandas as pd

# 生成随机点
def generate_points():
    return pd.DataFrame(
        np.random.randn(10, 2) / [50, 50] + [37.76, -122.4],
        columns=['lat', 'lon']
    )

if 'points' not in st.session_state:
    st.session_state.points = generate_points()

st.title("表单示例 - 地图更新器")

# 表单外部的按钮会立即触发重新运行
if st.button("生成新的点"):
    st.session_state.points = generate_points()

# 表单内的组件只有在提交表单时才会更新
with st.form("map_settings"):
    st.write("### 地图设置")
    zoom = st.slider("缩放级别", 1, 20, 11)
    color = st.color_picker("点的颜色", "#FF4B4B")
    size = st.number_input("点大小", 50, 300, 100)

    # 提交按钮
    submitted = st.form_submit_button("更新地图")

# 显示地图
st.write("### 地图")
st.map(st.session_state.points, zoom=zoom)

# 显示设置信息
st.write(f"缩放级别: {zoom}")
st.write(f"点的颜色: {color}")
st.write(f"点大小: {size}")
```

#### 表单是容器

当调用`st.form`时，会在前端创建一个容器。您可以像使用其他容器元素一样向该容器写入内容。也就是说，您可以使用 Python 的 with 语句（如上例所示），或者将表单容器分配给变量并直接在其上调用方法。此外，您可以在表单容器中的任何位置放置`st.form_submit_button`。

```python
import streamlit as st

animal = st.form('my_animal')

# 这直接写入主体。由于表单容器在上面定义，这将显示在表单中写入的所有内容之后。
sound = st.selectbox('听起来像', ['喵','汪','吱','啾'])

# 这些方法在表单容器上调用，因此它们出现在表单内部。
submit = animal.form_submit_button(f'用{sound}说出来！')
sentence = animal.text_input('你的句子:', '金枪鱼在哪里？')
say_it = sentence.rstrip('.,!?') + f', {sound}!'

if submit:
    animal.subheader(say_it)
else:
    animal.subheader('&nbsp;')
```

#### 处理表单提交

表单的目的是覆盖 Streamlit 的默认行为，即用户做出更改时立即重新运行脚本。对于表单外的小部件，逻辑流程是：

1. 用户在前端更改小部件的值
2. 更新`st.session_state`和 Python 后端（服务器）中的小部件值
3. 脚本重新运行开始
4. 如果小部件有回调，它将作为页面重新运行的前缀执行
5. 当重新运行期间执行更新的小部件的函数时，它会输出新值

对于表单内的小部件，用户所做的任何更改（步骤 1）在表单提交之前不会传递给 Python 后端（步骤 2）。此外，表单内唯一可以有回调函数的小部件是`st.form_submit_button`。

##### 处理表单提交的模式

###### 在表单之后执行处理

如果您需要执行一次性处理作为表单提交的结果，可以在`st.form_submit_button`上设置条件，并在表单之后执行处理。

```python
import streamlit as st

col1, col2 = st.columns([1, 2])
col1.title('总和:')

with st.form('addition'):
    a = st.number_input('a')
    b = st.number_input('b')
    submit = st.form_submit_button('加')

if submit:
    col2.title(f'{a+b:.2f}')
```

###### 使用会话状态的回调

您可以使用回调在脚本重新运行之前执行处理。

```python
import streamlit as st

if 'sum' not in st.session_state:
    st.session_state.sum = ''

def sum_numbers():
    result = st.session_state.a + st.session_state.b
    st.session_state.sum = result

col1, col2 = st.columns(2)
col1.title('总和:')
if isinstance(st.session_state.sum, float):
    col2.title(f'{st.session_state.sum:.2f}')

with st.form('addition'):
    st.number_input('a', key='a')
    st.number_input('b', key='b')
    st.form_submit_button('加', on_click=sum_numbers)
```

注意：当在回调内处理新更新的值时，不要通过`args`或`kwargs`参数直接将这些值传递给回调。您需要为要在回调中使用的任何小部件分配一个键（key）。如果您在回调函数体内从`st.session_state`中查找该小部件的值，您将能够访问新提交的值。

###### 使用 st.rerun

如果您的处理会影响表单上方的内容，另一种选择是使用额外的重新运行。

```python
import streamlit as st

if 'sum' not in st.session_state:
    st.session_state.sum = ''

col1, col2 = st.columns(2)
col1.title('总和:')
if isinstance(st.session_state.sum, float):
    col2.title(f'{st.session_state.sum:.2f}')

with st.form('addition'):
    a = st.number_input('a')
    b = st.number_input('b')
    submit = st.form_submit_button('加')

# st.session_state.sum的值会在脚本重新运行的末尾更新，
# 因此col2中顶部显示的值不会显示新的总和。当表单提交时触发
# 第二次重新运行，以更新上面的值。
st.session_state.sum = a + b
if submit:
    st.rerun()
```

#### 表单的限制

- 每个表单必须包含一个`st.form_submit_button`
- `st.button`和`st.download_button`不能添加到表单中
- `st.form`不能嵌套在另一个`st.form`中
- 在表单中，只有`st.form_submit_button`可以分配回调函数；表单中的其他小部件不能有回调
- 表单内相互依赖的小部件不太可能特别有用。如果在它们都在表单内部时将 widget1 的值传递给 widget2，那么只有在表单提交时 widget2 才会更新

### st.dialog

创建模态对话框。

```python
@st.dialog(title, *, width="small")
def dialog_function(args):
    # 对话框内的内容
    st.write("这是对话框内的内容")
```

使用 `@st.dialog` 装饰的函数会创建一个模态对话框。当调用此函数时，Streamlit 会在应用中插入一个模态对话框。在对话框函数内调用的 Streamlit 元素会渲染在对话框内部。

对话框函数可以接受参数，这些参数可以在调用函数时传递。任何需要在应用程序更广泛范围内访问的对话框值通常应存储在会话状态中。

用户可以通过以下方式关闭对话框：

- 点击对话框外部
- 点击右上角的"X"按钮
- 按键盘上的 ESC 键

关闭对话框不会触发应用重新运行。要以编程方式关闭对话框，可以在对话框函数内部显式调用 `st.rerun()`。

`st.dialog` 继承了 `st.fragment` 的行为。当用户与对话框内创建的输入控件交互时，Streamlit 只会重新运行对话框函数，而不是整个脚本。

在对话框函数中调用 `st.sidebar` 是不支持的。

对话框代码可以与会话状态、导入的模块以及在对话框外部创建的其他 Streamlit 元素交互。注意，这些交互在多次对话框重新运行中是累加的。你需要负责处理这种行为可能产生的任何副作用。

#### 参数

- **title** (str): 在对话框顶部显示的标题。不能为空。
- **width** ("small", "large"): 对话框的宽度。如果为 "small"（默认），对话框宽度为 500 像素。如果为 "large"，对话框宽度约为 750 像素。

#### 示例

以下示例演示了 `@st.dialog` 的基本用法。在这个应用中，点击"A"或"B"会打开一个模态对话框，提示你输入你的投票理由。在对话框中，点击"提交"将你的投票记录到会话状态中并重新运行应用。这将关闭模态对话框，因为在完整脚本重新运行期间不会调用对话框函数。

```python
import streamlit as st

@st.dialog("投票")
def vote(item):
    st.write(f"为什么 {item} 是你的最爱？")
    reason = st.text_input("因为...")
    if st.button("提交"):
        st.session_state.vote = {"item": item, "reason": reason}
        st.rerun()

if "vote" not in st.session_state:
    st.write("为你的最爱投票")
    if st.button("A"):
        vote("A")
    if st.button("B"):
        vote("B")
else:
    f"你投票给了 {st.session_state.vote['item']}，因为 {st.session_state.vote['reason']}"
```

这个例子展示了如何使用 `@st.dialog` 创建一个简单的投票表单，并将投票结果存储在会话状态中。

#### 另一个实践示例：用户信息确认

以下示例使用模态对话框来确认用户信息：

```python
import streamlit as st

@st.dialog("确认用户信息")
def confirm_user_info(user_data):
    st.write("请确认以下信息是否正确：")
    st.write(f"姓名: {user_data['name']}")
    st.write(f"电子邮件: {user_data['email']}")
    st.write(f"年龄: {user_data['age']}")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("确认"):
            st.session_state.confirmed = True
            st.rerun()
    with col2:
        if st.button("修改"):
            st.session_state.editing = True
            st.rerun()

if "user_data" not in st.session_state:
    st.session_state.user_data = {"name": "", "email": "", "age": 0}
    st.session_state.confirmed = False
    st.session_state.editing = False

if not st.session_state.confirmed:
    st.title("用户信息表单")

    with st.form("user_form"):
        st.session_state.user_data["name"] = st.text_input("姓名", st.session_state.user_data["name"])
        st.session_state.user_data["email"] = st.text_input("电子邮件", st.session_state.user_data["email"])
        st.session_state.user_data["age"] = st.number_input("年龄", min_value=0, max_value=120, value=st.session_state.user_data["age"])

        if st.form_submit_button("提交"):
            confirm_user_info(st.session_state.user_data)

else:
    st.title("信息已确认")
    st.success("您的信息已提交成功！")
    st.json(st.session_state.user_data)

    if st.button("重新填写"):
        st.session_state.confirmed = False
        st.session_state.editing = False
        st.session_state.user_data = {"name": "", "email": "", "age": 0}
        st.rerun()
```

#### 警告

在一次脚本运行中只能调用一个对话框函数，这意味着一次只能打开一个对话框。

### st.form_submit_button

在表单中创建提交按钮。

```python
with st.form("my_form"):
    st.write("表单内部")
    slider_val = st.slider("表单滑块")
    checkbox_val = st.checkbox("表单复选框")

    # 使用st.form_submit_button
    if st.form_submit_button("提交"):
        st.write("滑块值", slider_val, "复选框状态", checkbox_val)
```

### st.rerun

重新运行脚本。

```python
if st.button('重新运行'):
    st.rerun()
```

### st.get_query_params

获取 URL 查询参数。

```python
query_params = st.get_query_params()
st.write(query_params)
```

### st.set_query_params

设置 URL 查询参数。

```python
st.set_query_params(
    show_map=True,
    selected=["dog", "cat"]
)
```

## 连接功能

### st.connection

创建数据连接。

```python
conn = st.connection('my_database', type='sql')
df = conn.query('SELECT * FROM my_table')
st.dataframe(df)
```

### st.user

获取用户信息（企业版功能）。

```python
user = st.user
st.write(f'欢迎, {user.email}!')
```

## 性能优化

### st.fragment

创建片段，可以独立重新运行。

```python
@st.fragment
def my_fragment():
    option = st.selectbox('选择一个选项', ['A', 'B', 'C'])
    st.write('你选择了:', option)

my_fragment()
```

### st.experimental_memo

缓存函数结果（基于参数）。

```python
@st.experimental_memo
def expensive_computation(a, b):
    time.sleep(2)  # 模拟耗时计算
    return a * b

result = expensive_computation(2, 21)
st.write("计算结果:", result)
```

### st.experimental_singleton

缓存单例对象。

```python
@st.experimental_singleton
def get_database_connection():
    # 创建并返回数据库连接
    return db.connect('my_database')

conn = get_database_connection()
```

## 缓存

### st.cache_data

缓存数据计算。

```python
@st.cache_data
def load_data(url):
    df = pd.read_csv(url)
    return df

data = load_data("https://example.com/large_dataset.csv")
st.dataframe(data)
```

### st.cache_resource

缓存资源（如数据库连接、模型等）。

```python
@st.cache_resource
def get_model():
    return load_ml_model()

model = get_model()
```

## 会话状态

### st.session_state

访问和修改会话状态。

```python
if 'counter' not in st.session_state:
    st.session_state.counter = 0

st.session_state.counter += 1

st.write(f"计数器: {st.session_state.counter}")

if st.button("增加"):
    st.session_state.counter += 1

if st.button("重置"):
    st.session_state.counter = 0
```

## 用户上下文

### st.context

访问用户会话上下文，提供对当前用户会话的请求头和 cookies 的只读访问接口。

```python
# 显示所有可用的头信息
st.write(st.context.headers)

# 显示所有可用的cookies
st.write(st.context.cookies)

# 显示用户的IP地址
st.write(f"你的IP地址: {st.context.ip_address}")

# 显示应用是否被嵌入
st.write(f"应用是否被嵌入: {st.context.is_embedded}")

# 显示用户的语言环境
st.write(f"你的语言环境: {st.context.locale}")

# 显示用户的时区
st.write(f"你的时区: {st.context.timezone}")

# 显示用户的时区偏移
st.write(f"你的时区偏移: {st.context.timezone_offset}分钟")

# 显示应用的URL
st.write(f"应用URL: {st.context.url}")
```

#### st.context.headers

只读的类字典对象，包含初始请求中发送的头信息。键不区分大小写且可能重复。当键重复时，字典方法只返回每个键的最后一个实例。

```python
# 显示所有可用的头信息
st.context.headers

# 显示特定头信息的值
st.context.headers["host"]

# 显示特定头信息的所有值
st.context.headers.get_all("pragma")
```

#### st.context.cookies

只读的类字典对象，包含初始请求中发送的 cookies。

```python
# 显示所有可用的cookies
st.context.cookies

# 显示特定cookie的值
if "_ga" in st.context.cookies:
    st.context.cookies["_ga"]
```

#### st.context.ip_address

用户连接的只读 IP 地址。不应将其用于安全措施，因为它可以轻松被伪造。当用户通过 localhost 访问应用程序时，IP 地址为 None。

```python
ip = st.context.ip_address
if ip is None:
    st.write("无IP地址。这在本地开发中是正常的。")
elif ":" in ip:
    st.write("你有一个IPv6地址。")
elif "." in ip:
    st.write("你有一个IPv4地址。")
else:
    st.error("这不应该发生。")
```

#### st.context.is_embedded

应用程序是否被嵌入。返回一个布尔值，指示应用程序是否在嵌入上下文中运行。

```python
if st.context.is_embedded:
    st.write("应用程序在嵌入上下文中运行。")
```

#### st.context.locale

用户浏览器的只读语言环境。返回用户 DOM 中 navigator.language 的值。这是表示用户首选语言的字符串（例如"en-US"）。

```python
if st.context.locale == "zh-CN":
    st.write("你好！")
else:
    st.write("Hello!")
```

#### st.context.timezone

用户浏览器的只读时区。

```python
import pytz
from datetime import datetime, timezone

tz = st.context.timezone
tz_obj = pytz.timezone(tz)

now = datetime.now(timezone.utc)

st.write(f"用户时区：{tz}")
st.write(f"UTC时间：{now}")
st.write(f"用户本地时间：{now.astimezone(tz_obj)}")
```

#### st.context.timezone_offset

用户浏览器的只读时区偏移（以分钟为单位）。

```python
from datetime import datetime, timezone, timedelta

tzoff = st.context.timezone_offset
tz_obj = timezone(-timedelta(minutes=tzoff))

now = datetime.now(timezone.utc)

st.write(f"用户时区偏移：{tzoff}分钟")
st.write(f"UTC时间：{now}")
st.write(f"用户本地时间：{now.astimezone(tz_obj)}")
```

#### st.context.url

应用程序在用户浏览器中的只读 URL。返回用户访问应用程序的 URL，包括方案、域名、端口和路径。如果 URL 中存在查询参数或锚点，则会将其删除。

```python
if st.context.url.startswith("http://localhost"):
    st.write("您正在本地运行应用程序。")
```

## 主题

### st.theme

设置主题。

```python
st.theme({
    "primaryColor": "#FF4B4B",
    "backgroundColor": "#FFFFFF",
    "secondaryBackgroundColor": "#F0F2F6",
    "textColor": "#31333F",
    "font": "sans serif"
})
```

## 配置选项

Streamlit 提供了四种不同的方式来设置配置选项。以下列表按优先级从低到高排序，即当同一配置选项通过不同方式多次提供时，命令行标志的优先级高于环境变量。

> **注意**
>
> 如果你在应用运行时更改 .streamlit/config.toml 中的主题设置，这些更改将立即生效。如果你在应用运行时更改 .streamlit/config.toml 中的非主题设置，则需要重启服务器才能使更改在应用中生效。

### 配置方法

1. **全局配置文件**：macOS/Linux 系统位于 ~/.streamlit/config.toml，Windows 系统位于 %userprofile%/.streamlit/config.toml：

   ```toml
   [server]
   port = 80
   ```

2. **项目配置文件**：位于 $CWD/.streamlit/config.toml，其中 $CWD 是你运行 Streamlit 的文件夹。

3. **环境变量**：通过 STREAMLIT\_\* 环境变量设置，例如：

   ```bash
   export STREAMLIT_SERVER_PORT=80
   export STREAMLIT_SERVER_COOKIE_SECRET=dontforgottochangeme
   ```

4. **命令行标志**：运行 streamlit run 时作为标志传递：

   ```bash
   streamlit run your_script.py --server.port 80
   ```

### 可用选项

所有可用的配置选项都在 config.toml 中有文档说明。这些选项可以在 TOML 文件中声明，作为环境变量使用，或作为命令行选项使用。

当使用环境变量覆盖 config.toml 时，将变量（包括其章节标题）转换为大写蛇形命名并添加 STREAMLIT\_ 前缀。例如，STREAMLIT_CLIENT_SHOW_ERROR_DETAILS 等同于 TOML 中的以下内容：

```toml
[client]
showErrorDetails = true
```

当使用命令行选项覆盖 config.toml 和环境变量时，使用与 TOML 文件中相同的大小写，并将章节标题作为点分隔的前缀包含在内。例如，命令行选项 --server.enableStaticServing true 等同于以下内容：

```toml
[server]
enableStaticServing = true
```

### HTTPS 支持

许多应用需要通过 SSL/TLS 协议或 https:// 访问。

对于自托管和生产用例，我们建议在反向代理或负载均衡器中执行 SSL 终止，而不是直接在应用中执行。Streamlit Community Cloud 使用这种方法，每个主要的云和应用托管平台都应该允许你配置它并提供详细的文档。

如果要在 Streamlit 应用中终止 SSL，你必须配置 server.sslCertFile 和 server.sslKeyFile：

```toml
# .streamlit/config.toml

[server]
sslCertFile = '/path/to/certchain.pem'
sslKeyFile = '/path/to/private.key'
```

#### 使用细节

- 配置值应该是证书文件和密钥文件的本地文件路径。这些文件必须在应用启动时可用。
- 必须同时指定 server.sslCertFile 和 server.sslKeyFile。如果只指定其中一个，应用将退出并显示错误。
- 此功能在 Community Cloud 中不起作用，因为 Community Cloud 已经使用 TLS 提供应用服务。

> **警告**
>
> 在生产环境中，我们建议通过负载均衡器或反向代理执行 SSL 终止，而不是使用此选项。Streamlit 中使用此选项尚未经过广泛的安全审核或性能测试。

### 静态文件服务

Streamlit 应用可以托管和提供小型静态媒体文件，以支持普通媒体元素无法处理的媒体嵌入用例。

要启用此功能，请在配置文件的 [server] 下设置 enableStaticServing = true，或使用环境变量 STREAMLIT_SERVER_ENABLE_STATIC_SERVING=true。

存储在运行的应用文件相对路径 ./static/ 文件夹中的媒体将通过路径 app/static/[filename] 提供服务，例如 http://localhost:8501/app/static/cat.png。

```toml
# .streamlit/config.toml

[server]
enableStaticServing = true
```

#### 使用细节

- 以下扩展名的文件将正常提供服务：
  - 常见图像类型：.jpg、.jpeg、.png、.gif
  - 常见字体类型：.otf、.ttf、.woff、.woff2
  - 其他类型：.pdf、.xml、.json
  - 任何其他文件都将使用标头 Content-Type:text/plain 发送，这将导致浏览器以纯文本方式渲染。这是出于安全考虑 - 需要渲染的其他文件类型应托管在应用之外。
- Streamlit 还为从静态目录渲染的所有文件设置 X-Content-Type-Options:nosniff。
- 对于在 Streamlit Community Cloud 上运行的应用：
  - Github 仓库中可用的文件将始终被提供服务。
  - 应用运行时生成的任何文件，如基于用户交互（文件上传等）的文件，不能保证在用户会话之间持久存在。
  - 存储和提供大量文件或大文件的应用可能会达到资源限制并被关闭。

#### 使用示例

```python
# app.py
import streamlit as st

with st.echo():
    st.title("CAT")

    st.markdown("[![Click me](app/static/cat.png)](https://streamlit.io)")
```

### 遥测

如安装过程中所述，Streamlit 会收集使用统计数据。你可以通过阅读我们的隐私声明了解更多信息，但高级摘要是，尽管我们收集遥测数据，但我们无法查看也不会存储 Streamlit 应用中包含的信息。

如果你想选择退出使用统计，请在配置文件中添加以下内容：

```toml
[browser]
gatherUsageStats = false
```

### 查看所有配置选项

如命令行选项中所述，你可以使用以下命令查看所有可用的配置选项：

```bash
streamlit config show
```

这将显示所有可用的配置选项及其当前值和默认值的列表。

## 主题

Streamlit 主题通过常规配置选项定义：可以使用 streamlit run 时的命令行标志设置主题，或在 .streamlit/config.toml 文件的 [theme] 部分定义主题。

以下配置选项显示了在 .streamlit/config.toml 文件的 [theme] 部分中重新创建的默认 Streamlit Light 主题：

```toml
[theme]
primaryColor="#FF4B4B"
backgroundColor="#FFFFFF"
secondaryBackgroundColor="#F0F2F6"
textColor="#31333F"
font="sans serif"
```

下面我们详细介绍每个选项，并说明它们对 Streamlit 应用的影响：

### primaryColor

primaryColor 定义了 Streamlit 应用中最常用的强调色。使用 primaryColor 的 Streamlit 组件示例包括 st.checkbox、st.slider 和 st.text_input（当聚焦时）。

> **提示**
>
> 任何 CSS 颜色都可以作为 primaryColor 和其他颜色选项的值。这意味着主题颜色可以用十六进制指定，也可以用浏览器支持的颜色名称指定，如"green"、"yellow"和"chartreuse"。它们甚至可以用 RGB 和 HSL 格式定义！

### backgroundColor

定义应用主要内容区域中使用的背景颜色。

### secondaryBackgroundColor

当需要第二个背景颜色以增加对比度时使用此颜色。最明显的是，它是侧边栏的背景颜色。它也用作大多数交互式组件的背景颜色。

### textColor

此选项控制 Streamlit 应用中大部分文本的颜色。

### font

选择 Streamlit 应用中使用的字体。有效值为"sans serif"、"serif"和"monospace"。如果未设置或无效，此选项默认为"sans serif"。

请注意，无论此处选择的字体如何，代码块始终使用等宽字体渲染。

### base

定义对预设 Streamlit 主题进行小更改的自定义主题的一种简单方法是使用 base 选项。使用 base，可以通过编写以下内容将 Streamlit Light 主题重新创建为自定义主题：

```toml
[theme]
base="light"
```

base 选项允许你指定自定义主题继承的预设 Streamlit 主题。在你的主题设置中未定义的任何主题配置选项的值都设置为基本主题的值。base 的有效值为"light"和"dark"。

例如，以下主题配置定义了一个几乎与 Streamlit Dark 主题相同的自定义主题，但有一个新的 primaryColor：

```toml
[theme]
base="dark"
primaryColor="purple"
```

如果省略 base 本身，它默认为"light"，因此你可以用以下配置定义更改 Streamlit Light 主题字体为 serif 的自定义主题：

```toml
[theme]
font="serif"
```

### st.theme

设置主题。

```python
st.theme({
    "primaryColor": "#FF4B4B",
    "backgroundColor": "#FFFFFF",
    "secondaryBackgroundColor": "#F0F2F6",
    "textColor": "#31333F",
    "font": "sans serif"
})
```

## Streamlit Agraph

Streamlit Agraph 是一个用于在 Streamlit 应用中创建和显示图表的组件。它提供了一种简单的方式来创建和显示图表，并支持自定义样式和内容。

### 安装

```bash
pip install streamlit-agraph
```

### 使用

#### Basic Usage

```python
import streamlit
from streamlit_agraph import agraph, Node, Edge, Config

nodes = []
edges = []
nodes.append( Node(id="Spiderman",
                   label="Peter Parker",
                   size=25,
                   shape="circularImage",
                   image="http://marvel-force-chart.surge.sh/marvel_force_chart_img/top_spiderman.png")
            ) # includes **kwargs
nodes.append( Node(id="Captain_Marvel",
                   size=25,
                   shape="circularImage",
                   image="http://marvel-force-chart.surge.sh/marvel_force_chart_img/top_captainmarvel.png")
            )
edges.append( Edge(source="Captain_Marvel",
                   label="friend_of",
                   target="Spiderman",
                   # **kwargs
                   )
            )

config = Config(width=750,
                height=950,
                directed=True,
                physics=True,
                hierarchical=False,
                # **kwargs
                )

return_value = agraph(nodes=nodes,
                      edges=edges,
                      config=config)
```

#### Config Builder

```python
from streamlit_agraph.config import Config, ConfigBuilder

# 1. Build the config (with sidebar to play with options) .
config_builder = ConfigBuilder(nodes)
config = config_builder.build()

# 2. If your done, save the config to a file.
config.save("config.json")

# 3. Simple reload from json file (you can bump the builder at this point.)
config = Config(from_json="config.json")
```

Formating the graph with hierachies is also possible via Hierarchical Option (see config):
Group as you can see on the node colors too. Just pass the group attribute to the Node object.

#### TripleStore

You may also want to use the TripleStore (untested & incomplete - yet):
HINT: Make sure to add only unique nodes and edges.

```python
# Currently not workin since update to agraph 2.0 - work in progress
from rdflib import Graph
from streamlit_agraph import TripleStore, agraph

graph = Graph()
graph.parse("http://www.w3.org/People/Berners-Lee/card")
store = TripleStore()

for subj, pred, obj in graph:
store.add_triple(subj, pred, obj, "")

agraph(list(store.getNodes()), list(store.getEdges()), config)
```

Also graph algos can dirctly supported via the networkx API (untested & incomplete - yet):

```python
from streamlit_agraph import GraphAlgos

algos = GraphAlgos(store)
algos.shortest_path("Spiderman", "Captain_Marvel")
algos.density()
```

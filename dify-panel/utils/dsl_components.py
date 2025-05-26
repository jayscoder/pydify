import streamlit as st
from streamlit_agraph import agraph, Node, Edge, Config
import yaml
import pandas as pd

def dsl_graph(dsl_content):
    """
    使用streamlit_agraph可视化DSL图结构
    
    参数:
        dsl_content: 包含workflow图结构的DSL内容
    """
    try:
        if isinstance(dsl_content, str):
            dsl_content = yaml.safe_load(dsl_content)
        
        if not dsl_content or 'workflow' not in dsl_content or 'graph' not in dsl_content['workflow']:
            st.error("无效的DSL内容或缺少图结构")
            return
        # 提取图数据
        graph_data = dsl_content['workflow']['graph']
        dsl_nodes = graph_data.get('nodes', [])
        dsl_edges = graph_data.get('edges', [])
        
        # 生成节点颜色映射
        node_types = {
            'start': '#4CAF50',      # 绿色
            'end': '#F44336',        # 红色
            'llm': '#2196F3',        # 蓝色
            'code': '#FF9800',       # 橙色
            'template-transform': '#9C27B0',  # 紫色
            'if-else': '#FFEB3B',    # 黄色
            'tool': '#795548',       # 棕色
            'custom': '#607D8B'      # 蓝灰色
        }
        
        # 创建nodes列表
        nodes = []
        nodes_data = []  # 为DataFrame准备数据
        
        for node in dsl_nodes:
            node_id = node['id']
            node_type = node['data'].get('type', 'custom')
            node_title = node['data'].get('title', node_id)
            
            # 收集节点数据
            node_info = {
                'ID': node_id,
                '类型': node_type,
                '标题': node_title,
                '位置X': node.get('position', {}).get('x', 0),
                '位置Y': node.get('position', {}).get('y', 0)
            }
            
            # 添加其他节点特定属性
            if 'variables' in node['data']:
                node_info['变量数'] = len(node['data']['variables'])
            
            # 添加到节点数据列表
            nodes_data.append(node_info)
            
            # 设置节点颜色和形状
            color = node_types.get(node_type, '#607D8B')
            shape = 'dot'
            
            if node_type == 'if-else':
                shape = 'diamond'
            elif node_type == 'start':
                shape = 'hexagon'
            elif node_type == 'end':
                shape = 'hexagon'
            
            # 创建节点
            nodes.append(
                Node(
                    id=node_id,
                    label=node_title,
                    color=color,
                    shape=shape,
                    size=25
                )
            )
        
        # 创建edges列表
        edges = []
        edges_data = []  # 为DataFrame准备数据
        
        for edge in dsl_edges:
            # 收集边数据
            source_id = edge['source']
            target_id = edge['target']
            source_type = edge['data'].get('sourceType', '')
            target_type = edge['data'].get('targetType', '')
            condition = edge['data'].get('condition', '')
            
            edge_info = {
                '源节点': source_id,
                '目标节点': target_id,
                '源类型': source_type,
                '目标类型': target_type,
                '条件': condition
            }
            
            # 添加到边数据列表
            edges_data.append(edge_info)
            
            # 添加边的标签（如果if-else分支使用条件作为标签）
            label = ""
            if condition:
                label = f"条件: {condition}"
            elif 'false' in source_id or 'true' in source_id:
                label = f"条件: {source_id}"
            
            # 设置边的类型（直线或曲线）
            curve_type = "CURVE_SMOOTH"
            
            edges.append(
                Edge(
                    source=source_id,
                    target=target_id,
                    label=label,
                    type=curve_type
                )
            )
        
        # 创建DataFrame
        nodes_df = pd.DataFrame(nodes_data) if nodes_data else pd.DataFrame(columns=['ID', '类型', '标题', '位置X', '位置Y'])
        edges_df = pd.DataFrame(edges_data) if edges_data else pd.DataFrame(columns=['源节点', '目标节点', '源类型', '目标类型', '条件'])
        
        # 配置图
        config = Config(
            width=600,
            height=600,
            directed=True,
            physics=True,
            hierarchical=False,
            nodeHighlightBehavior=True,
            highlightColor="#F7A7A6",
            collapsible=False,
            node={'labelProperty': 'label'},
            link={'labelProperty': 'label', 'renderLabel': True}
        )
        
        # 创建选项卡
        tab1, tab2, tab3 = st.tabs(["图表可视化", "节点列表", "连接列表"])
        
        with tab1:
            # 渲染图
            st.header("DSL 工作流图")
            
            # 添加图例
            st.subheader("图例")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.markdown(f"<div style='background-color: {node_types['start']}; padding: 10px; border-radius: 5px; margin: 2px;'>开始节点</div>", unsafe_allow_html=True)
                st.markdown(f"<div style='background-color: {node_types['end']}; padding: 10px; border-radius: 5px; margin: 2px;'>结束节点</div>", unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"<div style='background-color: {node_types['llm']}; padding: 10px; border-radius: 5px; margin: 2px;'>LLM节点</div>", unsafe_allow_html=True)
                st.markdown(f"<div style='background-color: {node_types['code']}; padding: 10px; border-radius: 5px; margin: 2px;'>代码节点</div>", unsafe_allow_html=True)
            
            with col3:
                st.markdown(f"<div style='background-color: {node_types['template-transform']}; padding: 10px; border-radius: 5px; margin: 2px;'>模板转换节点</div>", unsafe_allow_html=True)
                st.markdown(f"<div style='background-color: {node_types['if-else']}; padding: 10px; border-radius: 5px; margin: 2px;'>条件分支节点</div>", unsafe_allow_html=True)
            
            with col4:
                st.markdown(f"<div style='background-color: {node_types['tool']}; padding: 10px; border-radius: 5px; margin: 2px;'>工具节点</div>", unsafe_allow_html=True)
                st.markdown(f"<div style='background-color: {node_types['custom']}; padding: 10px; border-radius: 5px; margin: 2px;'>自定义节点</div>", unsafe_allow_html=True)
            
            # 统计信息
            st.subheader("工作流统计信息")
            col1, col2, col3 = st.columns(3)
            col1.metric("节点总数", len(nodes))
            col2.metric("连接总数", len(edges))
            
            # 节点类型统计
            node_type_counts = {}
            for node in dsl_nodes:
                node_type = node['data'].get('type', 'custom')
                if node_type in node_type_counts:
                    node_type_counts[node_type] += 1
                else:
                    node_type_counts[node_type] = 1
            
            col3.metric("节点类型数", len(node_type_counts))
            
            st.subheader("节点类型分布")
            for node_type, count in node_type_counts.items():
                st.text(f"{node_type}: {count}")
            
            # 渲染图
            if nodes and edges:
                return_value = agraph(nodes=nodes, edges=edges, config=config)
                
                # 显示用户交互信息
                if return_value:
                    st.write(f"选中节点: {return_value}")
            else:
                st.warning("没有足够的节点或连接来渲染图表")
        
        with tab2:
            # 显示节点表格
            st.header("节点列表")
            
            # 添加搜索过滤功能
            search_node = st.text_input("搜索节点", "", key="search_node")
            if not nodes_df.empty:
                if search_node:
                    filtered_nodes_df = nodes_df[nodes_df.apply(lambda row: search_node.lower() in str(row).lower(), axis=1)]
                    st.dataframe(filtered_nodes_df, use_container_width=True)
                else:
                    st.dataframe(nodes_df, use_container_width=True)
                
                # 节点详情查看
                node_ids = nodes_df['ID'].tolist()
                if node_ids:  # 只有当列表非空时才显示选择框
                    selected_node = st.selectbox("选择节点查看详情", node_ids, key="select_node")
                    if selected_node:
                        st.subheader(f"节点 '{selected_node}' 详情")
                        node_detail = next((node for node in dsl_nodes if node['id'] == selected_node), None)
                        if node_detail:
                            st.json(node_detail)
                else:
                    st.info("没有可用节点")
            else:
                st.info("没有节点数据可显示")
        
        with tab3:
            # 显示边表格
            st.header("连接列表")
            
            # 添加搜索过滤功能
            search_edge = st.text_input("搜索连接", "", key="search_edge")
            
            if not edges_df.empty:
                if search_edge:
                    filtered_edges_df = edges_df[edges_df.apply(lambda row: search_edge.lower() in str(row).lower(), axis=1)]
                    st.dataframe(filtered_edges_df, use_container_width=True)
                else:
                    st.dataframe(edges_df, use_container_width=True)
                
                # 边详情查看
                source_nodes = edges_df['源节点'].tolist()
                if source_nodes:  # 只有当列表非空时才显示选择框
                    selected_edge_source = st.selectbox("源节点", source_nodes, key="select_source")
                    if selected_edge_source:
                        filtered_targets = edges_df[edges_df['源节点'] == selected_edge_source]['目标节点'].tolist()
                        if filtered_targets:  # 确保目标节点列表非空
                            selected_edge_target = st.selectbox("目标节点", filtered_targets, key="select_target")
                            if selected_edge_target:
                                st.subheader(f"连接 '{selected_edge_source}' -> '{selected_edge_target}' 详情")
                                edge_detail = next((edge for edge in dsl_edges 
                                                if edge['source'] == selected_edge_source 
                                                and edge['target'] == selected_edge_target), None)
                                if edge_detail:
                                    st.json(edge_detail)
                                else:
                                    st.info("找不到连接详情")
                        else:
                            st.info("该源节点没有连接到任何目标节点")
                else:
                    st.info("没有连接源节点可选择")
            else:
                st.info("没有连接数据可显示")
        
        return nodes_df, edges_df
        
    except Exception as e:
        st.error(f"可视化DSL图失败: {str(e)}")
        import traceback
        st.error(traceback.format_exc())  # 显示完整错误堆栈
        return None, None


import streamlit as st
from utils.ui_components import site_sidebar
from utils.dify_client import DifyClient
from pydify.site import DifySite
import yaml
import pandas as pd
import json
import time
from typing import Callable
# 设置页面配置
st.set_page_config(
    page_title="测试页面 - Dify管理面板",
    page_icon="🔑",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("测试页面")

MAIN_APP_ID = st.text_input('主应用ID', value='')

site_sidebar()

client: DifySite = DifyClient.get_connection()

def export_app_json(self: DifySite, app_id: str, on_progress: Callable[[str, int], None] = None):
    """
    导出应用的JSON数据

    Args:
        app_id (str): 应用ID
        on_progress (Callable[[str, int], None], optional): 进度回调函数. Defaults to None.

    Returns:
        dict: 导出的JSON数据
    """
    dsl_dict = {}
    tool_dict = {}
    
    def do_fetch(app_id: str, depth: int = 0):
        if app_id in dsl_dict or depth > 50:
            # 防止无限递归
            return

        dsl = self.fetch_app_dsl(app_id)
        dsl = yaml.safe_load(dsl)
        dsl_dict[app_id] = dsl
        for node in dsl['workflow']['graph']['nodes']:
            if node['data']['type'] == 'tool':
                tool_id = node['data']['provider_id']
                tool = self.fetch_workflow_tool(workflow_tool_id=tool_id)
                tool_dict[tool_id] = tool
                tool_workflow_app_id = tool['workflow_app_id']
                if on_progress:
                    on_progress(tool_workflow_app_id, len(tool_dict) + len(dsl_dict))
                time.sleep(0.05)
                do_fetch(tool_workflow_app_id, depth + 1)
    
    do_fetch(app_id)
    
    return {
        'version': '1.0.0',
        'id': app_id,
        'name': dsl_dict[app_id]['app']['name'],
        'dsl': dsl_dict,
        'tool': tool_dict
    }


def import_app_json(self: DifySite, json_data: dict, prefix: str, suffix: str, tag_ids: list[str]):
    """
    导入JSON数据到Dify

    Args:
        json_data (dict): 导入的JSON数据
        prefix (str): 前缀
        suffix (str): 后缀
        tag_ids (list[str]): 标签ID列表
        override (bool, optional): 是否覆盖已存在的应用. Defaults to False.
    
    Raises:
        Exception: 导入的JSON数据中缺少dsl
        Exception: 导入的JSON数据中缺少tool
        Exception: 工具名称已存在
        Exception: 应用名称已存在
    """
    # 获取client中所有的app
    if 'dsl' not in json_data:
        raise Exception('JSON数据中缺少dsl')
    if 'tool' not in json_data:
        raise Exception('JSON数据中缺少tool')
    
    exist_apps = self.fetch_all_apps()
    exist_apps_map = {app['name']: app['id'] for app in exist_apps}
    exist_tool_providers = self.fetch_tool_providers()
    exist_tool_providers_map = {provider['name']: provider for provider in exist_tool_providers}
    
    # 修改所有tool的名称
    create_tool_payloads = {}
    for tool in json_data['tool'].values():
        tool['name'] = prefix + tool['name'] + suffix
        tool['label'] = prefix + tool['label'] + suffix
        if tool['name'] in exist_tool_providers_map:
            raise Exception(f'工具 {tool["name"]} 已存在')
        create_tool_payloads[tool['workflow_app_id']] = tool

    # 修改所有app的名称
    create_app_payloads = {}
    
    for app_id, dsl in json_data['dsl'].items():
        new_name = prefix + dsl['app']['name'] + suffix
        if new_name in exist_apps_map:
            raise Exception(f'应用 {new_name} 已存在')
        dsl['app']['name'] = new_name
        create_app_payloads[new_name] = {
            'name': new_name,
            'description': dsl['app']['description'],
            'mode': dsl['app']['mode'],
            'tag_ids': tag_ids,
            'dsl': dsl,
            'tool': create_tool_payloads.get(app_id, None)
        }
    
    old_tool_mapping = {} # 老的tool_id -> 新的tool
    
    for payload in create_app_payloads.values():
        payload['id'] = self.create_app(
            name=payload['name'],
            description=payload['description'],
            mode=payload['mode'],
            tag_ids=payload['tag_ids'],
            dsl=payload['dsl'],
        )['id']
        
        if payload['tool']:
            self.publish_workflow_app(payload['id'])
            tool = self.create_workflow_tool(
                name=payload['tool']['name'],
                label=payload['tool']['label'],
                workflow_app_id=payload['id'],
                description=payload['tool']['description'],
                parameters=payload['tool'].get('parameters', None),
                labels=payload['tool']['tool'].get('labels', None),
                privacy_policy=payload['tool'].get('privacy_policy', None),
                icon=payload['tool'].get('icon', None),
            )
            old_tool_mapping[payload['tool']['workflow_tool_id']] = tool
            payload['tool'] = tool
    
    # 更新所有的dsl中引用的provider_id为新的tool_id
    for payload in create_app_payloads.values():
        dsl = payload['dsl']
        for node in dsl['workflow']['graph']['nodes']:
            if node['data']['type'] == 'tool':
                new_tool = old_tool_mapping[node['data']['provider_id']]
                node['data']['provider_id'] = new_tool['workflow_tool_id']
                node['data']['provider_name'] = new_tool['name']
                node['data']['tool_label'] = new_tool['label']
                node['data']['tool_name'] = new_tool['name']
        
        # 更新dsl
        self.import_app_dsl(dsl=dsl, app_id=payload['id'])
        # 发布
        self.publish_workflow_app(payload['id'])
        # 重新更新工具
        if payload['tool']:
            self.update_workflow_tool(
                name=payload['tool']['name'],
                label=payload['tool']['label'],
                workflow_app_id=payload['id'],
                upsert=True,
            )
        



def main(app_id: str):
    main_app = client.fetch_app(app_id)
    main_dsl = client.fetch_app_dsl(app_id)
    main_dsl = yaml.safe_load(main_dsl)

    tabs = ['应用详情', 'DSL详情', '工具详情', '图分析', '递归导出JSON', '递归导入JSON']
    tab = st.tabs(tabs)

    with tab[0]:
        st.write(main_app)

    with tab[1]:
        st.write(main_dsl)
    
    with tab[2]:
        try:
            main_tools = client.fetch_workflow_tool(workflow_app_id=app_id)
            st.write(main_tools)
        except Exception as e:
            st.error(e)

    with tab[3]:
        graph = main_dsl['workflow']['graph']
        nodes = graph['nodes']
        edges = graph['edges']
        
        graph_tabs = ['节点', '边', '工具']
        graph_tab = st.tabs(graph_tabs)
        with graph_tab[0]:
            nodes_df = pd.DataFrame(nodes)
            st.write(nodes_df)

        with graph_tab[1]:
            st.write(edges)

        with graph_tab[2]:
            for node in nodes:
                if node['data']['type'] == 'tool':
                    tool_id = node['data']['provider_id']
                    tool = client.fetch_workflow_tool(workflow_tool_id=tool_id)
                    st.write(tool)
                    tool_workflow_app_id = tool['workflow_app_id']
                    tool_app = client.fetch_app(tool_workflow_app_id)
                    st.write(tool_app)

    with tab[4]:
        if st.button('导出JSON'):
            with st.spinner('正在导出JSON...'):
                progress_text = st.empty()
                def on_progress(app_id: str, progress: int):
                    progress_text.text(f'[{progress}]{app_id}')
                export_json = client.export_app_json(app_id, on_progress)
                st.download_button(
                    label='下载JSON',
                    data=json.dumps(export_json, indent=4), 
                    mime='application/json', 
                    file_name=f'{export_json["name"]}_批量导出_{time.strftime("%Y%m%d")}.json')
                # 展示导出结果，用DF来展示
                export_dsl_df = pd.DataFrame(export_json['dsl'].values())
                export_tool_df = pd.DataFrame(export_json['tool'].values())
                st.subheader(f'DSL {len(export_dsl_df)} 个')
                st.write(export_dsl_df)
                st.subheader(f'工具 {len(export_tool_df)} 个')
                st.write(export_tool_df)

    with tab[5]:
        # 上传JSON文件
        json_file = st.file_uploader('上传JSON文件', type='json')
        prefix = st.text_input('前缀', value='')
        suffix = st.text_input('后缀', value='')
        tags = st.text_input('标签', value='')
        
        if st.button('导入'):
            # 创建标签，逗号分隔，移除空白字符
            tags = tags.split(',')
            tags = [tag.strip() for tag in tags if tag.strip()]
            tag_ids = []
            for tag in tags:
                tag_ids.append(client.create_tag(tag)['id'])
            
            with st.spinner('正在导入JSON...'):
                try:
                    json_data = json.load(json_file)
                    client.import_app_json(json_data, prefix, suffix, tag_ids)
                    st.success('导入成功')
                except Exception as e:
                    st.error(e)
                    raise e


if MAIN_APP_ID:
    main(MAIN_APP_ID)
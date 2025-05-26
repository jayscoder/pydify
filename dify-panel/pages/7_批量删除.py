import re
import time  # 导入time模块，用于模拟耗时操作或在实际操作中控制频率

import pandas as pd
import streamlit as st
from utils.dify_client import DifyClient
from utils.ui_components import page_header, site_sidebar

# 设置页面配置，定义页面的标题、图标、布局和侧边栏初始状态
# page_title: 浏览器标签页上显示的标题
# page_icon: 浏览器标签页上显示的图标 (这里是一个删除相关的表情符号)
# layout: 页面布局方式，"wide"表示宽屏布局
# initial_sidebar_state: 侧边栏的初始状态，"expanded"表示默认展开
st.set_page_config(  # 这里原代码使用的是 st.page_container，但根据Streamlit文档和常见用法，st.set_page_config 更适合在脚本开头设置页面全局属性。如果st.page_container是特定封装，请忽略此注释。
    page_title="批量删除 - Dify管理面板",
    page_icon="🗑️",  # 将图标修正为垃圾桶图标，更符合删除功能
    layout="wide",
    initial_sidebar_state="expanded",
)


def main():
    """
    主函数，用于渲染批量删除页面内容和处理删除逻辑
    """
    # 显示侧边栏
    site_sidebar()

    # 页面标题和描述
    page_header("批量删除应用", "输入应用ID进行批量删除操作。")

    # 创建一个文本输入框，让用户输入要删除的应用ID
    # label: 输入框的标签提示文字
    # help: 输入框下方的帮助提示文字
    delete_ids_input = st.text_area(
        "请输入要删除的应用ID", help="每行一个ID，或用逗号分隔多个ID。"
    )
    # 使用正则表达式按换行符或逗号分割输入的字符串，得到ID列表
    # re.split(r'[\n,]', delete_ids_input) 会根据换行符(\n)或逗号(,)来分割字符串
    delete_ids = re.split(r"[\n,]", delete_ids_input)
    # 清理每个ID字符串：去除首尾空格，并过滤掉空字符串
    # id.strip() 用于去除字符串两端的空白字符
    # [id.strip() for id in delete_ids if id.strip()] 列表推导式，高效处理列表
    delete_ids = [id.strip() for id in delete_ids if id.strip()]
    # 检查用户是否输入了ID
    if len(delete_ids) > 0:
        all_apps = DifyClient.get_connection().fetch_all_apps()
        apps_df = pd.DataFrame(all_apps)
        apps_df = apps_df[["id", "name", "created_at", "updated_at"]]
        apps_df = apps_df[apps_df["id"].isin(delete_ids)]

        st.dataframe(apps_df)
        # 创建一个删除按钮，当用户点击时执行删除操作
        if st.button("开始删除", type="primary"):  # "type='primary'" 使按钮更醒目
            # 检查清理后的ID列表是否为空
            if len(delete_ids) > 0:
                # 获取Dify客户端实例
                client = DifyClient.get_connection()
                # 创建一个进度条，用于显示删除进度
                # 0 是初始值，len(delete_ids) 是最大值
                progress_bar = st.progress(0, text="准备开始删除...")
                # 记录成功删除的数量
                success_count = 0
                # 记录失败删除的ID和原因
                failed_deletions = []

                # 遍历ID列表，逐个删除应用
                for index, app_id in enumerate(delete_ids):
                    try:
                        # 调用Dify客户端的delete_app方法删除应用
                        client.delete_app(app_id=app_id)
                        # 更新成功计数
                        success_count += 1
                        # 在界面上显示删除成功的消息
                        st.toast(f"✅ 应用 {app_id} 删除成功！", icon="🎉")
                    except Exception as e:
                        # 如果删除过程中发生错误，记录失败信息
                        error_message = f"❌ 应用 {app_id} 删除失败: {e}"
                        st.toast(error_message, icon="🚨")
                        failed_deletions.append({"id": app_id, "reason": str(e)})

                    # 更新进度条
                    # (index + 1) 是当前处理完成的项数
                    # len(delete_ids) 是总项数
                    # text 参数用于在进度条旁边显示文本
                    progress_value = (index + 1) / len(delete_ids)
                    progress_bar.progress(
                        progress_value,
                        text=f"正在删除: {app_id} ({index + 1}/{len(delete_ids)})",
                    )
                    time.sleep(
                        0.1
                    )  # 短暂暂停，让用户能看清进度更新，实际API调用可能不需要

                # 所有ID处理完毕后，更新进度条到完成状态
                progress_bar.progress(1.0, text="批量删除操作完成！")

                # 显示总结信息
                st.success(f"🎉 批量删除操作完成！成功删除 {success_count} 个应用。")
                if failed_deletions:
                    st.error(f"⚠️ 有 {len(failed_deletions)} 个应用删除失败：")
                    for item in failed_deletions:
                        st.markdown(
                            f"- **ID:** `{item['id']}` - **原因:** {item['reason']}"
                        )
                elif success_count == len(delete_ids):
                    st.balloons()  # 如果全部成功，放气球庆祝

            else:
                # 如果清理后的ID列表为空，提示用户输入有效的ID
                st.error("🚫 请输入有效的应用ID。")


# Python的入口点检查，确保当脚本被直接执行时调用main函数
if __name__ == "__main__":
    main()

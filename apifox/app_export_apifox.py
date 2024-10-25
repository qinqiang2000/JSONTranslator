import json
import logging
import os
from dotenv import load_dotenv
import streamlit as st
import threading

from singlefile_apifox import export_apifox

# 设置你的密码
PASSWORD = "fpy2024"

# 创建一个 session state 用于存储认证状态
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

# 配置日志
logging.basicConfig(format='[%(asctime)s %(filename)s:%(lineno)d] %(levelname)s: %(message)s', level=logging.INFO, force=True)


# 读取JSON文件
def load_json(json_file):
    # 定义临时路径
    tmp_dir = 'tmp'
    os.makedirs(tmp_dir, exist_ok=True)  # 确保目录存在

    file_path = os.path.join(tmp_dir, json_file.name)

    # 将上传的文件保存到指定路径
    with open(file_path, 'wb') as f:
        f.write(json_file.getbuffer())

    logging.info(f"文件已保存到: {file_path}")

    return file_path


# 保存翻译后的JSON文件为StringIO对象以便下载
def save_json_to_stringio(data):
    with open("../output.json", 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    json_str = json.dumps(data, ensure_ascii=False, indent=4)
    return json_str


def show_status(text):
    if "log_placeholder" in st.session_state:
        st.session_state["log_placeholder"].markdown(text, unsafe_allow_html=True)


def do_export(url, json_file):
    file_path = load_json(json_file)
    return export_apifox(url, file_path, show_status)


# Streamlit界面
def main_page():
    st.title("Apifox导出")
    site_url = st.text_input("1.请输入要导出的apifox网址。注意：需要是自定义域名的，不能是apifox自动生成的")
    if not site_url or (not site_url.startswith("https://") and not site_url.startswith("http://")):
        st.error("请输入要导出的项目网址首页")
        return

    # 上传文件的部分
    uploaded_file = st.file_uploader("2.请上传apifox导出的json文件，方法：项目设置->导出数据->选择Apifox格式->导出", type="json")

    # 如果有上传文件，开始处理
    if uploaded_file is not None:
        # 显示文件名
        st.write(f"已上传文件: {uploaded_file.name}")

        # 日志占位符，实时更新日志
        st.session_state["log_placeholder"] = st.empty()

        # 翻译并生成可以下载的JSON
        with st.spinner('正在导出,可能需几分钟到10分钟不等...'):
            zip_path = do_export(site_url, uploaded_file)

        st.success('导出完成！')

        with open(zip_path, "rb") as f:
            st.download_button(
                label="下载文档",
                data=f,
                file_name=zip_path.split("/")[-1],
                mime="application/zip",
                on_click=lambda: setattr(st.session_state, 'authenticated', False)  # 点击后设置下载状态
            )


# 创建密码输入框
def login():
    st.title("Login Page")
    password = st.text_input("Enter your password:", type="password")
    if st.button("Login"):
        if password == PASSWORD:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Incorrect password")


if __name__ == "__main__":
    # 显示密码页面或主页面
    if st.session_state.authenticated:
        main_page()
    else:
        login()
import json
import os
from dotenv import load_dotenv
import streamlit as st
from io import StringIO
from groq import Groq

load_dotenv(override=True)
client = Groq(api_key=os.environ.get("GROQ_API_KEY"), )


# 假设这个函数已经实现了，将中文翻译为英文
def translate_text(text):
    sys_prompt = "将所给的文本中的中文，翻译成英文。要求：1）不要改动非中文以外的任何符号；2）只返回翻译结果，不要包含其他内容"
    completion = client.chat.completions.create(
        model="llama-3.1-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": sys_prompt
            },
            {
                "role": "user",
                "content": text
            }
        ],
        temperature=0,
    )

    ret = completion.choices[0].message.content
    return ret


# 递归遍历JSON，翻译所有中文内容
def translate_json(data, log_placeholder=None):
    if isinstance(data, dict):
        # 如果是字典，遍历所有键值对
        for key, value in data.items():
            data[key] = translate_json(value, log_placeholder)
    elif isinstance(data, list):
        # 如果是列表，遍历所有元素
        for i in range(len(data)):
            data[i] = translate_json(data[i], log_placeholder)
    elif isinstance(data, str):
        # 如果是字符串，检查是否包含中文
        if any('\u4e00' <= char <= '\u9fff' for char in data):
            ret = translate_text(data)
            if log_placeholder:
                log_placeholder.markdown(f"```Source```：{data}<br>```Translated``` ：{ret}",  unsafe_allow_html=True)
            return ret
    return data


# 读取JSON文件
def load_json(json_file):
    stringio = StringIO(json_file.getvalue().decode("utf-8"))
    return json.load(stringio)


# 保存翻译后的JSON文件为StringIO对象以便下载
def save_json_to_stringio(data):
    with open("output.json", 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    json_str = json.dumps(data, ensure_ascii=False, indent=4)
    return json_str


# 主函数：加载原始JSON -> 翻译 -> 返回翻译后的文件
def translate_and_save_json(json_file, log_placeholder):
    # 加载原始JSON文件
    original_data = load_json(json_file)

    # 翻译JSON中的所有中文内容
    translated_data = translate_json(original_data, log_placeholder)

    # 将翻译后的数据转换为StringIO对象
    return save_json_to_stringio(translated_data)


# Streamlit界面
def main():
    st.title("JSON Translator")
    st.write("上传一个包含中文的JSON文件，系统将其中文部分翻译为英文。")

    # 上传文件的部分
    uploaded_file = st.file_uploader("选择一个JSON文件", type="json")

    # 如果有上传文件，开始处理
    if uploaded_file is not None:
        # 显示文件名
        st.write(f"已上传文件: {uploaded_file.name}")

        # 日志占位符，实时更新日志
        log_placeholder = st.empty()

        # 翻译并生成可以下载的JSON
        with st.spinner('正在翻译...'):
            translated_json_io = translate_and_save_json(uploaded_file, log_placeholder)

        st.success('翻译完成！')

        # 提供下载链接
        st.subheader("下载翻译后的JSON文件")
        st.download_button(
            label="下载翻译后的JSON",
            data=translated_json_io,
            file_name="translated_" + uploaded_file.name,
            mime="application/json"
        )


if __name__ == "__main__":
    main()
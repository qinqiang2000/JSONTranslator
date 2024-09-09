import json
import logging
import os
from dotenv import load_dotenv
import streamlit as st
from io import StringIO
from groq import Groq
from openai.lib.azure import AzureOpenAI

# 配置日志
logging.basicConfig(format='[%(asctime)s %(filename)s:%(lineno)d] %(levelname)s: %(message)s', level=logging.INFO, force=True)

load_dotenv(override=True)

provider = os.environ.get("LLM_PROVIDER")
if provider == "azure":
    client = AzureOpenAI(
        api_key=os.environ['AZURE_OPENAI_GPT4oMINI_API_KEY'],
        api_version=os.environ['OPENAI_API_GPT4oMINI_VERSION'],
        azure_endpoint=os.environ['AZURE_OPENAI_GPT4oMINI_ENDPOINT']
    )
    model = os.environ['OPENAI_GPT4OMIN_DEPLOYMENT_NAME']
else:
    client = Groq(api_key=os.environ.get("GROQ_API_KEY"), )
    model = "llama-3.1-70b-versatile"

sys_prompt = """将所给的文本中的中文，翻译成英文。
    注意：1）文本中的‘票’，默认是指‘发票’ 
    2）红票或红字发票: credit invoice 
    3）蓝票或蓝字发票: invoice 
    4）开票项: invoicing item
    5）数电票: fully digitized e-invoice
    6）专票或增值税专用发票: Special VAT Invoice
    7）普票或增值税普通发票: Normal VAT Invoice
    输出要求：1）不要改动输入文本的任何格式和符号 2）只返回翻译结果，不要包含其他内容 3)请保留原始文本中的段落结构"""


# 批量翻译函数，按文本列表的 item 数量分批处理
def translate_text(text_list, batch_size=30, log_placeholder=None):
    translated_texts = []

    split_tag = '\n🚀'
    # 分批处理，确保每批不超过 batch_size
    for i in range(0, len(text_list), batch_size):
        if log_placeholder:
            log_placeholder.markdown(f"翻译进度: {i} / {len(text_list)}")

        batch = text_list[i:i + batch_size]  # 切分成每 batch_size 个文本的子列表

        combined_text = split_tag.join(batch)
        completion = client.chat.completions.create(
            model=model,
            messages=[{"role": "system", "content": sys_prompt}, {"role": "user", "content": combined_text}],
            temperature=0,
        )

        # 分割翻译结果并添加到列表
        translated_batch = completion.choices[0].message.content.split(split_tag)

        print(f"[中文 {len(batch)} \n{batch}\n")
        print(f"[英文]: {len(translated_batch)} \n{translated_batch}\n")
        if len(batch) != len(translated_batch):
            if log_placeholder:
                log_placeholder.warning(f"==========错误===============\n"
                f"[中文]: {len(batch)} \n{combined_text} \n "
                f"[英文]: {len(translated_batch)} \n{translated_batch} {completion.choices[0].message.content} \n ")

            translated_texts.extend(batch)
        else:
            translated_texts.extend(translated_batch)

    return translated_texts


# 递归遍历 JSON，批量收集需要翻译的文本
def collect_translations(data, translations, translated_data, log_placeholder=None):
    translated_data = data
    if isinstance(data, dict):
        for key, value in data.items():
            translated_data[key] = collect_translations(value, translations, {}, log_placeholder)
    elif isinstance(data, list):
        translated_data = []
        for item in data:
            translated_data.append(collect_translations(item, translations, {}, log_placeholder))
    elif isinstance(data, str):
        if any('\u4e00' <= char <= '\u9fff' for char in data):
            translations.append(data)  # 收集中文文本进行批量翻译
            translated_data = data
        else:
            translated_data = data
    return translated_data


# 递归替换 JSON 中的中文内容
def replace_translations(data, translated_texts, index=0):
    if isinstance(data, dict):
        for key, value in data.items():
            data[key], index = replace_translations(value, translated_texts, index)
    elif isinstance(data, list):
        for i in range(len(data)):
            data[i], index = replace_translations(data[i], translated_texts, index)
    elif isinstance(data, str):
        if any('\u4e00' <= char <= '\u9fff' for char in data):
            data = translated_texts[index]
            index += 1
    return data, index


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


# 主函数：加载原始 JSON -> 翻译 -> 返回翻译后的文件
def translate_and_save_json(json_file, log_placeholder):
    # 加载原始 JSON 文件
    original_data = load_json(json_file)

    # 收集所有需要翻译的文本
    translations = []
    translated_data = collect_translations(original_data, translations, {}, log_placeholder)

    # 批量翻译
    if translations:
        translated_texts = translate_text(translations, log_placeholder=log_placeholder)

        log_placeholder.markdown(f"已翻译的条目: {len(translations)}", unsafe_allow_html=True)
        logging.info(f"Translated Entries: {len(translations)}")

        # 替换 JSON 中的翻译内容
        translated_data, _ = replace_translations(translated_data, translated_texts)

    # 将翻译后的数据转换为 StringIO 对象
    return save_json_to_stringio(translated_data)


# Streamlit界面
def main():
    global sys_prompt  # 声明使用全局变量

    st.title("JSON Translator")
    st.write("上传一个包含中文的JSON文件，系统将其中文部分翻译为英文。")

    # 用户可以编辑sys_prompt的部分
    sys_prompt = st.text_area("提示词（可在此维护自定义术语）", sys_prompt, height=300)

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
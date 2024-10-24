"""
处理通过single-file 爬下来的apifox网页
"""
import json
import shutil
import subprocess
import re
from datetime import datetime
from bs4 import BeautifulSoup
import os

from extractEnums import extract_enums
from generateEnumHtml import generate_enum_html_v2


def check_and_remove_useless_html(file_path, soup):
    """
    检查是否存在无用 HTML 的特征：
    1. h2 元素的值是 '页面不存在'
    2. p 元素的值为 '找不到您要查找的页面'
    如果满足条件，则删除该 HTML 文件。
    """
    h2_tag = soup.find('h2', string="页面不存在")
    p_tag = soup.find('p', string="找不到您要查找的页面")

    # 同时存在符合条件的 h2 和 p 标签时删除文件
    if h2_tag and p_tag:
        print(f"Deleting file: {file_path} (contains '页面不存在' and '找不到您要查找的页面')")
        os.remove(file_path)
        return True

    return False


def wrap_button_in_a_tag(soup):
    # 找到所有 class="menu__list-item-collapsible" 的 <div>
    collapsible_divs = soup.find_all('div', class_="menu__list-item-collapsible")

    for div in collapsible_divs:
        # 找到 <a> 和 <button> 元素
        a_tag = div.find('a')
        button_tag = div.find('button')

        # 确保 <a> 和 <button> 同时存在
        if a_tag and button_tag:
            # 将 <button> 移动为 <a> 的子元素
            a_tag.append(button_tag)


def add_export_time_link(soup):
    # 找到指定的 <div> 元素
    div = soup.find('div', class_="pui-pages-public-project-doc-navigation-bar-index-nav-bar__right-feature")

    if not div:
        return

    # 检查是否已经有 <a> 元素
    if div.find('a'):
        return  # 如果已经存在 <a> 元素，直接退出

    current_date = datetime.now().strftime('%Y-%m-%d')

    # 创建新的 <a> 元素
    new_link = soup.new_tag('a', href='#', target='_blank')
    new_link['class'] = 'ui-tabs'
    new_link.string = f"本文导出日期: {current_date}"

    # 将 <a> 元素添加为该 <div> 的子元素
    div.append(new_link)


# 删除指定的 <div> 元素
def remove_specific_div(soup):
    div = soup.find('div', class_="pui-components-f-a-b-index-fab fixed")
    if div:
        div.decompose()  # 删除 div 元素

    # 删除内容为 "示例代码" 的 <h3> 及其后紧跟的第一个 <div>
    for h3 in soup.find_all('h3'):
        if h3.string == "示例代码":  # 检查 <h3> 标签的文本内容是否为 "示例代码"
            next_div = h3.find_next_sibling('div')  # 找到紧跟着的第一个 <div>
            h3.decompose()  # 删除 <h3> 标签
            if next_div:
                next_div.decompose()  # 删除紧跟着的 <div>


# 提取URL的最后一个段落
def get_last_segment(href):
    # 检查是否有路径段，排除只有域名的情况
    match = re.search(r'\/([^\/]+)\/?$', href)

    # 如果 href 没有路径段，或者以域名结束（没有路径），返回 '#'
    if not match or href.rstrip('/').count('/') <= 2:
        return '#'

    return f'{match.group(1)}.html'


# 删除指定的 <img> 元素
def remove_images_from_div(soup):
    div = soup.find('div', class_="w-full pui-pages-shared-doc-sider-index-theme-switch")
    if div:
        for img in div.find_all('img'):
            img.decompose()  # 删除 img 元素


# 替换特定的文本和链接
def replace_text_and_links(soup):
    # 替换文本 "Run in Apifox" 为 "Run"
    for text in soup.find_all(string="Run in Apifox"):
        text.replace_with("Run")

    # 替换文本 "Apifox" 为 "金蝶发票云" (大小写敏感)
    for text in soup.find_all(string=re.compile(r'Apifox')):
        updated_text = text.replace("Apifox", "金蝶发票云")
        text.replace_with(updated_text)

    # 替换 href="https://apifox.com/" 为 href="https://www.piaozone.com/"
    for tag in soup.find_all(href="https://apifox.com/"):
        tag['href'] = "https://open.piaozone.com/"
        tag['target'] = "_blank"


# 插入枚举值说明信息
def insert_enum_table(filename, api_schema, soup):
    # 1. 从 filename 获取 id，'api-{id}' 的格式
    if 'api-' in filename:
        api_id = filename.split('api-')[1]  # 获取 'api-' 之后的部分作为 id
    else:
        return soup

    # 检查是否包含 id=piaozone_num 的 div
    if soup.find('div', id='piaozone_enum'):
        return soup  # 如果存在，直接返回 soup

    # 2. 调用 generate_table 返回 html 字符串（伪代码）
    result = extract_enums(api_schema, api_id)
    table_html = generate_enum_html_v2(result)
    if not table_html:
        return soup

    # 3. 找到 class="pui-pages-shared-doc-http-api-index-container w-full" 的 div
    container_div = soup.find('div', class_='pui-pages-shared-doc-http-api-index-container w-full')

    if not container_div:
        raise ValueError(
            "Could not find the container div with class 'pui-pages-shared-doc-http-api-index-container w-full'")

    # 4. 在该 div 内找到最后一个 class="group-content" 的子 div
    group_content_divs = container_div.find_all('div', class_='group-content')

    if not group_content_divs:
        return soup

    last_group_content_div = group_content_divs[-1]  # 获取最后一个 group-content div

    # 5. 在子 div 后面加上第 2 步生成的 HTML
    last_group_content_div.insert_after(BeautifulSoup(table_html, 'html.parser'))

    return soup


def inject_scroll_script(soup):
    # 创建 <script> 标签
    script_content = """
    function scrollToExactActiveLink() {
  const sidebar = document.querySelector('.pui-pages-main-tree-list-index-content__tree.overflow-y-scroll.h-full');
  console.log(sidebar);

  // 获取所有 class 包含 "menu__link" 和 "menu__link--active" 的 <a> 元素
  const links = document.querySelectorAll('a.menu__link.menu__link--active');

  // 找到 class 只有 "menu__link" 和 "menu__link--active" 的 <a> 元素
  const exactActiveLink = Array.from(links).find(link => {
      // 检查该 <a> 的 classList 是否正好包含 2 个类
      return link.classList.length === 2;
  });

  if (exactActiveLink) {
      console.log('找到仅包含 class="menu__link menu__link--active" 的 <a> 元素', exactActiveLink);
      // 计算 <a> 在 sidebar 中的相对位置
      const linkRect = exactActiveLink.getBoundingClientRect();
      const sidebarRect = sidebar.getBoundingClientRect();
      
      // 计算目标位置
      const targetScrollTop = linkRect.top - sidebarRect.top + sidebar.scrollTop - 39;
      console.log(targetScrollTop);
      
      // 滚动 sidebar 到目标位置
      sidebar.scrollTop = targetScrollTop;
  } else {
      console.log('未找到仅包含 class="menu__link menu__link--active" 的 <a> 元素');
  }
}
    window.onload = scrollToExactActiveLink;
    """

    # 创建 <script> 标签并插入内容
    script_tag = soup.new_tag('script')
    script_tag.string = script_content
    soup.body.append(script_tag)


def extract_html_styles(file_path, soup):
    # 1. 获取文件所在目录
    file_dir = os.path.dirname(file_path)
    css_path = os.path.join(file_dir, '1.css')

    # 2. 检查是否存在 1.css 文件
    if not os.path.exists(css_path):
        # 3.1 如果不存在，提取 <style> 标签内容并保存到 1.css
        style_content = ""
        for style_tag in soup.find_all('style'):
            style_content += style_tag.string if style_tag.string else ""

        if style_content:
            # 将 <style> 的内容写入到 1.css 文件中
            with open(css_path, 'w', encoding='utf-8') as css_file:
                css_file.write(style_content)

    # 3.2 删除所有的 <style> 标签
    for style_tag in soup.find_all('style'):
        style_tag.decompose()  # 删除 <style> 标签

    # 4. 添加 <link rel="stylesheet" href="1.css"> 引用
    if not soup.find('link', {'rel': 'stylesheet', 'href': '1.css'}):
        link_tag = soup.new_tag('link', rel='stylesheet', href='1.css')
        soup.html.insert(0, link_tag)

    return soup


# 处理单个HTML文件
def process_html_file(file_path, api_schema, keywords):
    with open(file_path, 'r', encoding='utf-8') as file:
        soup = BeautifulSoup(file, 'html.parser')

    if check_and_remove_useless_html(file_path, soup):
        return

    # 查找并处理所有带有 href 的标签
    for tag in soup.find_all(href=True):
        href = tag['href']

        # 移除 target="_blank" 属性
        if tag.has_attr('target') and tag['target'] == '_blank':
            del tag['target']

        # 跳过不包含关键词的链接
        if not any(keyword in href for keyword in keywords):
            continue

        # 提取并替换 URL 的最后一段
        tag['href'] = get_last_segment(href)

    # 在文档说明插入枚举值描述链接
    fn = os.path.splitext(os.path.basename(file_path))[0]
    insert_enum_table(fn, api_schema, soup)

    # 删除特定 div 下的 <img> 标签
    remove_images_from_div(soup)

    # 替换文本和链接
    replace_text_and_links(soup)

    # 删除指定的 <div>
    remove_specific_div(soup)

    # 增加导出说明
    add_export_time_link(soup)

    # 对 class="menu__list-item-collapsible" 的 div 进行修改
    wrap_button_in_a_tag(soup)

    # 向 document 增加 scrollToExactActiveLink 脚本
    inject_scroll_script(soup)

    # 提取css为单一文件
    # extract_html_styles(file_path, soup)

    # 将修改后的HTML写回文件
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(str(soup))


# 查找唯一包含关键词的文件并重命名为 index.html
def rename_file_if_needed(directory, keyword):
    # 查找所有文件名中包含关键词的 HTML 文件
    matching_files = [f for f in os.listdir(directory) if f.endswith('.html') and keyword in f]

    # 检查是否只有一个匹配文件，并且没有 index.html 文件
    if len(matching_files) == 1 and 'index.html' not in os.listdir(directory):
        old_file_path = os.path.join(directory, matching_files[0])
        new_file_path = os.path.join(directory, 'index.html')
        os.rename(old_file_path, new_file_path)
        print(f'Renamed: {matching_files[0]} to index.html')


def create_endpoint_filemapping(directory):
    # 创建一个字典用于存放文件名映射关系
    file_mapping = {}

    # 遍历目录中的所有文件
    for filename in os.listdir(directory):
        # 只处理以 .html 结尾的文件
        if not filename.endswith('.html'):
            continue  # 跳过不是 .html 的文件

        # 提取文件名（不含扩展名）
        name_without_extension = filename[:-5]  # 去掉 '.html'

        # 检查文件名是否以 'endpoint-' 开头
        if not name_without_extension.startswith('endpoint-'):
            continue  # 跳过不以 'endpoint-' 开头的文件

        # 获取关键词
        keyword = name_without_extension[len('endpoint-'):]

        # 在目录中寻找包含此关键词的其他文件名
        for other_filename in os.listdir(directory):
            if not other_filename.endswith('.html'):
                continue  # 跳过不是 .html 的文件

            other_name_without_extension = other_filename[:-5]

            # 如果找到包含关键词的文件名且不与当前文件名相同
            if keyword in other_name_without_extension and other_name_without_extension != name_without_extension:
                # 将映射关系添加到字典中
                file_mapping[name_without_extension] = other_name_without_extension

    return file_mapping


def deduplicate_file(directory):
    # 获取映射关系，用于替换其他html的链接内容
    file_mapping = create_endpoint_filemapping(directory)

    # 遍历目录中的所有文件
    for filename in os.listdir(directory):
        if not filename.endswith('.html'):
            continue  # 跳过不是 .html 的文件

        file_path = os.path.join(directory, filename)

        # 读取 HTML 文件内容
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
        except Exception as e:
            print(f"读取文件 {file_path} 时出错: {e}")
            continue

        # 替换文件内容中的 key 为 value
        for key, value in file_mapping.items():
            content = content.replace(key, value)

        # 将修改后的内容写回文件
        try:
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(content)
        except Exception as e:
            print(f"写入文件 {file_path} 时出错: {e}")

    # 删除所有以 'endpoint-' 开头的 HTML 文件
    for filename in os.listdir(directory):
        if filename.endswith('.html') and filename.startswith('endpoint-'):
            file_path = os.path.join(directory, filename)
            try:
                os.remove(file_path)
                print(f"已删除文件: {file_path}")  # 可选：打印已删除的文件路径
            except Exception as e:
                print(f"删除文件 {file_path} 时出错: {e}")


# 处理目录中的所有HTML文件
def process_directory(directory, data_schema_path, keywords=['piaozone']):
    # 检查是否需要重命名文件为 index.html
    rename_file_if_needed(directory, 'piaozone.')

    # 处理重复文件
    deduplicate_file(directory)

    with open(data_schema_path, 'r', encoding='utf-8') as f:
        api_schema = json.load(f)

    for item in os.listdir(directory):
        file_path = os.path.join(directory, item)
        if os.path.isfile(file_path) and item.endswith('.html'):
            process_html_file(file_path, api_schema, keywords)
            print(f'Processed: {file_path}')


# 导出url对应的站点
def run_single_file_script(output_directory, url):
    # 定义脚本和用户脚本的路径
    script_path = os.path.join('script', 'single-file')
    user_script_path = os.path.join('script', 'userScript.js')

    # 构建命令参数
    command = [
        script_path,
        url,
        '--filename-template={url-last-segment}.html',
        '--crawl-replace-URLs=true',
        # '--crawl-links=true',
        '--filename-conflict-action=skip',
        '--crawl-max-depth=3',
        f'--output-directory={output_directory}',
        f'--browser-script={user_script_path}'
    ]

    try:
        # 运行脚本
        result = subprocess.run(command, check=True, text=True, capture_output=True)
        print("脚本执行成功:")
        print(result.stdout)  # 打印标准输出
    except subprocess.CalledProcessError as e:
        print("脚本执行失败:")
        print(e.stderr)  # 打印标准错误输出
    except Exception as e:
        print(f"发生错误: {e}")


def backup_data(src, dest):
    os.makedirs(dest, exist_ok=True)

    # 仅复制当前目录的HTML文件，不复制其他内容和子目录
    for item in os.listdir(src):
        source_file = os.path.join(src, item)
        # 检查是否为文件
        if os.path.isfile(source_file):
            shutil.copy2(source_file, dest)  # 使用copy2保留元数据


def compress_directory_to_zip(source_dir, output_zip):
    # 确保输出文件路径以 .zip 结尾
    if not output_zip.endswith('.zip'):
        output_zip += '.zip'

    # 创建 zip 文件
    shutil.make_archive(output_zip.replace('.zip', ''), 'zip', root_dir=os.path.dirname(source_dir), base_dir=os.path.basename(source_dir))


def export_apifox(url, apifox_data_path, log_function=None):
    base_name = os.path.splitext(os.path.basename(apifox_data_path))[0]
    output_directory = 'dist/' + base_name + '_' + datetime.now().strftime('%Y%m%d%H%M')

    os.makedirs(output_directory, exist_ok=True)

    # 先用single-file导出整站
    if log_function:
        log_function(f"正在导出站点: {url}")
    run_single_file_script(output_directory, url)
    print(f"已完成single-file导出到: {output_directory}")

    # 备份原始数据
    backup_data(output_directory, output_directory + '_bak')

    # 对下载的文件做后处理
    process_directory(output_directory, apifox_data_path)

    output_zip = 'dist/' + base_name + '.zip'
    compress_directory_to_zip(output_directory, output_zip)

    print(f"已完成apifox导出到: {output_zip}")
    return output_zip


def test_all():
    _url = 'https://open.piaozone.com/'
    # 先用apifox导出数据apifox格式的json数据
    data_path = 'data/发票云(旗舰版)API文档.apifox.20241021.json'

    export_apifox(_url, data_path)


def test_post_process():
    _url = 'https://open.piaozone.com/'
    # 先用apifox导出数据apifox格式的json数据
    data_path = 'data/发票云(旗舰版)API文档.apifox.20241021.json'

    process_directory('dist/test', data_path)


def test_any(path):
    with open(path, 'r', encoding='utf-8') as f:
        api_schema = json.load(f)
        print(api_schema)


if __name__ == "__main__":
    # test_all()
    test_post_process()
    # ./single-file https://open-ultimate.piaozone.com --filename-template={url-last-segment}.html --crawl-replace-URLs=true --crawl-links=true --filename-conflict-action=skip --crawl-max-depth=4 --output-directory=piaozone-ultimate
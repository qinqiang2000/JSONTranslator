import shutil
import os

def compress_directory_to_zip(source_dir, output_zip):
    # 确保输出文件路径以 .zip 结尾
    if not output_zip.endswith('.zip'):
        output_zip += '.zip'

    # 创建 zip 文件
    shutil.make_archive(output_zip.replace('.zip', ''), 'zip', root_dir=os.path.dirname(source_dir), base_dir=os.path.basename(source_dir))

# 示例用法
source_directory = '../apifox/dist/发票云（智能特性）_202410242259'  # 要压缩的目录
output_zip_file = 'a.zip'  # 生成的 zip 文件名
compress_directory_to_zip(source_directory, output_zip_file)
import os

from flask import current_app
from werkzeug.utils import secure_filename


def handle_file_upload(file, file_location):
    if not file:
        current_app.logger.warning(f"{file_location} 文件为空")
        return None

    folder = current_app.config[f'{file_location.upper()}_FOLDER']  # 动态获取文件夹配置

    # 确保文件夹存在
    os.makedirs(folder, exist_ok=True)

    # 保存文件
    filename = secure_filename(file.filename)
    file_path = os.path.join('static', file_location, filename)  # 存储相对路径
    file.save(os.path.join(folder, filename))  # 存储文件

    current_app.logger.info(f"{file_location} 文件已保存：{file_path}")
    return file_path

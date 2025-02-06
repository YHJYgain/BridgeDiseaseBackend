import os

from flask import current_app
from werkzeug.utils import secure_filename


def handle_avatar_upload(avatar_file):
    if not avatar_file:
        current_app.logger.warning("头像文件为空")
        return None

    avatar_folder = current_app.config['AVATAR_FOLDER']

    # 确保头像文件夹存在
    os.makedirs(avatar_folder, exist_ok=True)

    # 保存头像文件
    avatar_filename = secure_filename(avatar_file.filename)  # 获取安全的文件名
    avatar_path = os.path.join('static', 'avatars', avatar_filename)  # 存储相对路径
    avatar_file.save(os.path.join(avatar_folder, avatar_filename))  # 存储在 app/static/avatars 文件夹

    current_app.logger.info(f"头像文件已保存：{avatar_path}")
    return avatar_path

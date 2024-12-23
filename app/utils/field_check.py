import re

from flask import current_app


# 头像文件校验
def is_valid_avatar_file(avatar_file):
    """
    校验头像文件是否合规。

    :param avatar_file: 头像文件
    :return: 如果合规，返回 True，否则返回 False。
    """
    # 读取头像文件配置
    allowed_extensions = current_app.config['ALLOWED_EXTENSIONS']
    max_avatar_size = current_app.config['MAX_AVATAR_SIZE'] / (1024 * 1024)  # MB

    # 校验文件类型
    if not ('.' in avatar_file.filename and avatar_file.filename.rsplit('.', 1)[1].lower() in allowed_extensions):
        return False

    # 校验文件大小
    avatar_size = len(avatar_file.read()) / (1024 * 1024)  # MB
    if avatar_size > max_avatar_size:
        return False

    # 重置文件读取指针
    avatar_file.seek(0)
    return True


# 邮箱校验
def is_valid_email(email):
    """
    校验邮箱格式是否有效。

    :param email: 邮箱地址
    :return: 如果邮箱格式正确，返回 True，否则返回 False。
    """
    email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return re.match(email_regex, email) is not None


# 手机号校验
def is_valid_phone(phone):
    """
    校验手机号格式是否有效。

    :param phone: 手机号码
    :return: 如果手机号格式正确，返回 True，否则返回 False。
    """
    phone_regex = r'^\+?\d{10,15}$'
    return re.match(phone_regex, phone) is not None

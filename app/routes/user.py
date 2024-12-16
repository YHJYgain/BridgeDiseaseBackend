import os
import re

from flask import request, jsonify, current_app
from werkzeug.security import generate_password_hash
from werkzeug.utils import secure_filename

from . import user_routes
from .. import User, db


@user_routes.route('/register', methods=['POST'])
def register():
    """
    用户注册接口，处理用户注册流程。

    该函数接收前端传来的注册信息，包括用户名、邮箱、密码、头像、手机号等，并进行校验。
    校验通过后，将用户信息保存到数据库，并返回注册成功消息。

    注册流程：
    1. 校验必填字段（用户名、邮箱、密码）。
    2. 校验邮箱格式和手机号格式。
    3. 校验角色是否合法（'admin'、'developer'、'user'）。
    4. 检查用户名和邮箱是否已经存在。
    5. 对密码进行加密。
    6. 如果上传了头像，保存头像文件并生成相对路径。
    7. 将新用户的数据保存到数据库。

    :return: 返回包含注册结果的 JSON 响应。
    :rtype: flask.Response
    """
    # 获取请求中的表单数据
    username = request.form.get('username')
    email = request.form.get('email')
    password = request.form.get('password')
    first_name = request.form.get('first_name')
    last_name = request.form.get('last_name')
    role = request.form.get('role', 'user')  # 默认角色为 'user'
    avatar_file = request.files.get('avatar_file')
    phone = request.form.get('phone')

    # 校验必填字段
    if not username or not email or not password:
        current_app.logger.warning(f"注册失败：用户名、邮箱或密码为空：{request.form}")
        return jsonify({'message': '注册失败：用户名、邮箱和密码是必填项'}), 400

    # 校验邮箱格式
    if not is_valid_email(email):
        current_app.logger.warning(f'注册失败：无效的邮箱格式：{email}')
        return jsonify({'message': '注册失败：无效的邮箱格式', 'email': email}), 400

    # 校验角色是否有效
    if role not in ['admin', 'developer', 'user']:
        current_app.logger.warning(f'注册失败：无效的角色 {role}')
        return jsonify({'message': '注册失败：无效的角色', 'role': role}), 400

    # 校验头像文件是否合规
    max_avatar_size = current_app.config['MAX_AVATAR_SIZE']
    current_app.logger.info(f'头像最大文件大小：{max_avatar_size / (1024 * 1024)}MB')
    if avatar_file:
        # 检查文件格式
        if not allowed_file(avatar_file.filename):
            current_app.logger.warning(f"注册失败：不支持的头像文件格式：{avatar_file.filename}")
            return jsonify({'message': '注册失败：头像文件格式不支持，仅支持 png, jpg, jpeg 格式',
                            'avatar_filename': avatar_file.filename}), 400

        # 检查文件大小
        avatar_size = len(avatar_file.read())
        if avatar_size > max_avatar_size:
            current_app.logger.warning(f"注册失败：头像文件太大：{avatar_size / (1024 * 1024)}MB")
            return jsonify({'message': '注册失败：头像文件太大，最大允许大小为 5MB', 'avatar_size': avatar_size}), 400

        # 重置文件读取指针
        avatar_file.seek(0)
        current_app.logger.info(
            f"头像文件读取成功，文件名：{avatar_file.filename}, 大小：{avatar_size / (1024 * 1024)}MB")

    # 校验手机号格式
    if phone and not is_valid_phone(phone):
        current_app.logger.warning(f'注册失败：无效的手机号格式：{phone}')
        return jsonify({'message': '注册失败：无效的手机号格式', 'phone': phone}), 400

    # 检查用户名和邮箱是否已经存在
    if User.query.filter_by(username=username).first():
        current_app.logger.warning(f'注册失败：用户名 {username} 已存在')
        return jsonify({'message': '注册失败：用户名已存在', 'username': username}), 400
    if User.query.filter_by(email=email).first():
        current_app.logger.warning(f'注册失败：邮箱 {email} 已存在')
        return jsonify({'message': '注册失败：邮箱已存在', 'email': email}), 400

    # 加密密码
    hashed_password = generate_password_hash(password)

    # 头像存储处理
    avatar_path = None
    if avatar_file:
        # 获取配置的头像文件夹路径
        avatar_folder = current_app.config['AVATAR_FOLDER']
        current_app.logger.info(f"头像文件夹绝对路径：{avatar_folder}")

        # 确保头像文件夹存在
        try:
            if not os.path.exists(avatar_folder):
                os.makedirs(avatar_folder)
                current_app.logger.info(f"头像文件夹创建成功：{avatar_folder}")
        except Exception as e:
            current_app.logger.error(f"创建头像文件夹失败：{str(e)}")
            return jsonify({'message': '服务器错误，无法处理头像文件夹'}), 500

        # 保存头像文件
        try:
            avatar_filename = secure_filename(avatar_file.filename)  # 获取安全的文件名
            avatar_path = os.path.join('static', 'avatars', avatar_filename)  # 存储相对路径
            avatar_file.save(os.path.join(avatar_folder, avatar_filename))  # 存储在 app/static/avatars 文件夹
            current_app.logger.info(f"头像文件已保存：{avatar_path}")
        except Exception as e:
            current_app.logger.error(f"保存头像文件失败：{str(e)}")
            return jsonify({'message': '头像文件保存失败'}), 500

    # 创建新用户
    new_user = User(
        username=username,
        email=email,
        password=hashed_password,
        first_name=first_name,
        last_name=last_name,
        role=role,
        avatar_path=avatar_path,
        phone=phone
    )

    # 添加到数据库
    try:
        db.session.add(new_user)
        db.session.commit()
        current_app.logger.info(f"新用户注册成功：{username} ({email})")
    except Exception as e:
        current_app.logger.error(f"保存新用户数据失败：{str(e)}")
        db.session.rollback()
        return jsonify({'message': '服务器错误，无法保存新用户数据'}), 500

    user_data = {
        'id': new_user.user_id,
        'username': new_user.username,
        'email': new_user.email,
        'first_name': new_user.first_name,
        'last_name': new_user.last_name,
        'role': new_user.role,
        'avatar_path': new_user.avatar_path,
        'phone': new_user.phone
    }

    return jsonify({'message': '用户注册成功', 'user': user_data}), 201


def allowed_file(filename):
    """
    判断上传的文件是否是允许的扩展名类型。

    :param filename: 文件名
    :return: 如果文件类型允许，返回 True，否则返回 False。
    """
    allowed_extensions = current_app.config['ALLOWED_EXTENSIONS']
    current_app.logger.info(f"允许的头像文件类型：{', '.join(allowed_extensions)}")
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions


# 邮箱校验
def is_valid_email(email):
    """
    校验邮箱格式是否有效。

    :param email: 邮箱地址
    :return: 如果邮箱格式正确，返回 True，否则返回 False。
    """
    email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return re.match(email_regex, email) is not None


# 手机号的基本校验
def is_valid_phone(phone):
    """
    校验手机号格式是否有效。

    :param phone: 手机号码
    :return: 如果手机号格式正确，返回 True，否则返回 False。
    """
    phone_regex = r'^\+?\d{10,15}$'
    return re.match(phone_regex, phone) is not None

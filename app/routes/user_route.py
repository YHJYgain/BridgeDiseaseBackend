import os
from datetime import datetime
from zoneinfo import ZoneInfo

from flask import request, jsonify
from flask_jwt_extended import create_access_token
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

from . import user_routes
from ..constants import OperationType, UserRole
from ..models.operation import Operation
from ..models.user import User
from ..utils import *


@user_routes.route('/register', methods=['POST'])
def register():
    start_time = time.time()  # 记录操作开始时间

    # 获取请求中的表单数据
    username = request.form.get('username')
    email = request.form.get('email')
    password = request.form.get('password')
    first_name = request.form.get('first_name')
    last_name = request.form.get('last_name')
    role = request.form.get('role', 'user')  # 默认角色为 'user'
    avatar_file = request.files.get('avatar_file')
    phone = request.form.get('phone')

    # 创建一个新的操作记录
    new_operation = Operation(
        operation_type=OperationType.CREATE,
        description="用户注册",
        ip_address=request.remote_addr,
        device_info=request.user_agent.string,
    )

    # 校验必填字段和其他常见验证
    validation_checks = [
        (not username or not email or not password, "【注册失败】用户名、邮箱或密码为空"),
        (not is_valid_email(email), f"【注册失败】无效的邮箱格式：{email}"),
        (role not in UserRole.list(), f"【注册失败】无效的角色：{role}，只限 'admin', 'developer', 'user'"),
        (avatar_file and not is_valid_avatar_file(avatar_file), "【注册失败】头像文件类型或大小不合规"),
        (phone and not is_valid_phone(phone), f"【注册失败】无效的手机号格式：{phone}")
    ]
    for condition, message in validation_checks:
        if condition:
            return handle_operation_failure(new_operation, start_time, message)

    # 检查用户名和邮箱是否已经存在
    if User.query.filter_by(username=username).first() or User.query.filter_by(email=email).first():
        failure_message = f"【注册失败】用户名 {username} 或邮箱 {email} 已注册"
        return handle_operation_failure(new_operation, start_time, failure_message)

    # 加密密码
    hashed_password = generate_password_hash(password)

    # 头像存储处理
    avatar_path = handle_avatar_upload(avatar_file)

    # 创建新用户
    new_user = User(
        username=username,
        email=email,
        password=hashed_password,
        first_name=first_name,
        last_name=last_name,
        role=role,
        avatar_path=avatar_path,
        phone=phone,
    )
    db.session.add(new_user)
    db.session.commit()

    # 提交操作记录
    new_operation = handle_operation_success(new_operation, start_time, new_user.user_id)

    current_app.logger.info(f"【注册成功】user: {new_user}")
    return jsonify({'operation': new_operation.to_dict(), 'user': new_user.to_dict()}), 201


@user_routes.route('/login', methods=['POST'])
def login():
    start_time = time.time()  # 记录操作开始时间

    # 获取请求中的表单数据
    username_or_email = request.form.get('username_or_email')
    password = request.form.get('password')

    # 创建一个新的操作记录
    new_operation = Operation(
        operation_type=OperationType.AUTHENTICATE,
        description="用户登录",
        ip_address=request.remote_addr,
        device_info=request.user_agent.string,
    )

    # 校验必填字段
    if not username_or_email or not password:
        failure_message = "【登录失败】用户名或邮箱和密码是必填项"
        return handle_operation_failure(new_operation, start_time, failure_message)

    # 根据用户名或邮箱查找用户
    user = User.query.filter((User.username == username_or_email) | (User.email == username_or_email)).first()

    # 检查用户是否存在
    if not user:
        failure_message = f"【登录失败】用户名或邮箱 {username_or_email} 不存在"
        return handle_operation_failure(new_operation, start_time, failure_message)

    # 验证密码
    if not check_password_hash(user.password, password):
        failure_message = f"【登录失败】用户名或邮箱 {username_or_email} 密码错误"
        return handle_operation_failure(new_operation, start_time, failure_message, user.user_id)

    # 更新用户的最后登录时间和状态
    user.last_login = datetime.now(ZoneInfo("Asia/Shanghai"))
    user.status = 'active'
    db.session.commit()

    # 创建 JWT 令牌
    access_token = create_access_token(identity=user.user_id)

    # 提交操作记录
    new_operation = handle_operation_success(new_operation, start_time, user.user_id)

    current_app.logger.info(f"【登录成功】user: {user}, JWT 令牌：{access_token}")
    return jsonify({'operation': new_operation.to_dict(), 'user': user.to_dict()}), 200


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

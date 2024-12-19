import os
import time
from datetime import datetime
from zoneinfo import ZoneInfo

from flask import request, current_app, jsonify
from flask_jwt_extended import create_access_token
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

from . import user_routes
from ..constants import OperationType, UserRole, OperationStatus
from ..models import db
from ..models.operation import Operation
from ..models.user import User
from ..utils import is_valid_phone, is_valid_email, is_valid_avatar_file
from ..utils.operation_util import handle_operation_failure


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
            return handle_operation_failure(message, new_operation, start_time)

    # 检查用户名和邮箱是否已经存在
    if User.query.filter_by(username=username).first() or User.query.filter_by(email=email).first():
        return handle_operation_failure(f"【注册失败】用户名 {username} 或邮箱 {email} 已注册", new_operation,
                                        start_time)

    # 加密密码
    hashed_password = generate_password_hash(password)

    # 头像存储处理
    avatar_path = handle_avatar_upload(avatar_file, new_operation, start_time)
    if avatar_path is None:
        return jsonify({'operation': new_operation.to_dict()}), 500

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

    try:
        # 先保存新用户
        db.session.add(new_user)
        db.session.commit()

        # 然后更新操作记录
        new_operation.duration = time.time() - start_time
        new_operation.status = OperationStatus.SUCCESS
        new_operation.owner_id = new_user.user_id
        db.session.add(new_operation)
        db.session.commit()

        current_app.logger.info(f"【注册成功】operation: {new_operation}, user: {new_user}")
        return jsonify({'operation': new_operation.to_dict(), 'user': new_user.to_dict()}), 201
    except Exception as e:
        failure_message = "【服务器错误】无法保存用户数据"

        # 更新操作记录
        new_operation.duration = time.time() - start_time
        new_operation.failure_message = failure_message
        new_operation.status = OperationStatus.FAILURE
        db.session.add(new_operation)
        db.session.commit()

        current_app.logger.error(f"operation: {new_operation}, error: {str(e)}")
        return jsonify({'operation': new_operation.to_dict()}), 500


@user_routes.route('/login', methods=['POST'])
def login():
    # 获取请求中的表单数据
    username_or_email = request.form.get('username_or_email')
    password = request.form.get('password')

    # 校验必填字段
    if not username_or_email or not password:
        current_app.logger.warning(f"登录失败：用户名、邮箱或密码为空：{request.form}")
        return jsonify({'message': '登录失败：用户名或邮箱和密码是必填项'}), 400

    try:
        # 根据用户名或邮箱查找用户
        user = User.query.filter((User.username == username_or_email) | (User.email == username_or_email)).first()

        # 用户不存在
        if not user:
            current_app.logger.warning(f"登录失败：用户 {username_or_email} 不存在")
            return jsonify({'message': '登录失败：用户不存在', 'username_or_email': username_or_email}), 400

        # 验证密码
        if not check_password_hash(user.password, password):
            current_app.logger.warning(f"登录失败：用户 {username_or_email} 密码错误")
            return jsonify({'message': '登录失败：密码错误', 'username_or_email': username_or_email}), 400

        # 更新用户的最后登录时间和状态
        user.last_login = datetime.now(ZoneInfo("Asia/Shanghai"))
        user.status = 'active'

        # 提交更新到数据库
        db.session.commit()

        # 创建 JWT 令牌
        access_token = create_access_token(identity=user.user_id)

        current_app.logger.info(f"用户 {username_or_email} 登录成功，生成了 JWT 令牌：{access_token}")

        user_data = {
            'id': user.user_id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'role': user.role,
            'avatar_path': user.avatar_path,
            'phone': user.phone,
            'last_login': user.last_login,
            'status': user.status,
            'created_at': user.created_at,
            'updated_at': user.updated_at,
        }

        return jsonify({'message': '登录成功', 'access_token': access_token, 'user': user_data}), 200
    except Exception as e:
        current_app.logger.error(f"登录失败，出现异常：{str(e)}")
        return jsonify({'message': '登录失败，请稍后重试'}), 500


def handle_avatar_upload(avatar_file, new_operation, start_time):
    try:
        if not avatar_file:
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
    except Exception as e:
        failure_message = "【服务器错误】头像上传失败"

        # 更新操作记录
        new_operation.duration = time.time() - start_time
        new_operation.failure_message = failure_message
        new_operation.status = OperationStatus.FAILURE
        db.session.add(new_operation)
        db.session.commit()

        current_app.logger.error(f"operation: {new_operation}, error: {str(e)}")
        return None  # 返回 None 表示头像上传失败

import time
from datetime import datetime
from zoneinfo import ZoneInfo

from flask import request, jsonify, current_app
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, create_refresh_token
from werkzeug.security import generate_password_hash, check_password_hash

from app.constants import OperationType, UserRole, UserStatus
from app.models import Operation, User, db
from app.routes import user_routes
from app.utils import is_valid_email, is_valid_avatar_file, is_valid_phone, handle_operation_failure, \
    handle_operation_success, handle_file_upload


@user_routes.route('/register', methods=['POST'])
def register():
    start_time = time.time()  # 记录操作开始时间

    # 获取请求中的表单数据
    username = request.form.get('username')
    email = request.form.get('email')
    password = request.form.get('password')
    first_name = request.form.get('first_name', '名字')
    last_name = request.form.get('last_name', '姓氏')
    role = request.form.get('role', 'user')
    avatar_file = request.files.get('avatar_file')
    phone = request.form.get('phone')

    # 创建一个新的操作记录
    new_operation = Operation(
        operation_type=OperationType.CREATE,
        description="用户注册",
        ip_address=request.remote_addr,
        device_info=request.user_agent.string,
    )

    # 根据用户名或邮箱查找用户
    user = User.query.filter((User.username == username) | (User.email == email)).first()

    # 校验字段
    validation_checks = [
        (not username or not email or not password, "【注册失败】用户名、邮箱或密码为空"),
        (user and user.status == UserStatus.BANNED, "【注册失败】该用户已被封禁"),
        (user and (user.status != UserStatus.DELETED or not user.deleted_at),
         f"【注册失败】该用户 {username}/{email} 已注册，请直接登录"),
        (not is_valid_email(email), f"【注册失败】无效的邮箱格式：{email}"),
        (role not in UserRole.list(), f"【注册失败】无效的角色：{role}，只限 'admin', 'developer', 'user'"),
        (avatar_file and not is_valid_avatar_file(avatar_file), "【注册失败】头像文件类型或大小不合规"),
        (phone and not is_valid_phone(phone), f"【注册失败】无效的手机号格式：{phone}")
    ]
    for condition, message in validation_checks:
        if condition:
            new_operation = handle_operation_failure(new_operation, start_time, message)
            return jsonify({'operation': new_operation.to_dict()}), 400

    if user:
        # 已软删除用户，直接更新信息
        if user.status == UserStatus.DELETED or user.deleted_at:
            user.username = username
            user.email = email
            user.password = generate_password_hash(password)
            user.first_name = first_name
            user.last_name = last_name
            user.role = role
            user.avatar_path = handle_file_upload(avatar_file, 'avatars')
            user.phone = phone
            user.status = UserStatus.INACTIVE
            user.deleted_at = None
    else:
        # 新用户，创建新记录
        user = User(
            username=username,
            email=email,
            password=generate_password_hash(password),
            first_name=first_name,
            last_name=last_name,
            role=role,
            avatar_path=handle_file_upload(avatar_file, 'avatars'),
            phone=phone,
        )
        db.session.add(user)

    db.session.commit()

    # 记录操作
    new_operation = handle_operation_success(new_operation, start_time, user.user_id)

    current_app.logger.info(f"【注册成功】user: {user}")
    return jsonify({'operation': new_operation.to_dict(), 'user': user.to_dict()}), 201


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

    # 根据用户名或邮箱查找用户
    user = User.query.filter((User.username == username_or_email) | (User.email == username_or_email)).first()

    # 校验字段
    validation_checks = [
        (not username_or_email or not password, "【登录失败】用户名或邮箱和密码是必填项"),
        (not user, f"【登录失败】该用户 {username_or_email} 尚未注册，请先注册"),
        (user and (user.status == UserStatus.DELETED or user.deleted_at),
         f"【登录失败】该用户 {username_or_email} 已注销"),
        (not check_password_hash(user.password, password), "【登录失败】密码错误")
    ]
    for condition, message in validation_checks:
        if condition:
            new_operation = handle_operation_failure(new_operation, start_time, message)
            return jsonify({'operation': new_operation.to_dict()}), 400

    # 更新用户的最后登录时间和状态
    user.last_login = datetime.now(ZoneInfo("Asia/Shanghai"))
    user.status = UserStatus.ACTIVE
    db.session.commit()

    # 根据 user_id 创建 JWT 令牌
    access_token = create_access_token(identity=user.user_id)
    refresh_token = create_refresh_token(identity=user.user_id)

    # 记录操作
    new_operation = handle_operation_success(new_operation, start_time, user.user_id)

    current_app.logger.info(f"【登录成功】user: {user}, access_token：{access_token}, refresh_token: {refresh_token}")
    return jsonify({'operation': new_operation.to_dict(), 'user': user.to_dict(), 'access_token': access_token,
                    'refresh_token': refresh_token}), 200


@user_routes.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    start_time = time.time()  # 记录操作开始时间

    # 创建一个新的操作记录
    new_operation = Operation(
        operation_type=OperationType.AUTHENTICATE,
        description="用户登出",
        ip_address=request.remote_addr,
        device_info=request.user_agent.string,
    )

    # 获取当前用户的身份（使用 access token）
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    if not current_user:
        failure_message = f"【登出失败】服务器数据异常，用户 ID: {current_user_id} 不存在"
        new_operation = handle_operation_failure(new_operation, start_time, failure_message)
        return jsonify({'operation': new_operation.to_dict()}), 400

    # 更新用户的最后登录时间和状态
    current_user.last_logout = datetime.now(ZoneInfo("Asia/Shanghai"))
    current_user.status = UserStatus.INACTIVE
    db.session.commit()

    # 记录操作
    new_operation = handle_operation_success(new_operation, start_time, current_user_id)

    current_app.logger.info(f"【登出成功】user: {current_user}")
    return jsonify({'operation': new_operation.to_dict(), 'user': current_user.to_dict()}), 200


@user_routes.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    start_time = time.time()  # 记录操作开始时间

    # 创建一个新的操作记录
    new_operation = Operation(
        operation_type=OperationType.AUTHENTICATE,
        description="刷新用户 token",
        ip_address=request.remote_addr,
        device_info=request.user_agent.string,
    )

    # 获取当前用户的身份（使用 refresh token）
    current_user_id = get_jwt_identity()

    # 生成新的 access token
    access_token = create_access_token(identity=current_user_id)

    # 记录操作
    new_operation = handle_operation_success(new_operation, start_time, current_user_id)

    current_app.logger.info(f"【刷新 token 成功】user_id: {current_user_id}, access_token：{access_token}")
    return jsonify({'operation': new_operation.to_dict(), 'access_token': access_token}), 200


@user_routes.route('/profile', methods=['GET'])
@jwt_required()
def profile():
    start_time = time.time()  # 记录操作开始时间

    # 创建一个新的操作记录
    new_operation = Operation(
        operation_type=OperationType.READ,
        description="获取用户资料",
        ip_address=request.remote_addr,
        device_info=request.user_agent.string,
    )

    # 获取当前用户的身份（使用 access token）
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    if not current_user:
        failure_message = f"【获取用户资料失败】服务器数据异常，用户 ID: {current_user_id} 不存在"
        new_operation = handle_operation_failure(new_operation, start_time, failure_message)
        return jsonify({'operation': new_operation.to_dict()}), 400

    # 记录操作
    new_operation = handle_operation_success(new_operation, start_time, current_user_id)

    current_app.logger.info(f"【获取用户资料成功】user: {current_user}")
    return jsonify({'operation': new_operation.to_dict(), 'user': current_user.to_dict()}), 200


@user_routes.route('/update_profile', methods=['PUT'])
@jwt_required()
def update_profile():
    start_time = time.time()  # 记录操作开始时间

    # 获取请求中的更新数据
    username = request.form.get('username')
    email = request.form.get('email')
    first_name = request.form.get('first_name')
    last_name = request.form.get('last_name')
    avatar_file = request.files.get('avatar_file')
    phone = request.form.get('phone')

    # 创建一个新的操作记录
    new_operation = Operation(
        operation_type=OperationType.UPDATE,
        description="更新用户资料",
        ip_address=request.remote_addr,
        device_info=request.user_agent.string,
    )

    # 获取当前用户的身份（使用 access token）
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)

    # 校验字段
    validation_checks = [
        (not current_user, f"【更新用户资料失败】服务器数据异常，用户 ID: {current_user_id} 不存在"),
        (not username or not email, "【更新用户资料失败】用户名或邮箱为空"),
        (not is_valid_email(email), f"【更新用户资料失败】无效的邮箱格式：{email}"),
        (avatar_file and not is_valid_avatar_file(avatar_file), "【更新用户资料失败】头像文件类型或大小不合规"),
        (phone and not is_valid_phone(phone), f"【更新用户资料失败】无效的手机号格式：{phone}"),
        (User.query.filter_by(username=username).first() or User.query.filter_by(email=email).first(),
         f"【更新用户资料失败】用户 {username}/{email} 已存在")
    ]
    for condition, message in validation_checks:
        if condition:
            new_operation = handle_operation_failure(new_operation, start_time, message)
            return jsonify({'operation': new_operation.to_dict(), 'user': current_user.to_dict()}), 400

    # 更新用户信息
    current_user.username = username
    current_user.email = email
    current_user.first_name = first_name
    current_user.last_name = last_name
    current_user.avatar_path = handle_file_upload(avatar_file, 'avatars')
    current_user.phone = phone
    db.session.commit()

    # 记录操作
    new_operation = handle_operation_success(new_operation, start_time, current_user_id)

    current_app.logger.info(f"【更新用户资料成功】user: {current_user}")
    return jsonify({'operation': new_operation.to_dict(), 'user': current_user.to_dict()}), 200


@user_routes.route('/change_password', methods=['PUT'])
@jwt_required()
def change_password():
    start_time = time.time()  # 记录操作开始时间

    # 获取请求中的当前密码和新密码
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')

    # 创建一个新的操作记录
    new_operation = Operation(
        operation_type=OperationType.UPDATE,
        description="修改密码",
        ip_address=request.remote_addr,
        device_info=request.user_agent.string,
    )

    # 获取当前用户的身份（使用 access token）
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)

    # 校验字段
    validation_checks = [
        (not current_user, f"【修改密码失败】服务器数据异常，用户 ID: {current_user_id} 不存在"),
        (not current_password or not new_password, "【修改密码失败】当前密码或新密码为空"),
        (not check_password_hash(current_user.password, current_password), "【修改密码失败】当前密码错误")
    ]
    for condition, message in validation_checks:
        if condition:
            new_operation = handle_operation_failure(new_operation, start_time, message)
            return jsonify({'operation': new_operation.to_dict(), 'user': current_user.to_dict()}), 400

    # 更新密码
    current_user.password = generate_password_hash(new_password)
    db.session.commit()

    # 记录操作
    new_operation = handle_operation_success(new_operation, start_time, current_user_id)

    current_app.logger.info(f"【修改密码成功】user: {current_user}")
    return jsonify(
        {'operation': new_operation.to_dict(), 'user': current_user.to_dict(), "old_password": current_password}), 200


@user_routes.route('/delete_account', methods=['DELETE'])
@jwt_required()
def delete_account():
    start_time = time.time()  # 记录操作开始时间

    # 创建一个新的操作记录
    new_operation = Operation(
        operation_type=OperationType.DELETE,
        description="删除账户",
        ip_address=request.remote_addr,
        device_info=request.user_agent.string,
    )

    # 获取当前用户的身份（使用 access token）
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    if not current_user:
        failure_message = f"【删除账户失败】服务器数据异常，用户 ID: {current_user_id} 不存在"
        new_operation = handle_operation_failure(new_operation, start_time, failure_message)
        return jsonify({'operation': new_operation.to_dict()}), 400

    # 软删除用户
    current_user.deleted_at = datetime.now(ZoneInfo("Asia/Shanghai"))
    current_user.status = UserStatus.DELETED
    db.session.commit()

    # 记录操作
    new_operation = handle_operation_success(new_operation, start_time, current_user_id)

    current_app.logger.info(f"【删除账户成功】user: {current_user}")
    return jsonify({'operation': new_operation.to_dict(), 'user': current_user.to_dict()}), 200

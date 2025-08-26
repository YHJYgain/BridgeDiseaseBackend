import random
import time
from datetime import datetime
from zoneinfo import ZoneInfo

from flask import request, jsonify, current_app
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, create_refresh_token
from werkzeug.security import generate_password_hash, check_password_hash

from app.constants import OperationType, UserRole, UserStatus
from app.decorators import login_required
from app.models import Operation, User, db
from app.routes import user_routes
from app.utils import is_valid_email, is_valid_avatar_file, is_valid_phone, handle_operation_failure, \
    handle_operation_success, handle_file_upload, get_pagination_params, adjust_page_if_needed, rate_limit, \
    user_rate_limit


@user_routes.route('/register', methods=['POST'])
def register():
    start_time = time.time()  # 记录操作开始时间

    # 获取请求中的表单数据
    username = request.form.get('username')
    email = request.form.get('email')
    password = request.form.get('password')
    first_name = request.form.get('first_name', '名字')
    last_name = request.form.get('last_name', '姓氏')
    role = request.form.get('role', 'user').lower()
    avatar_file = request.files.get('avatar_file')
    phone = request.form.get('phone')

    # 创建一个新的操作记录
    new_operation = Operation(
        operation_type=OperationType.CREATE,
        description="用户注册",
        ip_address=request.remote_addr,
        device_info=request.user_agent.string,
    )

    # 根据用户名、邮箱、手机号查找用户（因为这三个字段具有唯一性）
    user = User.query.filter((User.username == username) | (User.email == email) | (User.phone == phone)).first()

    # 校验字段
    validation_checks = [
        (not username or not email or not password, "【注册失败】用户名、邮箱或密码为空", 400),
        (user and user.status == UserStatus.BANNED,
         f"【注册失败】您的账号已被封禁，如有疑问请联系管理员/开发人员", 403),
        (user and (user.status == UserStatus.DELETED or user.deleted_at),
         f"【注册失败】您的账号已注销，若要重新注册请联系管理员/开发人员", 403),
        (user and (user.status != UserStatus.DELETED or not user.deleted_at), f"【注册失败】您已注册过，请直接登录", 400),
        (not is_valid_email(email), f"【注册失败】无效的邮箱格式：{email}", 400),
        (role not in UserRole.list(), f"【注册失败】无效的角色：{role}，只限 'admin', 'developer', 'user'", 400),
        (avatar_file and not is_valid_avatar_file(avatar_file), "【注册失败】头像文件不合规", 400),
        (phone and not is_valid_phone(phone), f"【注册失败】无效的手机号格式：{phone}", 400),
    ]
    for condition, message, code in validation_checks:
        if condition:
            new_operation = handle_operation_failure(new_operation, start_time, message)
            current_app.logger.warning(message)
            return jsonify({
                'operation': new_operation.to_dict(),
            }), code

    # 新用户，创建新记录
    user = User(
        username=username,
        email=email,
        password=generate_password_hash(password),
        first_name=first_name,
        last_name=last_name,
        role=UserRole(role),
        avatar_path=handle_file_upload(avatar_file, 'avatars'),
        phone=phone,
    )
    db.session.add(user)
    db.session.commit()

    # 记录操作
    new_operation = handle_operation_success(new_operation, start_time, user.user_id)

    current_app.logger.info(f"【注册成功】new_user: {user}")
    return jsonify({
        'operation': new_operation.to_dict(),
        'new_user': user.to_dict(),
    }), 201


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
    user_id = user.user_id if user is not None else None

    # 校验字段
    validation_checks = [
        (not username_or_email or not password, "【登录失败】用户名或邮箱和密码是必填项", 400),
        (not user, f"【登录失败】用户 {username_or_email} 尚未注册，请先注册", 400),
        (user and user.status == UserStatus.BANNED, f"【登录失败】您已被封禁，如有疑问请联系管理员/开发人员", 403),
        (user and (user.status == UserStatus.DELETED or user.deleted_at),
         f"【登录失败】您的账号已注销，若需重新注册请联系管理员/开发人员", 403),
        (user and not check_password_hash(user.password, password), "【登录失败】密码错误", 400),
    ]
    for condition, message, code in validation_checks:
        if condition:
            new_operation = handle_operation_failure(new_operation, start_time, message, user_id)
            current_app.logger.warning(message)
            return jsonify({
                'operation': new_operation.to_dict(),
            }), code

    # 更新用户的最后登录时间和状态
    user.last_login = datetime.now(ZoneInfo("Asia/Shanghai"))
    user.status = UserStatus.ACTIVE
    db.session.commit()

    # 根据 user_id 创建 JWT 令牌
    access_token = create_access_token(identity=user.user_id)
    refresh_token = create_refresh_token(identity=user.user_id)

    # 记录操作
    new_operation = handle_operation_success(new_operation, start_time, user.user_id)

    current_app.logger.info(
        f"【登录成功】login_user: {user}, access_token: {access_token}, refresh_token: {refresh_token}")
    return jsonify({
        'operation': new_operation.to_dict(),
        'login_user': user.to_dict(),
        'access_token': access_token,
        'refresh_token': refresh_token,
    }), 200


@user_routes.route('/logout', methods=['POST'])
@jwt_required()
@login_required
def logout():
    start_time = time.time()  # 记录操作开始时间

    # 创建一个新的操作记录
    new_operation = Operation(
        operation_type=OperationType.AUTHENTICATE,
        description="用户登出",
        ip_address=request.remote_addr,
        device_info=request.user_agent.string,
    )

    # 获取当前用户身份（使用 access token）
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)

    # 更新用户的最后登录时间和状态
    current_user.last_login = datetime.now(ZoneInfo("Asia/Shanghai"))
    current_user.status = UserStatus.INACTIVE
    db.session.commit()

    # 记录操作
    new_operation = handle_operation_success(new_operation, start_time, current_user_id)

    current_app.logger.info(f"【登出成功】logout_user: {current_user}")
    return jsonify({
        'operation': new_operation.to_dict(),
        'logout_user': current_user.to_dict(),
    }), 200


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

    # 获取当前用户身份（使用 refresh token）
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)

    # 生成新的 access token
    access_token = create_access_token(identity=current_user_id)

    # 记录操作
    new_operation = handle_operation_success(new_operation, start_time, current_user_id)

    current_app.logger.info(f"【刷新 token 成功】current_user: {current_user}, access_token: {access_token}")
    return jsonify({
        'operation': new_operation.to_dict(),
        'access_token': access_token,
    }), 200


@user_routes.route('/profile', methods=['GET'])
@jwt_required()
@login_required
def profile():
    # 获取当前用户身份（使用 access token）
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)

    return jsonify({
        'current_user': current_user.to_dict(),
    }), 200


@user_routes.route('/detail/<int:user_id>', methods=['GET'])
@jwt_required()
@login_required
def detail(user_id):
    # 获取当前用户身份（使用 access token）
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)

    # 获取指定用户
    user = User.query.get(user_id)

    # 校验字段
    validation_checks = [
        (not user, f"【获取用户 ID={user_id} 详情失败】该用户不存在", 404),
        (user and user.user_id != current_user_id and current_user.role != UserRole.ADMIN
         and current_user.role != UserRole.DEVELOPER,
         f"【获取用户 ID={user_id} 详情失败】当前登录用户非管理员/开发人员，无权查看其他用户信息", 403),
    ]
    for condition, message, code in validation_checks:
        if condition:
            current_app.logger.warning(message + f', operator: {current_user}')
            return jsonify({
                'failure_message': message,
            }), code

    return jsonify({
        'user': user.to_dict(),
    }), 200


@user_routes.route('/update', methods=['PUT'])
@jwt_required()
@login_required
def update():
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

    # 获取当前用户身份（使用 access token）
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)

    # 校验字段
    validation_checks = [
        (not username or not email, "【更新用户资料失败】用户名或邮箱为空", 400),
        (not is_valid_email(email), f"【更新用户资料失败】无效的邮箱格式：{email}", 400),
        (avatar_file and not is_valid_avatar_file(avatar_file), "【更新用户资料失败】头像文件类型或大小不合规", 400),
        (phone and not is_valid_phone(phone), f"【更新用户资料失败】无效的手机号格式：{phone}", 400),
        (current_user.username != username and User.query.filter_by(username=username).first(),
         f"【更新用户资料失败】用户名 {username} 已注册过", 400),
        (current_user.email != email and User.query.filter_by(email=email).first(),
         f"【更新用户资料失败】邮箱 {email} 已注册过", 400),
        (phone and current_user.phone != phone and User.query.filter_by(phone=phone).first(),
         f"【更新用户资料失败】手机号 {phone} 已注册过", 400),
    ]
    for condition, message, code in validation_checks:
        if condition:
            new_operation = handle_operation_failure(new_operation, start_time, message, current_user_id)
            current_app.logger.warning(message + f', operator: {current_user}')
            return jsonify({
                'operation': new_operation.to_dict(),
            }), code

    # 更新用户信息
    current_user.username = username
    current_user.email = email
    current_user.first_name = first_name if first_name else current_user.first_name
    current_user.last_name = last_name if last_name else current_user.last_name
    if avatar_file:  # 如果有头像文件，则上传并更新头像路径；如果没有，则说明用户不需要更新头像
        current_user.avatar_path = handle_file_upload(avatar_file, 'avatars')
    current_user.phone = phone if phone else current_user.phone
    db.session.commit()

    # 记录操作
    new_operation = handle_operation_success(new_operation, start_time, current_user_id)

    current_app.logger.info(f"【更新用户资料成功】updated_user: {current_user}")
    return jsonify({
        'operation': new_operation.to_dict(),
        'updated_user': current_user.to_dict(),
    }), 200


@user_routes.route('/update/<int:user_id>', methods=['PUT'])
@jwt_required()
@login_required
def update_user(user_id):
    start_time = time.time()  # 记录操作开始时间

    # 获取请求中的更新数据
    username = request.form.get('username')
    email = request.form.get('email')
    password = request.form.get('password')
    first_name = request.form.get('first_name')
    last_name = request.form.get('last_name')
    role = request.form.get('role').lower()
    avatar_file = request.files.get('avatar_file')
    phone = request.form.get('phone')

    # 创建一个新的操作记录
    new_operation = Operation(
        operation_type=OperationType.UPDATE,
        description=f"更新用户 ID={user_id} 资料",
        ip_address=request.remote_addr,
        device_info=request.user_agent.string,
    )

    # 获取当前用户身份（使用 access token）
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)

    # 获取指定用户
    updated_user = User.query.get(user_id)

    # 校验字段
    validation_checks = [
        (current_user.role != UserRole.ADMIN and current_user.role != UserRole.DEVELOPER,
         f"【更新用户 ID={user_id} 资料失败】您非管理员/开发人员，无权修改其他用户信息", 403),
        (not username or not email or not role, f"【更新用户 ID={user_id} 资料失败】用户名、邮箱或角色为空", 400),
        (not is_valid_email(email), f"【更新用户 ID={user_id} 资料失败】无效的邮箱格式：{email}", 400),
        (avatar_file and not is_valid_avatar_file(avatar_file),
         f"【更新用户 ID={user_id} 资料失败】头像文件类型或大小不合规", 400),
        (phone and not is_valid_phone(phone), f"【更新用户 ID={user_id} 资料失败】无效的手机号格式：{phone}", 400),
        (not updated_user, f"【更新用户 ID={user_id} 资料失败】该用户不存在", 404),
        (updated_user.username != username and User.query.filter_by(username=username).first(),
         f"【更新用户 ID={user_id} 资料失败】用户名 {username} 已注册过", 400),
        (updated_user.email != email and User.query.filter_by(email=email).first(),
         f"【更新用户 ID={user_id} 资料失败】邮箱 {email} 已注册过", 400),
        (phone and updated_user.phone != phone and User.query.filter_by(phone=phone).first(),
         f"【更新用户 ID={user_id} 资料失败】手机号 {phone} 已注册过", 400),
    ]
    for condition, message, code in validation_checks:
        if condition:
            new_operation = handle_operation_failure(new_operation, start_time, message, current_user_id)
            current_app.logger.warning(message + f', operator: {current_user}')
            return jsonify({
                'operation': new_operation.to_dict(),
            }), code

    # 更新用户信息
    updated_user.username = username
    updated_user.email = email
    if password:  # 如果有密码，则更新密码；如果没有，则说明用户不需要更新密码
        updated_user.password = generate_password_hash(password)
    updated_user.first_name = first_name if first_name else updated_user.first_name
    updated_user.last_name = last_name if last_name else updated_user.last_name
    updated_user.role = UserRole(role)
    if avatar_file:  # 如果有头像文件，则上传并更新头像路径；如果没有，则说明用户不需要更新头像
        updated_user.avatar_path = handle_file_upload(avatar_file, 'avatars')
    updated_user.phone = phone if phone else updated_user.phone
    db.session.commit()

    # 记录操作
    new_operation = handle_operation_success(new_operation, start_time, current_user_id)

    current_app.logger.info(f"【更新用户 ID={user_id} 资料成功】updated_user: {updated_user}, operator: {current_user}")
    return jsonify({
        'operation': new_operation.to_dict(),
        'updated_user': updated_user.to_dict(),
    }), 200


@user_routes.route('/change_password', methods=['PUT'])
@jwt_required()
@login_required
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

    # 获取当前用户身份（使用 access token）
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)

    # 校验字段
    validation_checks = [
        (not current_password or not new_password, "【修改密码失败】当前密码或新密码为空", 400),
        (not check_password_hash(current_user.password, current_password), "【修改密码失败】当前密码错误", 400),
    ]
    for condition, message, code in validation_checks:
        if condition:
            new_operation = handle_operation_failure(new_operation, start_time, message, current_user_id)
            current_app.logger.warning(message + f', operator: {current_user}')
            return jsonify({
                'operation': new_operation.to_dict(),
            }), code

    # 更新密码
    current_user.password = generate_password_hash(new_password)
    db.session.commit()

    # 记录操作
    new_operation = handle_operation_success(new_operation, start_time, current_user_id)

    current_app.logger.info(f"【修改密码成功】current_user: {current_user}, old_password: {current_password}")
    return jsonify({
        'operation': new_operation.to_dict(),
        'current_user': current_user.to_dict(),
        "old_password": current_password,
    }), 200


@user_routes.route('/delete', methods=['DELETE'])
@jwt_required()
@login_required
def delete():
    start_time = time.time()  # 记录操作开始时间

    # 创建一个新的操作记录
    new_operation = Operation(
        operation_type=OperationType.DELETE,
        description="注销账户",
        ip_address=request.remote_addr,
        device_info=request.user_agent.string,
    )

    # 获取当前用户身份（使用 access token）
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)

    # 软删除用户
    current_user.deleted_at = datetime.now(ZoneInfo("Asia/Shanghai"))
    current_user.status = UserStatus.DELETED
    db.session.commit()

    # 记录操作
    new_operation = handle_operation_success(new_operation, start_time, current_user_id)

    current_app.logger.info(f"【注销账户成功】deleted_user: {current_user}")
    return jsonify({
        'operation': new_operation.to_dict(),
        'deleted_user': current_user.to_dict(),
    }), 200


@user_routes.route('/delete/<int:user_id>', methods=['DELETE'])
@jwt_required()
@login_required
def delete_user(user_id):
    start_time = time.time()  # 记录操作开始时间

    # 创建一个新的操作记录
    new_operation = Operation(
        operation_type=OperationType.DELETE,
        description=f"注销用户 ID={user_id}",
        ip_address=request.remote_addr,
        device_info=request.user_agent.string,
    )

    # 获取当前用户身份（使用 access token）
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)

    # 获取指定用户
    deleted_user = User.query.get(user_id)

    # 校验字段
    validation_checks = [
        (current_user.role != UserRole.ADMIN and current_user.role != UserRole.DEVELOPER,
         f"【注销用户 ID={user_id} 失败】您非管理员/开发人员，无权注销其他用户", 403),
        (not deleted_user, f"【注销用户 ID={user_id} 失败】该用户不存在", 404),
        (current_user.role != UserRole.DEVELOPER and (deleted_user.role == UserRole.ADMIN
                                                      or deleted_user.role == UserRole.DEVELOPER),
         f"【注销用户 ID={user_id} 失败】您非开发人员，无权注销管理员/开发人员", 400),
        (deleted_user.status == UserStatus.DELETED or deleted_user.deleted_at,
         f"【注销用户 ID={user_id} 失败】该用户已注销", 400),
    ]
    for condition, message, code in validation_checks:
        if condition:
            new_operation = handle_operation_failure(new_operation, start_time, message, current_user_id)
            current_app.logger.warning(message + f', operator: {current_user}')
            return jsonify({
                'operation': new_operation.to_dict(),
            }), code

    # 软删除用户
    deleted_user.deleted_at = datetime.now(ZoneInfo("Asia/Shanghai"))
    deleted_user.status = UserStatus.DELETED
    db.session.commit()

    # 记录操作
    new_operation = handle_operation_success(new_operation, start_time, current_user_id)

    current_app.logger.info(f"【注销用户 ID={user_id} 成功】deleted_user: {deleted_user}, operator: {current_user}")
    return jsonify({
        'operation': new_operation.to_dict(),
        'deleted_user': deleted_user.to_dict(),
    }), 200


@user_routes.route('/undelete/<int:user_id>', methods=['PUT'])
@jwt_required()
@login_required
def undelete_user(user_id):
    start_time = time.time()  # 记录操作开始时间

    # 创建一个新的操作记录
    new_operation = Operation(
        operation_type=OperationType.DELETE,
        description=f"恢复注销用户 ID={user_id}",
        ip_address=request.remote_addr,
        device_info=request.user_agent.string,
    )

    # 获取当前用户身份（使用 access token）
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)

    # 获取指定用户
    undeleted_user = User.query.get(user_id)

    # 校验字段
    validation_checks = [
        (current_user.role != UserRole.ADMIN and current_user.role != UserRole.DEVELOPER,
         f"【恢复注销用户 ID={user_id} 失败】您非管理员/开发人员，无权恢复注销其他用户", 403),
        (not undeleted_user, f"【恢复注销用户 ID={user_id} 失败】该用户不存在", 404),
        (current_user.role != UserRole.DEVELOPER and (undeleted_user.role == UserRole.ADMIN
                                                      or undeleted_user.role == UserRole.DEVELOPER),
         f"【恢复注销用户 ID={user_id} 失败】您非开发人员，无权恢复注销管理员/开发人员", 400),
        (undeleted_user.status != UserStatus.DELETED or not undeleted_user.deleted_at,
         f"【恢复注销用户 ID={user_id} 失败】该用户未注销", 400),
    ]
    for condition, message, code in validation_checks:
        if condition:
            new_operation = handle_operation_failure(new_operation, start_time, message, current_user_id)
            current_app.logger.warning(message + f', operator: {current_user}')
            return jsonify({
                'operation': new_operation.to_dict(),
            }), code

    # 恢复注销用户
    undeleted_user.deleted_at = None
    undeleted_user.status = UserStatus.INACTIVE
    db.session.commit()

    # 记录操作
    new_operation = handle_operation_success(new_operation, start_time, current_user_id)

    current_app.logger.info(
        f"【恢复注销用户 ID={user_id} 成功】undeleted_user: {undeleted_user}, operator: {current_user}")
    return jsonify({
        'operation': new_operation.to_dict(),
        'undeleted_user': undeleted_user.to_dict(),
    }), 200


@user_routes.route('/ban/<int:user_id>', methods=['PUT'])
@jwt_required()
@login_required
def ban(user_id):
    start_time = time.time()  # 记录操作开始时间

    # 创建一个新的操作记录
    new_operation = Operation(
        operation_type=OperationType.UPDATE,
        description=f"封禁用户 ID={user_id}",
        ip_address=request.remote_addr,
        device_info=request.user_agent.string,
    )

    # 获取当前用户身份（使用 access token）
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)

    # 获取指定用户
    baned_user = User.query.get(user_id)

    # 校验字段
    validation_checks = [
        (current_user.role != UserRole.ADMIN and current_user.role != UserRole.DEVELOPER,
         f"【封禁用户 ID={user_id} 失败】您非管理员/开发人员，无权封禁其他用户", 403),
        (not baned_user, f"【封禁用户 ID={user_id} 失败】该用户不存在", 404),
        (current_user.role != UserRole.DEVELOPER and (baned_user.role == UserRole.ADMIN
                                                      or baned_user.role == UserRole.DEVELOPER),
         f"【封禁用户 ID={user_id} 失败】您非开发人员，无权封禁管理员/开发人员", 400),
        (baned_user.status == UserStatus.BANNED, f"【封禁用户 ID={user_id} 失败】该用户已被封禁", 400),
        (baned_user.status == UserStatus.DELETED, f"【封禁用户 ID={user_id} 失败】该用户已注销", 400),
    ]
    for condition, message, code in validation_checks:
        if condition:
            new_operation = handle_operation_failure(new_operation, start_time, message, current_user_id)
            current_app.logger.warning(message + f', operator: {current_user}')
            return jsonify({
                'operation': new_operation.to_dict(),
            }), code

    # 封禁用户
    baned_user.status = UserStatus.BANNED
    db.session.commit()

    # 记录操作
    new_operation = handle_operation_success(new_operation, start_time, current_user_id)

    current_app.logger.info(f"【封禁用户 ID={user_id} 成功】baned_user: {baned_user}, operator: {current_user}")
    return jsonify({
        'operation': new_operation.to_dict(),
        'baned_user': baned_user.to_dict(),
    }), 200


@user_routes.route('/unban/<int:user_id>', methods=['PUT'])
@jwt_required()
@login_required
def unban(user_id):
    start_time = time.time()  # 记录操作开始时间

    # 创建一个新的操作记录
    new_operation = Operation(
        operation_type=OperationType.UPDATE,
        description=f"解封用户 ID={user_id}",
        ip_address=request.remote_addr,
        device_info=request.user_agent.string,
    )

    # 获取当前用户身份（使用 access token）
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)

    # 获取指定用户
    unbaned_user = User.query.get(user_id)

    # 校验字段
    validation_checks = [
        (current_user.role != UserRole.ADMIN and current_user.role != UserRole.DEVELOPER,
         f"【解封用户 ID={user_id} 失败】您非管理员/开发人员，无权解封其他用户", 403),
        (not unbaned_user, f"【解封用户 ID={user_id} 失败】该用户不存在", 404),
        (current_user.role != UserRole.DEVELOPER and (unbaned_user.role == UserRole.ADMIN
                                                      or unbaned_user.role == UserRole.DEVELOPER),
         f"【解封用户 ID={user_id} 失败】您非开发人员，无权解封管理员/开发人员", 400),
        (unbaned_user.status != UserStatus.BANNED, f"【解封用户 ID={user_id} 失败】该用户未被封禁", 400),
        (unbaned_user.status == UserStatus.DELETED, f"【解封用户 ID={user_id} 失败】该用户已注销", 400),
    ]
    for condition, message, code in validation_checks:
        if condition:
            new_operation = handle_operation_failure(new_operation, start_time, message, current_user_id)
            current_app.logger.warning(message + f', operator: {current_user}')
            return jsonify({
                'operation': new_operation.to_dict(),
            }), code

    # 解封用户
    unbaned_user.status = UserStatus.INACTIVE
    db.session.commit()

    # 记录操作
    new_operation = handle_operation_success(new_operation, start_time, current_user_id)

    current_app.logger.info(f"【解封用户 ID={user_id} 成功】unbaned_user: {unbaned_user}, operator: {current_user}")
    return jsonify({
        'operation': new_operation.to_dict(),
        'unbaned_user': unbaned_user.to_dict(),
    }), 200


@user_routes.route('/users/all', methods=['GET'])
@jwt_required()
@login_required
def all_users():
    # 获取分页参数（从请求中获取，默认为第 1 页，每页 5 条记录）
    default_page = request.args.get('page', 1, type=int)
    default_per_page = request.args.get('per_page', 5, type=int)
    page, per_page = get_pagination_params(default_page, default_per_page)

    # 获取当前用户身份（使用 access token）
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)

    if current_user.role != UserRole.ADMIN and current_user.role != UserRole.DEVELOPER:
        failure_message = f"【获取所有用户失败】您非管理员/开发人员，权限不足"
        current_app.logger.warning(failure_message + f', operator: {current_user}')
        return jsonify({
            'failure_message': failure_message,
        }), 403

    # 查询所有用户
    query = User.query
    page, users_total, pages = adjust_page_if_needed(query, page, per_page)
    users = query.paginate(page=page, per_page=per_page, error_out=False)

    current_app.logger.info(
        f"【获取所有用户成功】total: {users_total}, per_page: {per_page}, page: {page}, pages: {pages}, users: {[user for user in users]}, operator: {current_user}")
    return jsonify({
        'users': [user.to_dict() for user in users],
        'total': users_total,
        'per_page': per_page,
        'page': page,
        'pages': pages,
    }), 200


@user_routes.route('/admin_info', methods=['GET'])
def get_admin_info():
    # 查询所有管理员用户
    admins = User.query.filter(User.role == UserRole.ADMIN, User.status != UserStatus.BANNED,
                               User.status != UserStatus.DELETED).all()

    # 如果没有管理员，返回 None
    if not admins:
        return jsonify({
            'admin_info': None,
        }), 200

    # 随机选择一个管理员
    random_admin = random.choice(admins)

    # 提取管理员的基本信息（只包含必要的联系信息）
    admin_info = {
        'username': random_admin.username,
        'email': random_admin.email,
        'phone': random_admin.phone,
        'role': random_admin.role.name,
        'first_name': random_admin.first_name,
        'last_name': random_admin.last_name,
    }

    # 将单个管理员信息放入列表中返回，保持 API 兼容性
    return jsonify({
        'admin_info': admin_info,
    }), 200


@user_routes.route('/developer_info', methods=['GET'])
def get_developer_info():
    # 查询所有开发人员用户
    developers = User.query.filter(User.role == UserRole.DEVELOPER, User.status != UserStatus.BANNED,
                                   User.status != UserStatus.DELETED).all()

    # 如果没有开发人员，返回 None
    if not developers:
        return jsonify({
            'developer_info': None,
        }), 200

    # 随机选择一个开发人员
    random_developer = random.choice(developers)

    # 提取开发人员的基本信息（只包含必要的联系信息）
    developer_info = {
        'username': random_developer.username,
        'email': random_developer.email,
        'phone': random_developer.phone,
        'role': random_developer.role.name,
        'first_name': random_developer.first_name,
        'last_name': random_developer.last_name,
    }

    # 将单个开发人员信息放入列表中返回，保持 API 兼容性
    return jsonify({
        'developer_info': developer_info,
    }), 200


@user_routes.route('/statistics', methods=['GET'])
@jwt_required()
@login_required
def statistics():
    # 查询用户总数（不包括软删除的用户）
    total_users = User.query.filter(User.status != UserStatus.DELETED).count()

    # 查询不同角色的用户数量（不包括软删除的用户）
    admin_users = User.query.filter(User.role == UserRole.ADMIN, User.status != UserStatus.DELETED).count()
    developer_users = User.query.filter(User.role == UserRole.DEVELOPER, User.status != UserStatus.DELETED).count()
    normal_users = User.query.filter(User.role == UserRole.USER, User.status != UserStatus.DELETED).count()

    # 构建统计数据
    users_statistics = {
        'total': total_users,
        'admin': admin_users,
        'developer': developer_users,
        'user': normal_users,
    }

    return jsonify({
        "users_statistics": users_statistics,
    }), 200

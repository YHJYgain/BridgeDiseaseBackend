import time
from functools import wraps

from flask import jsonify, request, current_app
from flask_jwt_extended import get_jwt_identity

from app.constants import UserRole, OperationType
from app.models import User, Operation
from app.utils import handle_operation_failure


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        start_time = time.time()  # 记录操作开始时间

        # 创建一个新的操作记录
        new_operation = Operation(
            operation_type=OperationType.AUTHENTICATE,
            description="登录用户验证",
            ip_address=request.remote_addr,
            device_info=request.user_agent.string,
        )

        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        if not current_user:
            failure_message = f"【登录用户验证失败】服务器数据异常，用户 ID: {current_user_id} 不存在"
            new_operation = handle_operation_failure(new_operation, start_time, failure_message)
            current_app.logger.error(failure_message)
            return jsonify({'operation': new_operation.to_dict()}), 404
        return f(*args, **kwargs)

    return decorated_function


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        start_time = time.time()  # 记录操作开始时间

        # 创建一个新的操作记录
        new_operation = Operation(
            operation_type=OperationType.AUTHENTICATE,
            description="权限验证",
            ip_address=request.remote_addr,
            device_info=request.user_agent.string,
        )

        # 获取当前用户的身份（使用 access token）
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        if current_user.role != UserRole.ADMIN:
            failure_message = f"【权限验证失败】当前登录用户非管理员，权限不足"
            new_operation = handle_operation_failure(new_operation, start_time, failure_message, current_user_id)
            current_app.logger.error(failure_message)
            return jsonify({'operation': new_operation.to_dict()}), 401
        return f(*args, **kwargs)

    return decorated_function

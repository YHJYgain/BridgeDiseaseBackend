import time

from flask import request, current_app, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.constants import OperationType
from app.decorators import admin_required, login_required
from app.models import Operation, User
from app.routes import operation_routes
from app.utils import handle_operation_success, handle_operation_failure


@operation_routes.route('/operations', methods=['GET'])
@jwt_required()
@login_required
def current_user_operations():
    start_time = time.time()  # 记录操作开始时间

    # 创建一个新的操作记录
    new_operation = Operation(
        operation_type=OperationType.READ,
        description="获取当前用户操作记录",
        ip_address=request.remote_addr,
        device_info=request.user_agent.string,
    )

    # 获取当前用户的身份（使用 access token）
    current_user_id = get_jwt_identity()

    # 获取当前用户的操作日志
    operations = Operation.query.filter_by(owner_id=current_user_id).all()

    # 记录操作
    new_operation = handle_operation_success(new_operation, start_time, current_user_id)

    current_app.logger.info(f"【获取当前用户操作记录成功】operations: {operations}")
    return jsonify({
        'operation': new_operation.to_dict(),
        'operations': [operation.to_dict() for operation in operations]
    }), 200


@operation_routes.route('/operations/<int:user_id>', methods=['GET'])
@jwt_required()
@login_required
@admin_required
def user_operations(user_id):
    start_time = time.time()  # 记录操作开始时间

    # 创建一个新的操作记录
    new_operation = Operation(
        operation_type=OperationType.READ,
        description=f"获取用户 ID={user_id} 操作记录",
        ip_address=request.remote_addr,
        device_info=request.user_agent.string,
    )

    # 获取当前用户的身份（使用 access token）
    current_user_id = get_jwt_identity()

    # 获取指定用户
    user = User.query.get(user_id)
    if not user:
        failure_message = f"【获取用户 ID={user_id} 操作记录失败】服务器数据异常，用户不存在"
        new_operation = handle_operation_failure(new_operation, start_time, failure_message, current_user_id)
        current_app.logger.error(failure_message)
        return jsonify({'operation': new_operation.to_dict()}), 404

    # 获取指定用户的操作日志
    operations = Operation.query.filter_by(owner_id=user_id).all()

    # 记录操作
    new_operation = handle_operation_success(new_operation, start_time, user_id)

    current_app.logger.info(f"【获取用户 ID={user_id} 操作记录成功】operations: {operations}")
    return jsonify({
        'operation': new_operation.to_dict(),
        'operations': [operation.to_dict() for operation in operations]
    }), 200

import time

from flask import request, current_app, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.constants import OperationType
from app.models import Operation, User
from app.routes import operation_routes
from app.utils import handle_operation_success, handle_operation_failure


@operation_routes.route('/operations', methods=['GET'])
@jwt_required()
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
    current_user = User.query.get(current_user_id)
    if not current_user:
        failure_message = f"【获取当前用户操作记录】服务器数据异常，用户 ID: {current_user_id} 不存在"
        new_operation = handle_operation_failure(new_operation, start_time, failure_message)
        return jsonify({'operation': new_operation.to_dict()}), 400

    # 获取当前用户的操作日志
    operations = Operation.query.filter_by(owner_id=current_user_id).all()

    # 记录操作
    new_operation = handle_operation_success(new_operation, start_time, current_user_id)

    current_app.logger.info(f"【获取当前用户操作记录成功】current_user: {current_user}, operations: {operations}")
    return jsonify({'operation': new_operation.to_dict(), 'current_user': current_user.to_dict(),
                    'operations': [operation.to_dict() for operation in operations]}), 200

import time

from flask import request, current_app, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.constants import OperationType, UserRole
from app.decorators import login_required
from app.models import Operation, User
from app.routes import operation_routes
from app.utils import handle_operation_success, handle_operation_failure, adjust_page_if_needed, get_pagination_params


@operation_routes.route('/operations/<int:user_id>', methods=['GET'])
@jwt_required()
@login_required
def user_operations(user_id):
    start_time = time.time()  # 记录操作开始时间

    # 获取分页参数（默认为第 1 页，每页 5 条记录）
    page, per_page = get_pagination_params()

    # 创建一个新的操作记录
    new_operation = Operation(
        operation_type=OperationType.READ,
        description=f"获取用户 ID={user_id} 操作记录",
        ip_address=request.remote_addr,
        device_info=request.user_agent.string,
    )

    # 获取当前用户身份（使用 access token）
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)

    # 获取指定用户身份
    user = User.query.get(user_id)

    # 校验字段
    validation_checks = [
        (not user, f"【获取用户 ID={user_id} 操作记录失败】该用户不存在", 404),
        (current_user_id != user_id and current_user.role != UserRole.ADMIN and current_user.role != UserRole.DEVELOPER,
         f"【获取用户 ID={user_id} 操作记录失败】当前登录用户非管理员/开发人员，权限不足", 403),
    ]
    for condition, message, code in validation_checks:
        if condition:
            new_operation = handle_operation_failure(new_operation, start_time, message, current_user_id)
            current_app.logger.error(message)
            return jsonify({'operation': new_operation.to_dict()}), code

    # 获取指定用户操作日志
    query = Operation.query.filter_by(owner_id=user_id)
    page, operations_total, pages = adjust_page_if_needed(query, page, per_page)
    operations = query.paginate(page=page, per_page=per_page, error_out=False)

    # 记录操作
    new_operation = handle_operation_success(new_operation, start_time, current_user_id)

    current_app.logger.info(
        f"【获取用户 ID={user_id} 操作记录成功】total: {operations_total}, per_page: {per_page}, page: {page}, pages: {pages}, operations: {[operation.to_dict() for operation in operations]}")
    return jsonify({
        'operation': new_operation.to_dict(),
        'operations': [operation.to_dict() for operation in operations],
        'total': operations_total,
        'per_page': per_page,
        'page': page,
        'pages': pages,
    }), 200

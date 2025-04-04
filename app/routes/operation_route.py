from flask import request, current_app, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.constants import UserRole
from app.decorators import login_required
from app.models import Operation, User
from app.routes import operation_routes
from app.utils import adjust_page_if_needed, get_pagination_params


@operation_routes.route('/detail/<int:operation_id>', methods=['GET'])
@jwt_required()
@login_required
def detail(operation_id):
    # 获取当前用户身份（使用 access token）
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)

    # 获取指定操作
    operation = Operation.query.get(operation_id)

    # 校验字段
    validation_checks = [
        (not operation, f"【获取操作 ID={operation_id} 详情失败】该操作不存在", 404),
        (operation and operation.owner_id != current_user_id and current_user.role != UserRole.ADMIN
         and current_user.role != UserRole.DEVELOPER,
         f"【获取操作 ID={operation_id} 详情失败】当前登录用户非管理员/开发人员，权限不足", 403),
    ]
    for condition, message, code in validation_checks:
        if condition:
            current_app.logger.warning(message + f', operator: {current_user}')
            return jsonify({'failure_message': message}), code

    return jsonify({
        'operation': operation.to_dict(),
    }), 200

@operation_routes.route('/operations/<int:user_id>', methods=['GET'])
@jwt_required()
@login_required
def user_operations(user_id):
    # 获取分页参数（从请求中获取，默认为第 1 页，每页 5 条记录）
    default_page = request.args.get('page', 1, type=int)
    default_per_page = request.args.get('per_page', 5, type=int)
    page, per_page = get_pagination_params(default_page, default_per_page)

    # 获取当前用户身份（使用 access token）
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)

    # 获取指定用户身份
    user = User.query.get(user_id)

    # 校验字段
    validation_checks = [
        (not user, f"【获取用户 ID={user_id} 操作失败】该用户不存在", 404),
        (current_user_id != user_id and current_user.role != UserRole.ADMIN and current_user.role != UserRole.DEVELOPER,
         f"【获取用户 ID={user_id} 操作失败】当前登录用户非管理员/开发人员，权限不足", 403),
    ]
    for condition, message, code in validation_checks:
        if condition:
            current_app.logger.warning(message + f', operator: {current_user}')
            return jsonify({'failure_message': message}), code

    # 获取指定用户操作日志
    query = Operation.query.filter_by(owner_id=user_id)
    page, operations_total, pages = adjust_page_if_needed(query, page, per_page)
    operations = query.paginate(page=page, per_page=per_page, error_out=False)

    current_app.logger.info(
        f"【获取用户 ID={user_id} 操作成功】total: {operations_total}, per_page: {per_page}, page: {page}, pages: {pages}, operations: {[operation.to_dict() for operation in operations]}, operator: {current_user}")
    return jsonify({
        'operations': [operation.to_dict() for operation in operations],
        'total': operations_total,
        'per_page': per_page,
        'page': page,
        'pages': pages,
    }), 200

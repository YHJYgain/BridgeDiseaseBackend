from flask import request, current_app, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.constants import UserRole
from app.decorators import login_required
from app.models import Operation, User, db
from app.routes import operation_routes
from app.utils import adjust_page_if_needed, get_pagination_params


@operation_routes.route('/detail/<int:operation_id>', methods=['GET'])
@jwt_required()
@login_required
def detail(operation_id):
    # 获取当前用户身份（使用 access token）
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)

    # 获取指定操作日志
    operation = Operation.query.get(operation_id)

    # 校验字段
    validation_checks = [
        (not operation, f"【获取操作 ID={operation_id} 详情失败】该操作不存在", 404),
        (operation and operation.owner_id != current_user_id and current_user.role != UserRole.ADMIN
         and current_user.role != UserRole.DEVELOPER,
         f"【获取操作 ID={operation_id} 详情失败】您非管理员/开发人员，权限不足", 403),
    ]
    for condition, message, code in validation_checks:
        if condition:
            current_app.logger.warning(message + f', operator: {current_user}')
            return jsonify({'failure_message': message}), code

    return jsonify({
        'operation': operation.to_dict(),
    }), 200


@operation_routes.route('/delete/<int:operation_id>', methods=['DELETE'])
@jwt_required()
@login_required
def delete_operation(operation_id):
    # 获取当前用户身份（使用 access token）
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)

    # 获取指定操作
    deleted_operation = Operation.query.get(operation_id)

    # 校验字段
    validation_checks = [
        (current_user.role != UserRole.ADMIN and current_user.role != UserRole.DEVELOPER,
         f"【删除操作 ID={operation_id} 日志失败】您非管理员/开发人员，权限不足", 403),
        (not deleted_operation, f"【删除操作 ID={operation_id} 日志失败】该操作不存在", 404),
    ]
    for condition, message, code in validation_checks:
        if condition:
            current_app.logger.warning(message + f', operator: {current_user}')
            return jsonify({'failure_message': message}), code

    # 删除操作日志
    db.session.delete(deleted_operation)
    db.session.commit()

    current_app.logger.info(
        f"【删除操作 ID={operation_id} 日志成功】deleted_operation: {deleted_operation}, operator: {current_user}")
    return jsonify({
        'deleted_operation': deleted_operation.to_dict()
    }), 200


@operation_routes.route('/clear', methods=['DELETE'])
@jwt_required()
@login_required
def clear():
    # 获取当前用户身份（使用 access token）
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)

    # 校验用户权限
    if current_user.role != UserRole.ADMIN and current_user.role != UserRole.DEVELOPER:
        message = f"【清空操作日志失败】您非管理员/开发人员，权限不足"
        current_app.logger.warning(message + f', operator: {current_user}')
        return jsonify({'failure_message': message}), 403

    # 清空所有操作日志
    Operation.query.delete()
    db.session.commit()

    current_app.logger.info(f"【清空操作日志成功】operator: {current_user}")
    return jsonify({
        'operator': current_user.to_dict(),
    }), 200


@operation_routes.route('/operations/all', methods=['GET'])
@jwt_required()
@login_required
def all_operations():
    # 获取分页参数（从请求中获取，默认为第 1 页，每页 5 条记录）
    default_page = request.args.get('page', 1, type=int)
    default_per_page = request.args.get('per_page', 5, type=int)
    page, per_page = get_pagination_params(default_page, default_per_page)

    # 获取当前用户身份（使用 access token）
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)

    # 校验字段
    validation_checks = [
        (current_user.role != UserRole.ADMIN and current_user.role != UserRole.DEVELOPER,
         f"【获取所有操作失败】您非管理员/开发人员，权限不足", 403),
    ]
    for condition, message, code in validation_checks:
        if condition:
            current_app.logger.warning(message + f', operator: {current_user}')
            return jsonify({'failure_message': message}), code

    # 获取所有操作
    query = (
        Operation.query
        .join(User, Operation.owner_id == User.user_id)
        .add_columns(User.username.label('operator_username'))
    )
    page, operations_total, pages = adjust_page_if_needed(query, page, per_page)
    paginated = query.paginate(page=page, per_page=per_page, error_out=False)
    operations = []
    for operation, operator_username in paginated.items:
        op = operation.to_dict()
        op.update({'operator_username': operator_username})
        operations.append(op)

    current_app.logger.info(
        f"【获取所有操作成功】total: {operations_total}, per_page: {per_page}, page: {page}, pages: {pages}, operations: {operations}, operator: {current_user}")
    return jsonify({
        'operations': operations,
        'total': operations_total,
        'per_page': per_page,
        'page': page,
        'pages': pages,
    }), 200

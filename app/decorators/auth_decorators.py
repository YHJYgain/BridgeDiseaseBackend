from functools import wraps

from flask import jsonify, current_app
from flask_jwt_extended import get_jwt_identity

from app.models import User


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        if not current_user:
            failure_message = f"【登录用户验证失败】尚未登录或服务器数据异常（用户 ID: {current_user_id} 不存在）"
            current_app.logger.error(failure_message)
            return jsonify({'error': failure_message}), 404
        return f(*args, **kwargs)

    return decorated_function

import traceback

from flask import jsonify, current_app, request
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.exceptions import HTTPException


def register_error_handlers(app):
    @app.errorhandler(Exception)
    def handle_error(error):
        # 获取详细的堆栈追踪信息
        stack_trace = traceback.format_exc()

        # 获取请求的相关信息
        request_method = request.method
        request_url = request.url
        request_data = request.get_data(as_text=True)

        # 记录日志，帮助排查问题
        current_app.logger.error(f"Error: {str(error)}\nStack Trace: {stack_trace}\n"
                                 f"Request Method: {request_method}\n"
                                 f"Request URL: {request_url}\n"
                                 f"Request Data: {request_data}")

        # 如果是数据库相关的错误
        if isinstance(error, SQLAlchemyError):
            return jsonify({"error": "Database operation failed"}), 500
        # 如果是 HTTP 异常（如 404, 405 等）
        elif isinstance(error, HTTPException):
            return jsonify({"error": error.description}), error.code
        # 其他标准异常（例如 ValueError, KeyError 等）
        elif isinstance(error, ValueError):
            return jsonify({"error": "Invalid value provided"}), 400
        elif isinstance(error, KeyError):
            return jsonify({"error": "Missing key in the request"}), 400
        # 捕获所有其他错误
        return jsonify({"error": "An unexpected error occurred"}), 500

import os

from flask import abort, send_from_directory, current_app, jsonify

from app.routes import file_routes

STATIC_FOLDER = os.path.join(os.getcwd(), 'app', 'static')


@file_routes.route('/static/<path:filepath>')
def serve_static(filepath):
    """
    自定义路由处理 static 路径下的所有静态文件请求（绕过 Flask 默认 static 机制）
    """

    # 安全性检查
    if '..' in filepath or filepath.startswith('/'):
        abort(400)

    abs_path = os.path.join(STATIC_FOLDER, filepath)
    if not os.path.isfile(abs_path):
        abort(404)

    current_app.logger.info(f'Serving static file: {abs_path}')
    return send_from_directory(STATIC_FOLDER, filepath)


@file_routes.route('/static')
def static():
    """
    静态文件路由
    """
    current_app.logger.info(f'Serving static file')
    return jsonify({
        'operation': 'Serving static file',
    }), 201

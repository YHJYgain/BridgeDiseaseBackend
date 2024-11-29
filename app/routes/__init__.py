from flask import Blueprint

# 创建蓝图
user_routes = Blueprint('user', __name__, url_prefix='/user')


def register_routes(app):
    """
    注册所有蓝图到 Flask 应用中。
    :param app: Flask 应用实例
    :type app: Flask
    :return: None
    """
    # 注册蓝图
    app.register_blueprint(user_routes)


from .user import *

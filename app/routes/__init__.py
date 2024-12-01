from flask import Blueprint

# 创建蓝图
user_routes = Blueprint('user', __name__, url_prefix='/user')
model_routes = Blueprint('model', __name__, url_prefix='/model')
media_routes = Blueprint('media', __name__, url_prefix='/media')


def register_routes(app):
    """
    将所有的蓝图注册到 Flask 应用中。

    该函数用于将定义的蓝图（例如 user_routes）与 Flask 应用绑定，
    使得在应用中能够通过指定的 URL 前缀访问相关视图函数。

    :param app: Flask 应用实例
    :type app: Flask
    :return: None
    """
    # 注册蓝图
    app.register_blueprint(user_routes)
    app.register_blueprint(model_routes)
    app.register_blueprint(media_routes)


from .user import *

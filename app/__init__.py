import os
from datetime import datetime
from logging.config import dictConfig

from flask import Flask

from .config import Config
from .errors import *
from .models import init_db
from .routes import register_routes
from .utils import init_jwt


def create_app():
    """
    创建和配置 Flask 应用实例。

    :return: 配置好的 Flask 应用实例
    :rtype: Flask
    """
    app = Flask(__name__, instance_relative_config=True)

    # 配置日志记录
    configure_logging()

    # 加载配置
    app.config.from_object(Config)
    app.logger.info(f'初始化服务配置：{dict(app.config)}')

    # 初始化 JWT
    init_jwt(app)

    # 初始化数据库
    init_db(app)

    # 注册蓝图
    register_routes(app)

    # 注册全局错误处理器
    register_error_handlers(app)

    return app


def configure_logging():
    """
    配置日志记录。

    创建一个名为 'logs' 的文件夹（如果不存在），并配置日志记录的格式和处理器。
    日志记录将保存到 'logs' 文件夹中一个以时间戳命名的文件中，以确保每次运行时都有一个新的日志文件。

    日志记录器包括：
    - `StreamHandler` 用于输出到控制台（WSGI 错误流）
    - `FileHandler` 用于将日志写入文件

    :return: None
    """
    log_folder = 'logs'
    if not os.path.exists(log_folder):
        os.makedirs(log_folder)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_filename = os.path.join(log_folder, f'app_{timestamp}.log')

    dictConfig({
        'version': 1,
        'formatters': {
            'default': {
                'format': '[%(asctime)s] %(levelname)s at %(filename)s:%(lineno)d: %(message)s',
                'datefmt': '%Y-%m-%d %H:%M:%S'
            }
        },
        'handlers': {
            'wsgi': {
                'class': 'logging.StreamHandler',
                'stream': 'ext://flask.logging.wsgi_errors_stream',
                'formatter': 'default'
            },
            'file': {
                'class': 'logging.FileHandler',
                'filename': log_filename,
                'formatter': 'default',
                'encoding': 'utf-8',
                'level': 'DEBUG'
            }
        },
        'root': {
            'level': 'DEBUG',
            'handlers': ['wsgi', 'file']
        }
    })

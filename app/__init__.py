from dotenv import load_dotenv
import os
from datetime import datetime
from logging.config import dictConfig
from flask import Flask
from instance.config import Config
from .models import db
from .routes import auth

# 加载环境变量
load_dotenv()


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
                'format': '[%(asctime)s] %(levelname)s in %(module)s at %(filename)s:%(lineno)d: %(message)s',
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


def register_blueprints(app):
    """
    注册所有蓝图到 Flask 应用中。

    目前注册了 `auth` 蓝图。如果有其他蓝图需要注册，可以在此函数中添加相应的代码。

    :param app: Flask 应用实例
    :type app: Flask
    :return: None
    """
    app.register_blueprint(auth)


def create_app():
    """
    创建和配置 Flask 应用实例。

    - 配置日志记录
    - 从配置对象加载应用配置
    - 注册蓝图
    - 初始化数据库

    :return: 配置好的 Flask 应用实例
    :rtype: Flask
    """
    app = Flask(__name__, instance_relative_config=True)
    # 配置日志记录
    configure_logging()
    # 加载配置
    app.config.from_object(Config)
    # 注册蓝图
    register_blueprints(app)
    app.logger.info(f'初始化服务配置：{dict(app.config)}')

    # 初始化 MySQL 数据库
    db.init_app(app)
    app.logger.info('初始化 MySQL 数据库。')

    app.logger.info('桥梁病害系统后端服务开始运行。')

    return app

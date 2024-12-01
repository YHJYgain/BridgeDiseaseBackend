from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def init_db(app):
    """
    初始化数据库并将其绑定到 Flask 应用。

    该函数会在 Flask 应用初始化时调用，负责设置数据库连接，并根据
    定义的模型创建相应的数据库表。

    :param app: Flask 应用实例
    """
    db.init_app(app)
    with app.app_context():
        db.create_all()  # 创建数据库表

    app.logger.info('初始化数据库。')

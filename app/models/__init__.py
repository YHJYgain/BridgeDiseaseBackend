from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def init_db(app):
    """
    用于在应用初始化时绑定数据库
    """
    db.init_app(app)
    with app.app_context():
        db.create_all()  # 创建数据库表

    app.logger.info('初始化数据库。')

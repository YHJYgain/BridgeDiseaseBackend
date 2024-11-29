class Config:
    # Flask 密钥，用于签名 cookies 和其他需要加密的操作
    SECRET_KEY = 'WZY'

    # SQLAlchemy 数据库 URI
    SQLALCHEMY_DATABASE_URI = 'mysql://root:YHJYgain9420.@localhost/bridge_disease'

    # 禁用 SQLAlchemy 的修改追踪
    SQLALCHEMY_TRACK_MODIFICATIONS = False

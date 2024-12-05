import os


class Config:
    SECRET_KEY = 'WZY'  # Flask 密钥，用于签名 cookies 和其他需要加密的操作
    SQLALCHEMY_DATABASE_URI = 'mysql://root:YHJYgain9420.@localhost/bridge_disease'  # SQLAlchemy 数据库 URI
    SQLALCHEMY_TRACK_MODIFICATIONS = False  # 禁用 SQLAlchemy 的修改追踪
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
    AVATAR_FOLDER = os.path.join(os.getcwd(), 'app', 'static', 'avatars')  # 头像存储的文件夹路径
    MAX_AVATAR_SIZE = 5 * 1024 * 1024  # 最大头像文件大小：5MB

import os
from datetime import timedelta


class Config:
    SECRET_KEY = 'WZY'  # Flask 密钥，用于签名 cookies 和其他需要加密的操作
    SQLALCHEMY_DATABASE_URI = 'mysql://root:YHJYgain9420.@localhost/bridge_disease'  # SQLAlchemy 数据库 URI
    SQLALCHEMY_TRACK_MODIFICATIONS = False  # 禁用 SQLAlchemy 的修改追踪
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'mp4', 'avi', 'mov'}  # 允许上传的文件扩展名
    AVATARS_FOLDER = os.path.join(os.getcwd(), 'app', 'static', 'avatars')  # 头像存储的文件夹路径
    MEDIAS_FOLDER = os.path.join(os.getcwd(), 'app', 'static', 'medias')  # 媒体存储的文件夹路径
    MAX_AVATAR_SIZE = 5 * 1024 * 1024  # 最大头像文件大小：5MB
    JWT_SECRET_KEY = 'WZY'  # 为 JWT 设置一个密钥
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)  # access token 过期时间
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)  # refresh token 过期时间

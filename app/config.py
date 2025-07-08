import os
from datetime import timedelta


class Config:
    SECRET_KEY = 'WZY'  # Flask 密钥，用于签名 cookies 和其他需要加密的操作
    SQLALCHEMY_DATABASE_URI = 'mysql://username:password@localhost/bridge_disease'  # SQLAlchemy 数据库 URI
    SQLALCHEMY_TRACK_MODIFICATIONS = False  # 禁用 SQLAlchemy 的修改追踪
    ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg'}  # 允许上传的图片文件扩展名
    ALLOWED_VIDEO_EXTENSIONS = {'mp4'}  # 允许上传的视频文件扩展名
    ALLOWED_MODEL_EXTENSIONS = {'pt'}  # 允许上传的模型文件扩展名
    AVATARS_FOLDER = os.path.join(os.getcwd(), 'app', 'static', 'avatars')  # 头像存储的文件夹路径
    MODELS_FOLDER = os.path.join(os.getcwd(), 'app', 'static', 'models')  # 模型存储的文件夹路径
    MEDIAS_FOLDER = os.path.join(os.getcwd(), 'app', 'static', 'medias')  # 媒体存储的文件夹路径
    RESULTS_FOLDER = os.path.join(os.getcwd(), 'app', 'static', 'results')  # 结果存储的文件夹路径
    MAX_AVATAR_SIZE = 5 * 1024 * 1024  # 最大头像文件大小：5MB
    JWT_SECRET_KEY = 'WZY'  # 为 JWT 设置一个密钥
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)  # access token 过期时间
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)  # refresh token 过期时间
    CRACK_SCALA_FACTOR = 0.1  # 裂缝缩放因子
    
    # 病害指标权重配置
    DISEASE_INDEX_WEIGHTS = {
        'disease_count': 0.15,
        'disease_perimeter': 0.15,
        'disease_area': 0.2,
        'shape_complexity': 0.15,
        'texture_roughness': 0.15,
        'crack_width': 0.1,
        'avg_hue': 0.1,
    }

    # API 限流配置
    RATE_LIMIT_DEFAULT_LIMIT = 60  # 默认每分钟允许的请求次数
    RATE_LIMIT_DEFAULT_PERIOD = 60  # 默认限流时间窗口（s）
